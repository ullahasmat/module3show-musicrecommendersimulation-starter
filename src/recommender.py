import csv
import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

# Columns that must be converted from CSV text into numbers so we can do math
# with them later. Everything else (title, artist, genre, mood) stays a string.
INT_FIELDS = ("id",)
FLOAT_FIELDS = ("energy", "tempo_bpm", "valence", "danceability", "acousticness")

# --- Algorithm Recipe (see README) -----------------------------------------
# Weights live here so experiments only ever change one place.
W_GENRE = 2.0
W_MOOD = 1.5
W_ENERGY = 1.0
W_VALENCE = 1.0

# Width of the Gaussian used for numeric closeness. Smaller = pickier about
# hitting the target exactly.
SIGMA = 0.25

MAX_SCORE = W_GENRE + W_MOOD + W_ENERGY + W_VALENCE  # 5.5

# How a reason that earned no points ends. Used to filter those out when
# summarising a recommendation.
ZERO_POINTS = "(+0.00)"


def closeness(a: float, b: float, sigma: float = SIGMA) -> float:
    """
    Scores how CLOSE two values are, on a 0.0 - 1.0 scale. 1.0 means identical.

    This is what makes "target_energy" mean "aim for this" rather than
    "higher is better" - a song scores best when it sits near the target and
    falls off in both directions.

    The falloff is Gaussian rather than linear on purpose. With a linear
    1 - abs(a - b), the worst possible match in the catalog still earns about
    half credit, and enough near-misses stacked together can outrank a real
    match. The curve below is forgiving of small misses and harsh on large ones.
    """
    return math.exp(-((a - b) ** 2) / (2 * sigma ** 2))


def genre_match(user_genre: str, song_genre: str) -> float:
    """
    Returns 1.0 for an exact genre match, 0.5 when the two genres share a word,
    and 0.0 otherwise.

    The partial credit exists because exact string matching scores "pop" against
    "indie pop" as a total stranger, which is obviously wrong. Moods deliberately
    do NOT get this treatment - see the bias notes in the README.
    """
    user_genre, song_genre = user_genre.lower(), song_genre.lower()
    if user_genre == song_genre:
        return 1.0
    if set(user_genre.split()) & set(song_genre.split()):
        return 0.5
    return 0.0

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        """Holds the catalog this recommender will rank."""
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        """NOT YET IMPLEMENTED - returns the first k songs unranked."""
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        """NOT YET IMPLEMENTED - returns placeholder text, not a real explanation."""
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file into a list of dictionaries.

    csv.DictReader hands back every value as a string, so "0.82" would break
    any arithmetic later on. This converts the numeric columns to int/float
    and leaves the text columns alone.
    Required by src/main.py
    """
    songs: List[Dict] = []

    try:
        # utf-8-sig strips the byte-order mark that Excel adds when it saves a
        # CSV, which would otherwise turn the first header into "﻿id".
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            for line_no, row in enumerate(csv.DictReader(f), start=2):
                song = dict(row)
                for field in INT_FIELDS:
                    song[field] = int(song[field])
                for field in FLOAT_FIELDS:
                    song[field] = float(song[field])
                songs.append(song)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find {csv_path}. Run this from the project root, "
            f"e.g. python -m src.main"
        ) from None
    except (KeyError, TypeError) as e:
        raise ValueError(f"{csv_path} line {line_no}: missing column {e}") from None
    except ValueError as e:
        raise ValueError(f"{csv_path} line {line_no}: bad number ({e})") from None

    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against one user's preferences.

    Returns (score, reasons) where reasons explains where every point came
    from. The reasons are built here, as each term is calculated, rather than
    written separately afterwards - that way an explanation can never drift
    away from the arithmetic that actually produced the ranking.

    Any preference the user leaves out is simply skipped, so a partial profile
    still scores. Every song in a run is judged on the same terms, so leaving
    one out never favours a particular song.

        2.0 x genre    (1.0 exact | 0.5 shared word | 0.0 none)
      + 1.5 x mood     (1.0 if equal | 0.0 otherwise)
      + 1.0 x closeness(energy,  target_energy)
      + 1.0 x closeness(valence, target_valence)
                                                       max = 5.5
    """
    score = 0.0
    reasons: List[str] = []

    if "genre" in user_prefs:
        match = genre_match(user_prefs["genre"], song["genre"])
        points = W_GENRE * match
        score += points
        if match == 1.0:
            reasons.append(f"genre match: {song['genre']} (+{points:.2f})")
        elif match == 0.5:
            reasons.append(
                f"related genre: {song['genre']} ~ {user_prefs['genre']} (+{points:.2f})"
            )
        else:
            reasons.append(f"different genre: {song['genre']} (+0.00)")

    if "mood" in user_prefs:
        match = 1.0 if user_prefs["mood"].lower() == song["mood"].lower() else 0.0
        points = W_MOOD * match
        score += points
        if match:
            reasons.append(f"mood match: {song['mood']} (+{points:.2f})")
        else:
            reasons.append(f"different mood: {song['mood']} (+0.00)")

    for field, pref_key, weight in (
        ("energy", "target_energy", W_ENERGY),
        ("valence", "target_valence", W_VALENCE),
    ):
        if pref_key not in user_prefs:
            continue
        target = user_prefs[pref_key]
        fraction = closeness(song[field], target)
        points = weight * fraction
        score += points
        # Word this from the fraction we actually scored, not from the raw
        # difference, so the sentence can never contradict the number beside it.
        if fraction >= 0.75:
            nearness = "close to"
        elif fraction >= 0.35:
            nearness = "somewhat near"
        else:
            nearness = "far from"
        reasons.append(
            f"{field} {song[field]:.2f} {nearness} your {target:.2f} (+{points:.2f})"
        )

    return score, reasons

def summarize_reasons(reasons: List[str], limit: int = 3) -> str:
    """
    Turns the full list of scoring reasons into one readable sentence.

    Terms that scored nothing are dropped - they explain why a song ranked
    LOW, which is useful when inspecting a single song but noise in a list of
    recommendations.
    """
    earned = [r for r in reasons if not r.endswith(ZERO_POINTS)]
    if not earned:
        return "nothing in this song matched your preferences"
    return "; ".join(earned[:limit])


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Ranks the whole catalog for one user and returns the best k songs.

    This is the ranking rule, and it is deliberately separate from
    score_song(). Scoring judges one song on its own merits; ranking decides
    what actually gets shown. Some of those decisions are impossible to make
    one song at a time - whether to show a second song by an artist depends on
    what is already in the list, which score_song() cannot see.

    Returns a list of (song, score, explanation) tuples, highest score first.
    Required by src/main.py
    """
    scored = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        scored.append((song, score, summarize_reasons(reasons)))

    # Sort by score descending, then break ties on purpose. Without the extra
    # keys, equal scores keep their CSV order, which means row position quietly
    # decides the ranking - a bias nobody asked for and nobody would notice.
    # Negating the score sorts it descending while the tiebreakers stay
    # ascending, which is the usual way to mix directions in one key.
    target_energy = user_prefs.get("target_energy")
    scored.sort(
        key=lambda item: (
            -item[1],
            abs(item[0]["energy"] - target_energy) if target_energy is not None else 0.0,
            item[0]["title"],
        )
    )

    return scored[:k]
