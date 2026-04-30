from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from src.recommender import DEFAULT_EXPLANATION_STYLE, SUPPORTED_STYLES, load_songs, recommend_with_report

APP_TITLE = "VibeMatch Reliable Recommender"
APP_ICON = "🎧"
DEFAULT_CHAT_GREETING = (
    "Hey! I'd love to help you find some great music. Tell me what genres, mood, and energy "
    "you want, or describe your vibe in plain English."
)


def load_catalog() -> List[Dict[str, Any]]:
    data_path = Path(__file__).resolve().parent / "data" / "songs.csv"
    return load_songs(str(data_path))


SONGS = load_catalog()
AVAILABLE_GENRES = sorted({song["genre"] for song in SONGS})
AVAILABLE_MOODS = sorted({song["mood"] for song in SONGS})


def init_session_state() -> None:
    if "username" not in st.session_state:
        st.session_state.username = "Butch"
    if "feedback_count" not in st.session_state:
        st.session_state.feedback_count = 0
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": DEFAULT_CHAT_GREETING},
        ]
    if "active_profile" not in st.session_state:
        st.session_state.active_profile = {
            "genre": "pop",
            "mood": "happy",
            "energy": 0.8,
            "likes_acoustic": False,
        }
    if "active_style" not in st.session_state:
        st.session_state.active_style = "curator"
    if "active_report" not in st.session_state:
        st.session_state.active_report = recommend_with_report(
            st.session_state.active_profile,
            SONGS,
            k=5,
            explanation_style=st.session_state.active_style,
        )
    if "last_prompt" not in st.session_state:
        st.session_state.last_prompt = ""


def reset_profile() -> None:
    st.session_state.feedback_count = 0
    st.session_state.chat_history = [{"role": "assistant", "content": DEFAULT_CHAT_GREETING}]
    st.session_state.active_profile = {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.8,
        "likes_acoustic": False,
    }
    st.session_state.active_style = "curator"
    st.session_state.active_report = recommend_with_report(
        st.session_state.active_profile,
        SONGS,
        k=5,
        explanation_style=st.session_state.active_style,
    )
    st.session_state.last_prompt = ""


def parse_prompt_to_profile(prompt: str) -> Dict[str, Any]:
    lowered = prompt.strip().lower()
    profile: Dict[str, Any] = {
        "genre": "",
        "mood": "",
        "energy": 0.5,
        "likes_acoustic": False,
    }

    for genre in sorted(AVAILABLE_GENRES, key=len, reverse=True):
        if genre in lowered:
            profile["genre"] = genre
            break

    for mood in sorted(AVAILABLE_MOODS, key=len, reverse=True):
        if mood in lowered:
            profile["mood"] = mood
            break

    acoustic_keywords = {"acoustic", "soft", "warm", "organic", "stripped-back", "folk"}
    if any(keyword in lowered for keyword in acoustic_keywords):
        profile["likes_acoustic"] = True

    energy_map = [
        ({"high energy", "energetic", "workout", "gym", "hype", "fast", "intense"}, 0.88),
        ({"upbeat", "dance", "drive", "party"}, 0.75),
        ({"medium energy", "steady", "balanced"}, 0.55),
        ({"chill", "focus", "study", "calm", "quiet", "relax", "sleep"}, 0.35),
    ]
    for keywords, value in energy_map:
        if any(keyword in lowered for keyword in keywords):
            profile["energy"] = value
            break

    if not profile["genre"] and "indie" in lowered:
        profile["genre"] = "indie"
    if not profile["mood"] and "happy" in lowered:
        profile["mood"] = "happy"

    return profile


def format_profile_summary(profile: Dict[str, Any], style: str) -> str:
    acoustic_text = "yes" if profile["likes_acoustic"] else "no"
    return (
        f"I translated that into a listener profile with genre=`{profile['genre'] or 'none'}`, "
        f"mood=`{profile['mood'] or 'none'}`, energy=`{profile['energy']:.2f}`, "
        f"likes_acoustic=`{acoustic_text}`, and explanation style=`{style}`."
    )


def build_assistant_reply(report: Any) -> str:
    top = report.recommendations[0]
    warning_text = report.warnings[0] if report.warnings else "No warning was needed for this run."
    return (
        f"My top pick is **{top.song['title']}** by **{top.song['artist']}** with confidence "
        f"**{top.confidence:.2f}**. {warning_text}\n\n"
        f"{top.explanation}"
    )


def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(f"## {APP_ICON} Music Recommender")
        st.caption("Reliable applied-AI music matching")
        st.text_input("Username", key="username")
        st.caption(f"Feedback given: {st.session_state.feedback_count}")
        if st.button("Reset this profile", use_container_width=True):
            reset_profile()
            st.rerun()

        st.markdown("### Quick Settings")
        selected_style = st.selectbox(
            "Explanation style",
            options=sorted(SUPPORTED_STYLES),
            index=sorted(SUPPORTED_STYLES).index(st.session_state.active_style),
        )
        st.session_state.active_style = selected_style

        st.markdown("### Profile Controls")
        with st.form("profile_controls"):
            genre = st.selectbox(
                "Favorite genre",
                options=[""] + AVAILABLE_GENRES,
                index=([""] + AVAILABLE_GENRES).index(st.session_state.active_profile["genre"])
                if st.session_state.active_profile["genre"] in AVAILABLE_GENRES
                else 0,
            )
            mood = st.selectbox(
                "Favorite mood",
                options=[""] + AVAILABLE_MOODS,
                index=([""] + AVAILABLE_MOODS).index(st.session_state.active_profile["mood"])
                if st.session_state.active_profile["mood"] in AVAILABLE_MOODS
                else 0,
            )
            energy = st.slider(
                "Target energy",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.active_profile["energy"]),
                step=0.05,
            )
            likes_acoustic = st.toggle(
                "Likes acoustic textures",
                value=bool(st.session_state.active_profile["likes_acoustic"]),
            )
            if st.form_submit_button("Update profile", use_container_width=True):
                st.session_state.active_profile = {
                    "genre": genre,
                    "mood": mood,
                    "energy": energy,
                    "likes_acoustic": likes_acoustic,
                }
                st.session_state.active_report = recommend_with_report(
                    st.session_state.active_profile,
                    SONGS,
                    k=5,
                    explanation_style=st.session_state.active_style,
                )
                st.session_state.chat_history.append(
                    {
                        "role": "assistant",
                        "content": format_profile_summary(st.session_state.active_profile, st.session_state.active_style),
                    }
                )
                st.rerun()


