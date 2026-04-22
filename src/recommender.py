import csv
import logging
from dataclasses import asdict, dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

GENRE_WEIGHT = 4.0
MOOD_WEIGHT = 2.5
ENERGY_WEIGHT = 2.0
ACOUSTIC_WEIGHT = 1.5

MAX_MATCH_SCORE = GENRE_WEIGHT + MOOD_WEIGHT + ENERGY_WEIGHT + ACOUSTIC_WEIGHT
REPEAT_GENRE_PENALTY = 0.75
REPEAT_ARTIST_PENALTY = 0.50
LOW_CONFIDENCE_THRESHOLD = 0.55
LOW_DIVERSITY_THRESHOLD = 0.60
DEFAULT_EXPLANATION_STYLE = "plain"
SUPPORTED_STYLES = {"plain", "curator", "studio"}


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


@dataclass
class RecommendationResult:
    """Structured recommendation output with reliability and retrieval details."""

    song: Dict[str, Any]
    base_score: float
    adjusted_score: float
    confidence: float
    reasons: List[str]
    explanation: str
    critique: str = ""
    applied_penalties: List[str] = field(default_factory=list)
    retrieved_context: List[str] = field(default_factory=list)
    explanation_style: str = DEFAULT_EXPLANATION_STYLE


@dataclass
class RecommendationReport:
    """End-to-end recommendation report with guardrails, trace, and metrics."""

    normalized_user_prefs: Dict[str, Any]
    recommendations: List[RecommendationResult]
    warnings: List[str]
    metrics: Dict[str, float]
    workflow_trace: List[str] = field(default_factory=list)
    retrieved_sections: List[str] = field(default_factory=list)
    explanation_style: str = DEFAULT_EXPLANATION_STYLE


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """

    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        user_prefs = _user_profile_to_dict(user)
        ranked_songs = sorted(
            self.songs,
            key=lambda song: _score_song_data(user_prefs, asdict(song))[0],
            reverse=True,
        )
        return ranked_songs[:k]

    def recommend_with_report(
        self,
        user: UserProfile,
        k: int = 5,
        explanation_style: str = DEFAULT_EXPLANATION_STYLE,
    ) -> RecommendationReport:
        """Return recommendations plus reliability, retrieval, and workflow diagnostics."""

        songs = [asdict(song) for song in self.songs]
        return recommend_with_report(
            _user_profile_to_dict(user),
            songs,
            k=k,
            explanation_style=explanation_style,
        )

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        _, reasons = _score_song_data(_user_profile_to_dict(user), asdict(song))
        return _build_explanation(song.title, reasons)


def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """

    path = Path(csv_path)
    if not path.exists():
        path = Path(__file__).resolve().parent.parent / csv_path

    songs: List[Dict[str, Any]] = []
    with path.open(newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            try:
                songs.append(
                    {
                        "id": int(row["id"]),
                        "title": row["title"],
                        "artist": row["artist"],
                        "genre": row["genre"],
                        "mood": row["mood"],
                        "energy": float(row["energy"]),
                        "tempo_bpm": float(row["tempo_bpm"]),
                        "valence": float(row["valence"]),
                        "danceability": float(row["danceability"]),
                        "acousticness": float(row["acousticness"]),
                    }
                )
            except (KeyError, TypeError, ValueError) as exc:
                logger.warning("Skipping invalid song row %s: %s", row, exc)
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """

    return _score_song_data(user_prefs, song)


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Functional implementation of the recommendation logic.
    Required by src/main.py
    """

    recommendations: List[Tuple[Dict, float, str]] = []
    for song in songs:
        score, reasons = score_song(user_prefs, song)
        recommendations.append((song, score, _build_explanation(song["title"], reasons)))

    recommendations.sort(key=lambda item: item[1], reverse=True)
    return recommendations[:k]


def recommend_with_report(
    user_prefs: Dict[str, Any],
    songs: List[Dict[str, Any]],
    k: int = 5,
    explanation_style: str = DEFAULT_EXPLANATION_STYLE,
) -> RecommendationReport:
    """
    Recommend songs and attach confidence, retrieval, guardrails, and workflow diagnostics.
    """

    if k <= 0:
        raise ValueError("k must be at least 1")

    workflow_trace: List[str] = []
    normalized_prefs, input_warnings = _normalize_user_prefs_with_warnings(user_prefs)
    style = _normalize_explanation_style(explanation_style)
    workflow_trace.append(
        f"Step 1. Normalized the listener profile and selected the '{style}' explanation style."
    )

    knowledge_sources = _load_knowledge_sources()
    workflow_trace.append(
        f"Step 2. Loaded {len(knowledge_sources)} retrieval sources from the local knowledge base."
    )

    logger.info("Generating guarded recommendations for prefs=%s style=%s", normalized_prefs, style)

    candidates: List[Dict[str, Any]] = []
    retrieval_hit_count = 0
    for song in songs:
        details = _score_song_details(normalized_prefs, song)
        retrieved_context = _retrieve_context_sections(normalized_prefs, song, knowledge_sources)
        if retrieved_context:
            retrieval_hit_count += 1

        result = RecommendationResult(
            song=song,
            base_score=details["score"],
            adjusted_score=details["score"],
            confidence=0.0,
            reasons=details["reasons"],
            explanation=_build_explanation(
                song["title"],
                details["reasons"],
                retrieved_context=retrieved_context,
                explanation_style=style,
            ),
            retrieved_context=retrieved_context,
            explanation_style=style,
        )
        candidates.append({"result": result, "diagnostics": details["diagnostics"]})

    workflow_trace.append(
        f"Step 3. Scored {len(songs)} songs and retrieved supporting notes for {retrieval_hit_count} candidates."
    )

    candidates.sort(key=lambda item: item["result"].base_score, reverse=True)
    selected = _rerank_with_diversity(candidates, k=k)
    penalty_count = sum(1 for result in selected if result.applied_penalties)
    workflow_trace.append(
        f"Step 4. Applied the self-critique reranking loop and adjusted {penalty_count} top-k recommendation(s)."
    )

    metrics = _assign_confidence_and_metrics(selected, catalog_size=len(songs))
    retrieved_sections = _collect_report_context(selected)
    warnings = input_warnings + _build_report_warnings(selected, metrics)
    workflow_trace.append(
        f"Step 5. Assigned confidence scores, compiled {len(warnings)} warning(s), and prepared the final report."
    )

    logger.info(
        "Completed recommendation run: top_k=%s average_confidence=%.2f diversity=%.2f retrieval_coverage=%.2f warnings=%s",
        len(selected),
        metrics["average_confidence"],
        metrics["genre_diversity_ratio"],
        metrics["retrieval_coverage_ratio"],
        len(warnings),
    )

    return RecommendationReport(
        normalized_user_prefs=normalized_prefs,
        recommendations=selected,
        warnings=warnings,
        metrics=metrics,
        workflow_trace=workflow_trace,
        retrieved_sections=retrieved_sections,
        explanation_style=style,
    )


def _user_profile_to_dict(user: UserProfile) -> Dict[str, Any]:
    """Convert a user profile dataclass into the shared dict format."""

    return {
        "genre": user.favorite_genre,
        "mood": user.favorite_mood,
        "energy": user.target_energy,
        "likes_acoustic": user.likes_acoustic,
    }


def _normalize_user_prefs(user_prefs: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize user preferences so both APIs use the same keys and types."""

    raw_energy = user_prefs.get("energy", user_prefs.get("target_energy", 0.5))
    return {
        "genre": str(user_prefs.get("genre", user_prefs.get("favorite_genre", ""))).strip().lower(),
        "mood": str(user_prefs.get("mood", user_prefs.get("favorite_mood", ""))).strip().lower(),
        "energy": float(raw_energy),
        "likes_acoustic": bool(user_prefs.get("likes_acoustic", False)),
    }


def _normalize_user_prefs_with_warnings(user_prefs: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Normalize preferences and attach guardrail warnings for risky inputs."""

    prefs = _normalize_user_prefs(user_prefs)
    warnings: List[str] = []

    if prefs["energy"] < 0.0 or prefs["energy"] > 1.0:
        original_energy = prefs["energy"]
        prefs["energy"] = min(max(prefs["energy"], 0.0), 1.0)
        warnings.append(
            f"Input guardrail: energy {original_energy:.2f} was clamped to {prefs['energy']:.2f}."
        )

    if not prefs["genre"]:
        warnings.append("Input guardrail: no genre preference was supplied, so genre matching was disabled.")

    if not prefs["mood"]:
        warnings.append("Input guardrail: no mood preference was supplied, so mood matching was disabled.")

    return prefs, warnings


def _normalize_explanation_style(explanation_style: str) -> str:
    """Clamp explanation style to a supported constrained output mode."""

    style = str(explanation_style or DEFAULT_EXPLANATION_STYLE).strip().lower()
    if style not in SUPPORTED_STYLES:
        return DEFAULT_EXPLANATION_STYLE
    return style


def _score_song_data(user_prefs: Dict[str, Any], song: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Apply the weighted scoring recipe and return score plus reasons."""

    details = _score_song_details(user_prefs, song)
    return details["score"], details["reasons"]


def _score_song_details(user_prefs: Dict[str, Any], song: Dict[str, Any]) -> Dict[str, Any]:
    """Return score, explanation reasons, and raw match diagnostics."""

    prefs = _normalize_user_prefs(user_prefs)
    genre = str(song["genre"]).strip().lower()
    mood = str(song["mood"]).strip().lower()
    energy = float(song["energy"])
    acousticness = float(song["acousticness"])

    score = 0.0
    reason_candidates: List[Tuple[float, str]] = []
    diagnostics: Dict[str, Any] = {
        "genre_match": False,
        "mood_match": False,
        "energy_closeness": 0.0,
        "acoustic_fit": 0.0,
        "signal_count": 0,
    }

    if prefs["genre"] and genre == prefs["genre"]:
        score += GENRE_WEIGHT
        diagnostics["genre_match"] = True
        diagnostics["signal_count"] += 1
        reason_candidates.append((GENRE_WEIGHT, f"genre match (+{GENRE_WEIGHT:.1f})"))

    if prefs["mood"] and mood == prefs["mood"]:
        score += MOOD_WEIGHT
        diagnostics["mood_match"] = True
        diagnostics["signal_count"] += 1
        reason_candidates.append((MOOD_WEIGHT, f"mood match (+{MOOD_WEIGHT:.1f})"))

    energy_closeness = max(0.0, 1 - abs(energy - prefs["energy"]))
    energy_score = energy_closeness * ENERGY_WEIGHT
    diagnostics["energy_closeness"] = energy_closeness
    score += energy_score
    if energy_closeness >= 0.65:
        diagnostics["signal_count"] += 1
        if energy_closeness >= 0.85:
            reason_candidates.append((energy_score, f"energy closeness (+{energy_score:.2f})"))
        else:
            reason_candidates.append((energy_score, f"energy similarity (+{energy_score:.2f})"))

    acoustic_fit = acousticness if prefs["likes_acoustic"] else 1 - acousticness
    acoustic_score = acoustic_fit * ACOUSTIC_WEIGHT
    diagnostics["acoustic_fit"] = acoustic_fit
    score += acoustic_score
    if prefs["likes_acoustic"] and acousticness >= 0.6:
        diagnostics["signal_count"] += 1
        reason_candidates.append((acoustic_score, f"acoustic preference fit (+{acoustic_score:.2f})"))
    elif not prefs["likes_acoustic"] and acousticness <= 0.4:
        diagnostics["signal_count"] += 1
        reason_candidates.append((acoustic_score, f"low-acoustic preference fit (+{acoustic_score:.2f})"))

    reason_candidates.sort(key=lambda item: item[0], reverse=True)
    reasons = [reason for _, reason in reason_candidates]
    if not reasons:
        reasons.append("closest overall match in this small catalog")

    return {
        "score": round(score, 3),
        "reasons": reasons,
        "diagnostics": diagnostics,
    }


def _rerank_with_diversity(candidates: List[Dict[str, Any]], k: int) -> List[RecommendationResult]:
    """Greedily rerank close matches to avoid repetitive top-k results."""

    remaining = list(candidates)
    selected: List[RecommendationResult] = []

    while remaining and len(selected) < k:
        best_item = None
        best_adjusted_score = float("-inf")
        best_penalties: List[str] = []

        for candidate in remaining:
            result = candidate["result"]
            adjusted_score, penalties = _apply_diversity_penalty(result, selected)
            if adjusted_score > best_adjusted_score or (
                adjusted_score == best_adjusted_score
                and result.base_score > (best_item["result"].base_score if best_item else float("-inf"))
            ):
                best_item = candidate
                best_adjusted_score = adjusted_score
                best_penalties = penalties

        chosen = best_item["result"]
        chosen.adjusted_score = round(best_adjusted_score, 3)
        chosen.applied_penalties = best_penalties
        selected.append(chosen)
        remaining.remove(best_item)

    return selected


def _apply_diversity_penalty(
    result: RecommendationResult,
    selected: List[RecommendationResult],
) -> Tuple[float, List[str]]:
    """Penalize repeat genre or artist matches when the top list gets too narrow."""

    penalties: List[str] = []
    adjusted_score = result.base_score

    selected_genres = {item.song["genre"].strip().lower() for item in selected}
    selected_artists = {item.song["artist"].strip().lower() for item in selected}
    genre = result.song["genre"].strip().lower()
    artist = result.song["artist"].strip().lower()

    if genre in selected_genres:
        adjusted_score -= REPEAT_GENRE_PENALTY
        penalties.append(f"genre repetition penalty (-{REPEAT_GENRE_PENALTY:.2f})")

    if artist in selected_artists:
        adjusted_score -= REPEAT_ARTIST_PENALTY
        penalties.append(f"artist repetition penalty (-{REPEAT_ARTIST_PENALTY:.2f})")

    if penalties:
        logger.info(
            "Applied diversity penalty to %s: %s",
            result.song["title"],
            ", ".join(penalties),
        )

    return round(adjusted_score, 3), penalties


def _assign_confidence_and_metrics(
    recommendations: List[RecommendationResult],
    catalog_size: int,
) -> Dict[str, float]:
    """Assign song-level confidence and compute report-level metrics."""

    if not recommendations:
        return {
            "average_confidence": 0.0,
            "genre_diversity_ratio": 0.0,
            "artist_diversity_ratio": 0.0,
            "catalog_coverage_ratio": 0.0,
            "retrieval_coverage_ratio": 0.0,
        }

    for index, result in enumerate(recommendations):
        next_score = (
            recommendations[index + 1].adjusted_score
            if index + 1 < len(recommendations)
            else result.adjusted_score
        )
        margin = max(0.0, result.adjusted_score - next_score)
        score_ratio = max(0.0, min(result.adjusted_score / MAX_MATCH_SCORE, 1.0))
        reason_ratio = min(len(result.reasons), 4) / 4
        margin_ratio = min(margin / 1.5, 1.0)
        penalty_ratio = max(
            0.0,
            1 - ((result.base_score - result.adjusted_score) / (REPEAT_GENRE_PENALTY + REPEAT_ARTIST_PENALTY)),
        )
        retrieval_ratio = 1.0 if result.retrieved_context else 0.5

        confidence = round(
            min(
                0.99,
                (0.40 * score_ratio)
                + (0.18 * reason_ratio)
                + (0.17 * margin_ratio)
                + (0.10 * penalty_ratio)
                + (0.15 * retrieval_ratio),
            ),
            2,
        )
        result.confidence = confidence
        result.critique = _build_result_critique(result)

    unique_genres = len({result.song["genre"].strip().lower() for result in recommendations})
    unique_artists = len({result.song["artist"].strip().lower() for result in recommendations})
    retrieval_coverage = sum(1 for result in recommendations if result.retrieved_context) / len(recommendations)

    return {
        "average_confidence": round(sum(result.confidence for result in recommendations) / len(recommendations), 2),
        "genre_diversity_ratio": round(unique_genres / len(recommendations), 2),
        "artist_diversity_ratio": round(unique_artists / len(recommendations), 2),
        "catalog_coverage_ratio": round(len(recommendations) / catalog_size, 2) if catalog_size else 0.0,
        "retrieval_coverage_ratio": round(retrieval_coverage, 2),
    }


def _build_result_critique(result: RecommendationResult) -> str:
    """Summarize the reranking and confidence tradeoffs for one recommendation."""

    parts: List[str] = []
    if result.applied_penalties:
        parts.append("reranking adjusted this pick because " + ", ".join(result.applied_penalties))

    if result.retrieved_context:
        parts.append("retrieval grounded the explanation with matching genre and mood notes")

    if result.confidence < LOW_CONFIDENCE_THRESHOLD:
        parts.append("confidence is lower because this match is not clearly separated from nearby options")

    if not parts:
        return "Self-check: no reranking penalty was needed for this recommendation."

    return "Self-check: " + "; ".join(parts) + "."


def _build_report_warnings(
    recommendations: List[RecommendationResult],
    metrics: Dict[str, float],
) -> List[str]:
    """Turn guardrail signals into user-facing warnings."""

    warnings: List[str] = []
    repeated_genre_count = sum(
        1
        for result in recommendations
        if any("genre repetition" in penalty for penalty in result.applied_penalties)
    )
    repeated_artist_count = sum(
        1
        for result in recommendations
        if any("artist repetition" in penalty for penalty in result.applied_penalties)
    )

    if repeated_genre_count:
        warnings.append(
            f"Self-critique loop: applied genre-diversity penalties to {repeated_genre_count} recommendation(s)."
        )

    if repeated_artist_count:
        warnings.append(
            f"Self-critique loop: applied artist-diversity penalties to {repeated_artist_count} recommendation(s)."
        )

    if metrics["genre_diversity_ratio"] <= LOW_DIVERSITY_THRESHOLD:
        warnings.append("Diversity warning: the final top-k list still clusters around a narrow set of genres.")

    if metrics["average_confidence"] < LOW_CONFIDENCE_THRESHOLD:
        warnings.append("Reliability warning: the average confidence is low for this listener profile.")

    if metrics["retrieval_coverage_ratio"] == 0.0:
        warnings.append("Retrieval warning: no knowledge-base context matched this listener profile.")

    return warnings


def _build_explanation(
    title: str,
    reasons: List[str],
    retrieved_context: List[str] | None = None,
    explanation_style: str = DEFAULT_EXPLANATION_STYLE,
) -> str:
    """Turn score reasons and retrieved notes into a short recommendation sentence."""

    top_reasons = reasons[:3]
    if len(top_reasons) == 1:
        reason_text = top_reasons[0]
    elif len(top_reasons) == 2:
        reason_text = " and ".join(top_reasons)
    else:
        reason_text = ", ".join(top_reasons[:-1]) + f", and {top_reasons[-1]}"

    style = _normalize_explanation_style(explanation_style)
    context_text = _summarize_context_for_output(retrieved_context or [])

    if style == "curator":
        context_clause = (
            f" Retrieved notes reinforce that {context_text}."
            if context_text
            else " Retrieved notes did not add extra context for this pick."
        )
        return f"Curator note: {title} earns this spot because of {reason_text}.{context_clause}"

    if style == "studio":
        context_clause = (
            f" Studio reference: {context_text}."
            if context_text
            else " Studio reference: the score carries more of the decision than the retrieval layer."
        )
        return f"Studio take: {title} matches the listener through {reason_text}.{context_clause}"

    explanation = f"{title} stands out because {reason_text}."
    if context_text:
        explanation += f" Retrieved context suggests {context_text}."
    return explanation


def _summarize_context_for_output(retrieved_context: List[str]) -> str:
    """Compress retrieved notes into one short explanation clause."""

    snippets = []
    for item in retrieved_context[:2]:
        _, _, text = item.partition(": ")
        snippets.append(text.rstrip("."))

    if not snippets:
        return ""

    if len(snippets) == 1:
        return snippets[0]

    return snippets[0] + "; " + snippets[1]


def _collect_report_context(recommendations: List[RecommendationResult]) -> List[str]:
    """Collect the unique retrieval sections referenced by the final top-k list."""

    seen: set[str] = set()
    ordered: List[str] = []
    for result in recommendations:
        for item in result.retrieved_context:
            label = item.split(":", maxsplit=1)[0]
            if label not in seen:
                seen.add(label)
                ordered.append(label)
    return ordered


@lru_cache(maxsize=1)
def _load_knowledge_sources() -> Dict[str, Dict[str, str]]:
    """Load local retrieval documents from the knowledge directory."""

    base_dir = Path(__file__).resolve().parent.parent / "knowledge"
    return {
        "genre_notes": _parse_markdown_sections(base_dir / "genre_notes.md"),
        "mood_notes": _parse_markdown_sections(base_dir / "mood_notes.md"),
    }


def _parse_markdown_sections(path: Path) -> Dict[str, str]:
    """Parse a markdown document into a mapping of section title to body text."""

    sections: Dict[str, List[str]] = {}
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line.startswith("## "):
            current_key = line[3:].strip().lower()
            sections[current_key] = []
            continue
        if not line or current_key is None or line.startswith("# "):
            continue
        sections[current_key].append(line)

    return {key: " ".join(value) for key, value in sections.items()}


def _retrieve_context_sections(
    prefs: Dict[str, Any],
    song: Dict[str, Any],
    knowledge_sources: Dict[str, Dict[str, str]],
) -> List[str]:
    """Retrieve matching sections from multiple local knowledge sources."""

    requests = [
        ("genre_notes", prefs["genre"]),
        ("mood_notes", prefs["mood"]),
        ("genre_notes", str(song["genre"]).strip().lower()),
        ("mood_notes", str(song["mood"]).strip().lower()),
    ]

    seen_labels: set[str] = set()
    retrieved: List[str] = []
    for source_name, key in requests:
        if not key:
            continue
        source = knowledge_sources.get(source_name, {})
        if key not in source:
            continue

        label = f"{source_name}/{key}"
        if label in seen_labels:
            continue

        seen_labels.add(label)
        retrieved.append(f"{label}: {source[key]}")

    return retrieved
