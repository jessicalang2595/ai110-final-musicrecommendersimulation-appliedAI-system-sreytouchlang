from src.recommender import (
    Recommender,
    Song,
    UserProfile,
    load_songs,
    recommend_songs,
    score_song,
)


def make_song(
    *,
    id: int,
    title: str,
    genre: str,
    mood: str,
    energy: float,
    acousticness: float,
) -> Song:
    return Song(
        id=id,
        title=title,
        artist="Test Artist",
        genre=genre,
        mood=mood,
        energy=energy,
        tempo_bpm=120,
        valence=0.7,
        danceability=0.7,
        acousticness=acousticness,
    )


def make_song_dict(
    *,
    id: int,
    title: str,
    genre: str,
    mood: str,
    energy: float,
    acousticness: float,
):
    return {
        "id": id,
        "title": title,
        "artist": "Test Artist",
        "genre": genre,
        "mood": mood,
        "energy": energy,
        "tempo_bpm": 120.0,
        "valence": 0.7,
        "danceability": 0.7,
        "acousticness": acousticness,
    }


def make_user(*, likes_acoustic: bool = False) -> UserProfile:
    return UserProfile(
        favorite_genre="pop",
        favorite_mood="happy",
        target_energy=0.8,
        likes_acoustic=likes_acoustic,
    )


def make_user_prefs(*, likes_acoustic: bool = False):
    return {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "likes_acoustic": likes_acoustic,
    }

def make_small_recommender() -> Recommender:
    songs = [
        make_song(
            id=1,
            title="Test Pop Track",
            genre="pop",
            mood="happy",
            energy=0.8,
            acousticness=0.2,
        ),
        make_song(
            id=2,
            title="Chill Lofi Loop",
            genre="lofi",
            mood="chill",
            energy=0.4,
            acousticness=0.9,
        ),
    ]
    return Recommender(songs)


def test_recommend_returns_songs_sorted_by_score():
    user = make_user()
    rec = make_small_recommender()
    results = rec.recommend(user, k=2)

    assert len(results) == 2
    # Starter expectation: the pop, happy, high energy song should score higher
    assert results[0].genre == "pop"
    assert results[0].mood == "happy"


def test_explain_recommendation_returns_non_empty_string():
    user = make_user()
    rec = make_small_recommender()
    song = rec.songs[0]

    explanation = rec.explain_recommendation(user, song)
    assert isinstance(explanation, str)
    assert explanation.strip() != ""
    assert "stands out because" in explanation


def test_score_song_favors_genre_and_mood_matches():
    user_prefs = make_user_prefs()
    strong_match = make_song_dict(
        id=1,
        title="Bright Pop Anthem",
        genre="pop",
        mood="happy",
        energy=0.78,
        acousticness=0.2,
    )
    weaker_match = make_song_dict(
        id=2,
        title="Calm Study Loop",
        genre="lofi",
        mood="focused",
        energy=0.78,
        acousticness=0.2,
    )

    strong_score, strong_reasons = score_song(user_prefs, strong_match)
    weak_score, _ = score_song(user_prefs, weaker_match)

    assert strong_score > weak_score
    assert any("genre match" in reason for reason in strong_reasons)
    assert any("mood match" in reason for reason in strong_reasons)


def test_score_song_prefers_closer_energy_when_other_features_are_equal():
    user_prefs = make_user_prefs()
    close_energy_song = make_song_dict(
        id=1,
        title="Near Energy Match",
        genre="indie",
        mood="chill",
        energy=0.76,
        acousticness=0.5,
    )
    far_energy_song = make_song_dict(
        id=2,
        title="Far Energy Match",
        genre="indie",
        mood="chill",
        energy=0.25,
        acousticness=0.5,
    )

    close_score, _ = score_song(user_prefs, close_energy_song)
    far_score, _ = score_song(user_prefs, far_energy_song)

    assert close_score > far_score


def test_score_song_respects_acoustic_preference():
    acoustic_song = make_song_dict(
        id=1,
        title="Wooden Session",
        genre="folk",
        mood="calm",
        energy=0.5,
        acousticness=0.9,
    )

    acoustic_lover_score, _ = score_song(make_user_prefs(likes_acoustic=True), acoustic_song)
    acoustic_avoider_score, _ = score_song(make_user_prefs(likes_acoustic=False), acoustic_song)

    assert acoustic_lover_score > acoustic_avoider_score


def test_load_songs_parses_numeric_fields(tmp_path):
    csv_path = tmp_path / "songs.csv"
    csv_path.write_text(
        (
            "id,title,artist,genre,mood,energy,tempo_bpm,valence,danceability,acousticness\n"
            "1,Sample Song,Sample Artist,pop,happy,0.8,120,0.7,0.9,0.2\n"
        ),
        encoding="utf-8",
    )

    songs = load_songs(str(csv_path))

    assert songs[0]["id"] == 1
    assert isinstance(songs[0]["id"], int)
    assert isinstance(songs[0]["energy"], float)
    assert isinstance(songs[0]["tempo_bpm"], float)


def test_recommend_songs_returns_sorted_top_k_with_explanations():
    songs = [
        make_song_dict(
            id=1,
            title="Top Match",
            genre="pop",
            mood="happy",
            energy=0.8,
            acousticness=0.2,
        ),
        make_song_dict(
            id=2,
            title="Second Match",
            genre="pop",
            mood="intense",
            energy=0.82,
            acousticness=0.1,
        ),
        make_song_dict(
            id=3,
            title="Lower Match",
            genre="ambient",
            mood="calm",
            energy=0.2,
            acousticness=0.9,
        ),
    ]

    recommendations = recommend_songs({"genre": "pop", "mood": "happy", "energy": 0.8}, songs, k=2)

    assert len(recommendations) == 2
    assert recommendations[0][0]["title"] == "Top Match"
    assert recommendations[0][1] >= recommendations[1][1]
    assert recommendations[0][2].strip() != ""
    assert "stands out because" in recommendations[0][2]