def render_chat_tab() -> None:
    st.markdown("## Tell me what you're in the mood for")
    st.caption("Type something like: `happy pop for a workout`, `chill acoustic study music`, or `intense rock drive`.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    prompt = st.chat_input("Your answer...")
    if prompt:
        st.session_state.last_prompt = prompt
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        inferred_profile = parse_prompt_to_profile(prompt)
        if not inferred_profile["genre"] and st.session_state.active_profile["genre"]:
            inferred_profile["genre"] = st.session_state.active_profile["genre"]
        if not inferred_profile["mood"] and st.session_state.active_profile["mood"]:
            inferred_profile["mood"] = st.session_state.active_profile["mood"]

        st.session_state.active_profile = inferred_profile
        st.session_state.active_report = recommend_with_report(
            inferred_profile,
            SONGS,
            k=5,
            explanation_style=st.session_state.active_style,
        )
        assistant_message = (
            format_profile_summary(inferred_profile, st.session_state.active_style)
            + "\n\n"
            + build_assistant_reply(st.session_state.active_report)
        )
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})
        st.rerun()


def render_picks_tab() -> None:
    report = st.session_state.active_report
    metrics = report.metrics
    hero = report.recommendations[0]

    metric_cols = st.columns(4)
    metric_cols[0].metric("Top Confidence", f"{hero.confidence:.2f}")
    metric_cols[1].metric("Avg Confidence", f"{metrics['average_confidence']:.2f}")
    metric_cols[2].metric("Genre Diversity", f"{metrics['genre_diversity_ratio']:.2f}")
    metric_cols[3].metric("Retrieval Coverage", f"{metrics['retrieval_coverage_ratio']:.2f}")

    st.markdown("### Top picks")
    for index, result in enumerate(report.recommendations, start=1):
        song = result.song
        with st.container(border=True):
            top_cols = st.columns([4, 1.2, 1.2])
            top_cols[0].markdown(
                f"**#{index} {song['title']}**  \n"
                f"{song['artist']} • `{song['genre']}` • `{song['mood']}`"
            )
            top_cols[1].metric("Score", f"{result.adjusted_score:.2f}")
            top_cols[2].metric("Confidence", f"{result.confidence:.2f}")

            st.markdown(f"**Why it matched**: {', '.join(result.reasons[:3])}")
            st.markdown(result.explanation)
            st.caption(result.critique)
            if result.retrieved_context:
                with st.expander("Retrieved context"):
                    for item in result.retrieved_context:
                        st.markdown(f"- {item}")


def render_profile_tab() -> None:
    report = st.session_state.active_report
    profile = report.normalized_user_prefs

    left, right = st.columns([1, 1.2])
    with left:
        st.markdown("### Active profile")
        st.json(profile)
        st.markdown("### Warnings")
        if report.warnings:
            for warning in report.warnings:
                st.warning(warning, icon="⚠️")
        else:
            st.success("No reliability warnings for this profile.", icon="✅")

    with right:
        st.markdown("### Workflow trace")
        for step in report.workflow_trace:
            st.markdown(f"- {step}")
        st.markdown("### Retrieved sections")
        if report.retrieved_sections:
            st.markdown(", ".join(f"`{section}`" for section in report.retrieved_sections))
        else:
            st.caption("No retrieval sections were attached to the final top-k list.")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top, #171924 0%, #0b0d12 55%, #090a0f 100%);
            color: #f7f3ee;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #262531 0%, #222330 100%);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
        }
        [data-testid="stSidebar"] * {
            color: #f7f3ee;
        }
        [data-testid="stChatMessage"] {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 18px;
            padding: 0.55rem 0.8rem;
            margin-bottom: 0.7rem;
        }
        [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }
        [data-baseweb="tab"] {
            background: transparent;
            color: #c9c5bf;
            border-bottom: 2px solid transparent;
            padding-bottom: 0.8rem;
        }
        [data-baseweb="tab"][aria-selected="true"] {
            color: #ff6f61;
            border-bottom-color: #ff6f61;
        }
        .stButton button, .stDownloadButton button {
            border-radius: 14px;
        }
        .stTextInput input, .stTextArea textarea {
            border-radius: 14px;
        }
        .block-container {
            padding-top: 1.4rem;
            max-width: 1150px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
    init_session_state()
    inject_styles()
    render_sidebar()

    st.title("Tell me what you're in the mood for")
    st.caption("A chat-style front end for the reliable music recommender.")

    tabs = st.tabs(["💬 Chat", "🎼 Picks", "📊 Profile"])
    with tabs[0]:
        render_chat_tab()
    with tabs[1]:
        render_picks_tab()
    with tabs[2]:
        render_profile_tab()


if __name__ == "__main__":
    main()
