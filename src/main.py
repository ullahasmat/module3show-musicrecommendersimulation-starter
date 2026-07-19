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


def main() -> None:
    songs = load_songs("data/songs.csv")

    user_prefs = {
        "genre": "pop",
        "mood": "happy",
        "target_energy": 0.80,
        "target_valence": 0.75,
    }

    print("=" * WIDTH)
    print("  MUSIC RECOMMENDER SIMULATION")
    print("=" * WIDTH)
    print(f"Loaded songs: {len(songs)}\n")
    print_profile(user_prefs)

    k = 5
    recommendations = recommend_songs(user_prefs, songs, k=k)

    print("\n" + "-" * WIDTH)
    print(f"  Top {k} recommendations")
    print("-" * WIDTH + "\n")
    print_recommendations(recommendations)


if __name__ == "__main__":
    main()
