"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

The recommendation logic itself lives in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from typing import Dict, List, Tuple

from src.recommender import MAX_SCORE, load_songs, recommend_songs

WIDTH = 68


def print_profile(user_prefs: Dict) -> None:
    """Shows what the recommender was asked for, so the results can be judged."""
    print("Your taste profile:")
    for key, value in user_prefs.items():
        shown = f"{value:.2f}" if isinstance(value, float) else value
        print(f"    {key:<16} {shown}")


def score_bar(score: float, width: int = 20) -> str:
    """A quick visual for how strong a match is, relative to a perfect score."""
    filled = round((score / MAX_SCORE) * width)
    return "#" * filled + "." * (width - filled)


def print_recommendations(recommendations: List[Tuple[Dict, float, str]]) -> None:
    for rank, (song, score, explanation) in enumerate(recommendations, start=1):
        print(f"{rank}. {song['title']} - {song['artist']}")
        print(f"   score {score:.2f} / {MAX_SCORE:.2f}  [{score_bar(score)}]")
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


def run_profile(name: str, user_prefs: dict, songs: List[Dict], k: int = 5) -> None:
    """Scores the catalog for one profile and prints its top k."""
    print("-" * WIDTH)
    print(f"  PROFILE: {name}")
    print("-" * WIDTH)
    print_profile(user_prefs)
    print(f"\n  Top {k}:\n")
    print_recommendations(recommend_songs(user_prefs, songs, k=k))


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


if __name__ == "__main__":
    main()
