"""
Command line runner for the applied music recommender system.

This CLI now shows:
- retrieval-backed explanations
- specialized explanation styles
- a workflow trace for the multi-step recommendation chain
- confidence estimates and self-critique notes
- guardrail warnings for risky inputs
"""

import logging
from pathlib import Path

from .recommender import load_songs, recommend_with_report


def configure_logging() -> None:
    """Log recommendation runs to a local file."""

    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
        handlers=[
            logging.FileHandler(log_dir / "recommender.log", encoding="utf-8"),
        ],
    )


def print_profile_recommendations(
    profile_name: str,
    user_prefs: dict,
    songs: list[dict],
    explanation_style: str,
) -> None:
    """Print a formatted recommendation block for one user profile."""

    report = recommend_with_report(user_prefs, songs, k=5, explanation_style=explanation_style)

    print(f"\n=== {profile_name} ===")
    print(f"User preferences: {user_prefs}")
    print(f"Explanation style: {report.explanation_style}")
    print(
        "System metrics: "
        f"avg confidence={report.metrics['average_confidence']:.2f}, "
        f"genre diversity={report.metrics['genre_diversity_ratio']:.2f}, "
        f"artist diversity={report.metrics['artist_diversity_ratio']:.2f}, "
        f"retrieval coverage={report.metrics['retrieval_coverage_ratio']:.2f}\n"
    )

    print("Workflow trace:")
    for step in report.workflow_trace:
        print(f"- {step}")
    print()

    if report.retrieved_sections:
        print("Retrieved knowledge sections:")
        for label in report.retrieved_sections:
            print(f"- {label}")
        print()

    if report.warnings:
        print("Guardrails and warnings:")
        for warning in report.warnings:
            print(f"- {warning}")
        print()

    for result in report.recommendations:
        song = result.song
        print(
            f"{song['title']} by {song['artist']} - "
            f"Base Score: {result.base_score:.2f} | "
            f"Adjusted Score: {result.adjusted_score:.2f} | "
            f"Confidence: {result.confidence:.2f}"
        )
        print(f"Reasons: {', '.join(result.reasons[:3])}")
        if result.retrieved_context:
            print("Retrieved context:")
            for item in result.retrieved_context:
                print(f"  - {item}")
        print(f"Because: {result.explanation}")
        print(result.critique)
        print()


def main() -> None:
    configure_logging()

    songs = load_songs(str(Path(__file__).resolve().parent.parent / "data" / "songs.csv"))
    print(f"Loaded songs: {len(songs)}")

    profiles = [
        (
            "High-Energy Pop",
            {"genre": "pop", "mood": "happy", "energy": 0.8},
            "curator",
        ),
        (
            "Chill Lofi",
            {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True},
            "curator",
        ),
        (
            "Deep Intense Rock",
            {"genre": "rock", "mood": "intense", "energy": 0.9},
            "studio",
        ),
    ]

    for profile_name, user_prefs, explanation_style in profiles:
        print_profile_recommendations(profile_name, user_prefs, songs, explanation_style)


if __name__ == "__main__":
    main()
