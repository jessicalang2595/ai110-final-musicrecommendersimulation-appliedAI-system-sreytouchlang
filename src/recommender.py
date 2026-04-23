import csv
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

GENRE_WEIGHT = 4.0
MOOD_WEIGHT = 2.5
ENERGY_WEIGHT = 2.0
ACOUSTIC_WEIGHT = 1.5


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
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        user_prefs = _user_profile_to_dict(user)
        ranked_songs = sorted(
            self.songs,
            key=lambda song: _score_song_data(user_prefs, asdict(song))[0],
            reverse=True,
        )
        return ranked_songs[:k]

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
    return songs


def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Scores a single song against user preferences.
    Required by recommend_songs() and src/main.py
    """
    # Expected return format: (score, reasons)
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


def _score_song_data(user_prefs: Dict[str, Any], song: Dict[str, Any]) -> Tuple[float, List[str]]:
    """Apply the weighted scoring recipe and return score plus reasons."""
    prefs = _normalize_user_prefs(user_prefs)
    genre = str(song["genre"]).strip().lower()
    mood = str(song["mood"]).strip().lower()
    energy = float(song["energy"])
    acousticness = float(song["acousticness"])

    score = 0.0
    reason_candidates: List[Tuple[float, str]] = []

    if prefs["genre"] and genre == prefs["genre"]:
        score += GENRE_WEIGHT
        reason_candidates.append((GENRE_WEIGHT, f"genre match (+{GENRE_WEIGHT:.1f})"))

    if prefs["mood"] and mood == prefs["mood"]:
        score += MOOD_WEIGHT
        reason_candidates.append((MOOD_WEIGHT, f"mood match (+{MOOD_WEIGHT:.1f})"))

    energy_closeness = max(0.0, 1 - abs(energy - prefs["energy"]))
    energy_score = energy_closeness * ENERGY_WEIGHT
    score += energy_score
    if energy_closeness >= 0.85:
        reason_candidates.append((energy_score, f"energy closeness (+{energy_score:.2f})"))
    elif energy_closeness >= 0.65:
        reason_candidates.append((energy_score, f"energy similarity (+{energy_score:.2f})"))

    acoustic_fit = acousticness if prefs["likes_acoustic"] else 1 - acousticness
    acoustic_score = acoustic_fit * ACOUSTIC_WEIGHT
    score += acoustic_score
    if prefs["likes_acoustic"] and acousticness >= 0.6:
        reason_candidates.append((acoustic_score, f"acoustic preference fit (+{acoustic_score:.2f})"))
    elif not prefs["likes_acoustic"] and acousticness <= 0.4:
        reason_candidates.append((acoustic_score, f"low-acoustic preference fit (+{acoustic_score:.2f})"))

    reason_candidates.sort(key=lambda item: item[0], reverse=True)
    reasons = [reason for _, reason in reason_candidates]
    if not reasons:
        reasons.append("closest overall match in this small catalog")

    return round(score, 3), reasons


def _build_explanation(title: str, reasons: List[str]) -> str:
    """Turn the strongest score reasons into a short recommendation sentence."""
    top_reasons = reasons[:3]
    if len(top_reasons) == 1:
        reason_text = top_reasons[0]
    elif len(top_reasons) == 2:
        reason_text = " and ".join(top_reasons)
    else:
        reason_text = ", ".join(top_reasons[:-1]) + f", and {top_reasons[-1]}"

    return f"{title} stands out because {reason_text}."
