"""Evaluation harness for the applied music recommender."""

from pathlib import Path

from .recommender import load_songs, recommend_with_report

EVALUATION_PROFILES = [
    ("Balanced Pop", {"genre": "pop", "mood": "happy", "energy": 0.8}, "plain"),
    ("Acoustic Study", {"genre": "lofi", "mood": "chill", "energy": 0.4, "likes_acoustic": True}, "curator"),
    ("High-Intensity Rock", {"genre": "rock", "mood": "intense", "energy": 0.9}, "studio"),
    ("Guardrail Stress Test", {"mood": "happy", "energy": 1.3, "likes_acoustic": False}, "curator"),
]


def main() -> None:
    songs = load_songs(str(Path(__file__).resolve().parent.parent / "data" / "songs.csv"))
    reports = []

    print(f"Running evaluation on {len(EVALUATION_PROFILES)} profiles and {len(songs)} songs.\n")

    for profile_name, user_prefs, explanation_style in EVALUATION_PROFILES:
        report = recommend_with_report(
            user_prefs,
            songs,
            k=5,
            explanation_style=explanation_style,
        )
        reports.append((profile_name, report))

        top_pick = report.recommendations[0].song["title"]
        print(
            f"{profile_name}: top pick={top_pick} | "
            f"style={report.explanation_style} | "
            f"avg confidence={report.metrics['average_confidence']:.2f} | "
            f"genre diversity={report.metrics['genre_diversity_ratio']:.2f} | "
            f"retrieval coverage={report.metrics['retrieval_coverage_ratio']:.2f} | "
            f"warnings={len(report.warnings)}"
        )
        for warning in report.warnings:
            print(f"  - {warning}")
        print()

    avg_confidence = sum(report.metrics["average_confidence"] for _, report in reports) / len(reports)
    diversity_warning_count = sum(
        1
        for _, report in reports
        if any("Diversity warning" in warning for warning in report.warnings)
    )
    self_critique_count = sum(
        1
        for _, report in reports
        if any("Self-critique loop" in warning for warning in report.warnings)
    )
    guardrail_warning_count = sum(
        1
        for _, report in reports
        if any("Input guardrail" in warning for warning in report.warnings)
    )
    retrieval_profile_count = sum(
        1
        for _, report in reports
        if report.metrics["retrieval_coverage_ratio"] > 0.0
    )

    sample_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}
    plain_report = recommend_with_report(sample_prefs, songs, k=1, explanation_style="plain")
    curator_report = recommend_with_report(sample_prefs, songs, k=1, explanation_style="curator")
    style_outputs_differ = (
        plain_report.recommendations[0].explanation
        != curator_report.recommendations[0].explanation
    )

    print("Summary")
    print(f"- Average confidence across profiles: {avg_confidence:.2f}")
    print(f"- Profiles with self-critique penalties: {self_critique_count}/{len(reports)}")
    print(f"- Profiles with diversity warnings: {diversity_warning_count}/{len(reports)}")
    print(f"- Profiles with input guardrail warnings: {guardrail_warning_count}/{len(reports)}")
    print(f"- Profiles with retrieval-backed explanations: {retrieval_profile_count}/{len(reports)}")
    print(f"- Specialized style differs from baseline: {style_outputs_differ}")
    print(f"- Baseline explanation sample: {plain_report.recommendations[0].explanation}")
    print(f"- Curator explanation sample: {curator_report.recommendations[0].explanation}")


if __name__ == "__main__":
    main()
