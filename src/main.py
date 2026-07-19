"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

The recommendation logic itself lives in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

import textwrap
from typing import Dict, List, Tuple

from src.recommender import load_songs, max_score, recommend_songs

try:
    from tabulate import tabulate
except ImportError:  # tabulate is optional - the table still prints without it
    tabulate = None

WIDTH = 68
REASON_WIDTH = 46


def print_profile(user_prefs: Dict) -> None:
    """Shows what the recommender was asked for, so the results can be judged."""
    print("Your taste profile:")
    for key, value in user_prefs.items():
        if isinstance(value, float):
            shown = f"{value:.2f}"
        elif isinstance(value, list):
            shown = ", ".join(value)
        else:
            shown = value
        print(f"    {key:<18} {shown}")


def score_bar(score: float, ceiling: float, width: int = 20) -> str:
    """A quick visual for how strong a match is, relative to a perfect score."""
    filled = round((score / ceiling) * width) if ceiling else 0
    return "#" * filled + "." * (width - filled)


def print_recommendations(
    recommendations: List[Tuple[Dict, float, str]], ceiling: float
) -> None:
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   score {score:.2f} / {ceiling:.2f}  [{score_bar(score, ceiling)}]")
        # recommend_songs joins the reasons with "; " - split them back out so
        # each one gets its own line.
        for reason in explanation.split("; "):
            print(f"     - {reason}")
        print()


# Three listeners who want clearly different things. If the recommender works,
# these should produce three clearly different lists.
PROFILES = {
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.75,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "chill",
        "target_energy": 0.35,
        "target_valence": 0.58,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "target_energy": 0.92,
        "target_valence": 0.40,
    },
}

# Profiles built to break the scoring rather than to be served well. Each one
# targets a specific weakness - see the README for what each is probing.
EDGE_CASE_PROFILES = {
    "Contradictory (quiet genre, loud target)": {
        "genre": "classical",
        "mood": "angry",
        "target_energy": 0.95,
        "target_valence": 0.20,
    },
    "Indecisive (no genre or mood, mid-range numbers)": {
        "target_energy": 0.65,
        "target_valence": 0.50,
    },
    "Unknown genre (nothing in the catalog matches)": {
        "genre": "k-pop",
        "mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.80,
    },
}


# Profiles that use the extended attributes. The first pair is the same
# listener described two ways, to show what mood tags fix.
EXTENDED_PROFILES = {
    "Dark and heavy, asked for by MOOD WORD (the old way)": {
        "mood": "intense",
        "target_energy": 0.92,
    },
    "Dark and heavy, asked for by MOOD TAGS (the new way)": {
        "mood_tags": ["intense", "aggressive"],
        "target_energy": 0.92,
    },
    "Obscure 90s instrumental for deep focus": {
        "target_popularity": 30,
        "favorite_decade": 1990,
        "target_vocal": 0.05,
        "language": "instrumental",
    },
}


def print_table(recommendations: List[Tuple[Dict, float, str]], ceiling: float) -> None:
    """
    Prints the recommendations as one compact table, reasons included.

    Uses tabulate when it is installed and falls back to plain formatting when
    it is not, so the program never depends on the extra package being there.
    """
    headers = ["#", "Song", "Artist", "Score", "Why it was picked"]
    rows = []
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        rows.append(
            [
                rank,
                song["title"],
                song["artist"],
                f"{score:.2f}/{ceiling:.2f}",
                explanation,
            ]
        )

    if tabulate is not None:
        print(
            tabulate(
                rows,
                headers=headers,
                tablefmt="simple_grid",
                maxcolwidths=[None, 20, 16, None, REASON_WIDTH],
            )
        )
        return

    # Fallback: same information, wrapped by hand.
    widths = [3, 20, 16, 11, REASON_WIDTH]
    line = "-+-".join("-" * w for w in widths)
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print(line)
    for row in rows:
        wrapped = textwrap.wrap(row[4], REASON_WIDTH) or [""]
        for i, chunk in enumerate(wrapped):
            cells = [str(row[j]) if i == 0 else "" for j in range(4)] + [chunk]
            print(" | ".join(c.ljust(w) for c, w in zip(cells, widths)))
        print(line)


def run_profile(name: str, user_prefs: dict, songs: List[Dict], k: int = 5) -> None:
    """Scores the catalog for one profile and prints its top k."""
    print("-" * WIDTH)
    print(f"  PROFILE: {name}")
    print("-" * WIDTH)
    print_profile(user_prefs)
    print(f"\n  Top {k}:\n")
    print_recommendations(recommend_songs(user_prefs, songs, k=k), max_score(user_prefs))


def main() -> None:
    songs = load_songs("data/songs.csv")

    print("=" * WIDTH)
    print("  MUSIC RECOMMENDER SIMULATION")
    print("=" * WIDTH)
    print(f"Loaded songs: {len(songs)}\n")

    for name, prefs in PROFILES.items():
        run_profile(name, prefs, songs, k=5)

    print("=" * WIDTH)
    print("  EDGE CASES - trying to break the scoring")
    print("=" * WIDTH + "\n")

    for name, prefs in EDGE_CASE_PROFILES.items():
        run_profile(name, prefs, songs, k=3)

    print("=" * WIDTH)
    print("  EXTENDED ATTRIBUTES - the same request, told two ways")
    print("=" * WIDTH + "\n")

    for name, prefs in EXTENDED_PROFILES.items():
        run_profile(name, prefs, songs, k=3)

    print("=" * WIDTH)
    print("  DIVERSITY PENALTY - same listener, three settings")
    print("=" * WIDTH + "\n")

    print("=" * WIDTH)
    print("  SUMMARY TABLES")
    print("=" * WIDTH + "\n")

    for name, prefs in PROFILES.items():
        print(f"{name}\n")
        print_table(recommend_songs(prefs, songs, k=5), max_score(prefs))
        print()

    lofi = PROFILES["Chill Lofi"]
    for label, artist_pen, genre_pen in (
        ("Off (default) - ranked purely by score", 0.0, 0.0),
        ("Artist penalty 1.0", 1.0, 0.0),
        ("Artist penalty 1.0 + genre penalty 0.8", 1.0, 0.8),
    ):
        print("-" * WIDTH)
        print(f"  {label}")
        print("-" * WIDTH)
        for song, score, _ in recommend_songs(
            lofi, songs, k=5, artist_penalty=artist_pen, genre_penalty=genre_pen
        ):
            print(
                f"   {score:5.2f}  {song['title']:<22}"
                f"{song['artist']:<16}{song['genre']}"
            )
        print()


if __name__ == "__main__":
    main()
