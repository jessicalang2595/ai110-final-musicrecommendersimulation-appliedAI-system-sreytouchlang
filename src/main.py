"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from pathlib import Path

from .recommender import load_songs, recommend_songs, score_song


def print_profile_recommendations(profile_name: str, user_prefs: dict, songs: list[dict]) -> None:
    """Print a formatted recommendation block for one user profile."""
    recommendations = recommend_songs(user_prefs, songs, k=5)

    print(f"\n=== {profile_name} ===")
    print(f"User preferences: {user_prefs}\n")
    for song, score, explanation in recommendations:
        _, reasons = score_song(user_prefs, song)
        print(f"{song['title']} by {song['artist']} - Score: {score:.2f}")
        print(f"Reasons: {', '.join(reasons[:3])}")
        print(f"Because: {explanation}")
        print()


def main() -> None:
    songs = load_songs(str(Path(__file__).resolve().parent.parent / "data" / "songs.csv"))
    print(f"Loaded songs: {len(songs)}")

    profiles = [
        ("High-Energy Pop", {"genre": "pop", "mood": "happy", "energy": 0.8}),
        ("Chill Lofi", {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True}),
        ("Deep Intense Rock", {"genre": "rock", "mood": "intense", "energy": 0.9}),
    ]

    for profile_name, user_prefs in profiles:
        print_profile_recommendations(profile_name, user_prefs, songs)


if __name__ == "__main__":
    main()
