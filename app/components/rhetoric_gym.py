"""
Rhetoric Gym - Practice rhetorical techniques with LingFrame feedback.
"""

import streamlit as st
from pathlib import Path
import yaml
from typing import Optional


def load_exercises() -> list[dict]:
    """Load exercises from the YAML file."""
    exercises_path = Path(__file__).resolve().parent.parent.parent / "data" / "exercises.yaml"

    if not exercises_path.exists():
        return []

    try:
        with open(exercises_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("exercises", [])
    except Exception:
        return []


def render_exercise_library(exercises: list[dict]) -> Optional[str]:
    """Render the exercise library with category filtering."""
    st.markdown("## Exercise Library")
    st.markdown("Choose an exercise to practice your rhetorical skills.")

    col1, col2 = st.columns(2)
    categories = sorted(set(e.get("category", "Other") for e in exercises))
    difficulties = ["beginner", "intermediate", "advanced"]

    with col1:
        selected_category = st.selectbox("Filter by Category", ["All"] + categories, key="gym_category_filter")
    with col2:
        selected_difficulty = st.selectbox("Filter by Difficulty", ["All"] + difficulties, key="gym_difficulty_filter")

    filtered = exercises
    if selected_category != "All":
        filtered = [e for e in filtered if e.get("category") == selected_category]
    if selected_difficulty != "All":
        filtered = [e for e in filtered if e.get("difficulty") == selected_difficulty]

    if not filtered:
        st.info("No exercises match the selected filters.")
        return None

    st.markdown("---")

    for exercise in filtered:
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                category_emoji = {"ethos": "🎓", "pathos": "❤️", "logos": "🧠"}.get(
                    exercise.get("category", "").lower(), "📝"
                )
                st.markdown(f"### {category_emoji} {exercise.get('name', 'Untitled')}")
                st.markdown(f"*{exercise.get('category', 'Unknown').title()} | {exercise.get('difficulty', 'Unknown').title()}*")
                prompt = exercise.get("prompt", "")
                if len(prompt) > 150:
                    st.markdown(prompt[:150] + "...")
                else:
                    st.markdown(prompt)
            with col2:
                word_limit = exercise.get("word_limit", [100, 150])
                st.markdown(f"**{word_limit[0]}-{word_limit[1]} words**")
                if st.button("Start", key=f"start_{exercise.get('id', 'unknown')}"):
                    return exercise.get("id")

    return None


def render_practice_interface(exercise: dict):
    """Render the practice writing interface."""
    category_emoji = {"ethos": "🎓", "pathos": "❤️", "logos": "🧠"}.get(
        exercise.get("category", "").lower(), "📝"
    )
    st.markdown(f"## {category_emoji} {exercise.get('name', 'Exercise')}")

    if st.button("← Back to Library"):
        st.session_state.gym_current_exercise = None
        st.session_state.gym_submission = None
        st.rerun()

    st.markdown("---")
    st.markdown("### Instructions")
    st.markdown(exercise.get("prompt", "Write your response."))

    tips = exercise.get("tips", [])
    if tips:
        st.markdown("### Tips")
        for tip in tips:
            st.markdown(f"- {tip}")

    example = exercise.get("example", "")
    if example:
        with st.expander("Show Example"):
            st.markdown(example)

    word_limit = exercise.get("word_limit", [100, 150])
    st.markdown(f"**Word limit:** {word_limit[0]}-{word_limit[1]} words")

    st.markdown("---")
    st.markdown("### Your Response")

    user_text = st.text_area("Write here", height=250, key="gym_user_text", label_visibility="collapsed")
    word_count = len(user_text.split()) if user_text.strip() else 0

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if word_count < word_limit[0]:
            st.warning(f"Words: {word_count}/{word_limit[0]} min")
        elif word_count > word_limit[1]:
            st.error(f"Words: {word_count}/{word_limit[1]} max")
        else:
            st.success(f"Words: {word_count}")

    with col2:
        can_submit = word_limit[0] <= word_count <= word_limit[1]
        if st.button("Submit for Feedback", disabled=not can_submit):
            st.session_state.gym_submission = user_text
            st.rerun()

    if st.session_state.get("gym_submission"):
        render_feedback_view(exercise, st.session_state.gym_submission)


def generate_feedback(text: str, exercise: dict) -> dict:
    """Generate feedback using LingFrame analysis."""
    try:
        from app.components.analysis_engine import run_analysis
        results = run_analysis(text, exercise.get("name", "Exercise"))

        if not results:
            return {"error": "Analysis failed"}

        focus = exercise.get("evaluation_focus", [])
        feedback = {
            "overall_score": 0,
            "strengths": [],
            "areas_for_improvement": [],
            "specific_feedback": {},
        }

        if "pathos" in focus and "sentiment" in results:
            sentiment = results["sentiment"]
            if sentiment.get("average_sentiment", 0) > 0.1:
                feedback["strengths"].append("Good emotional engagement with positive tone")
            elif sentiment.get("average_sentiment", 0) < -0.1:
                feedback["strengths"].append("Strong emotional impact with serious tone")
            feedback["specific_feedback"]["pathos"] = {
                "score": abs(sentiment.get("average_sentiment", 0)) * 100,
                "note": "Emotional resonance detected"
            }

        if "ethos" in focus and "entity" in results:
            entities = results["entity"]
            if entities.get("total_entities", 0) > 3:
                feedback["strengths"].append("Good use of specific references")
            else:
                feedback["areas_for_improvement"].append("Consider adding more specific references")
            feedback["specific_feedback"]["ethos"] = {
                "score": min(entities.get("total_entities", 0) * 15, 100),
                "note": f"Found {entities.get('total_entities', 0)} references"
            }

        if "logos" in focus and "semantic" in results:
            semantic = results["semantic"]
            if semantic.get("theme_count", 0) > 2:
                feedback["strengths"].append("Clear logical structure")
            feedback["specific_feedback"]["logos"] = {
                "score": min(semantic.get("theme_count", 0) * 25, 100),
                "note": f"Identified {semantic.get('theme_count', 0)} themes"
            }

        scores = [v.get("score", 0) for v in feedback["specific_feedback"].values()]
        if scores:
            feedback["overall_score"] = sum(scores) / len(scores)

        return feedback

    except Exception as e:
        return {"error": str(e)}


def render_feedback_view(exercise: dict, submission: str):
    """Render feedback on the submitted writing."""
    st.markdown("---")
    st.markdown("## Feedback")

    with st.spinner("Analyzing your writing..."):
        feedback = generate_feedback(submission, exercise)

    if "error" in feedback:
        st.error(f"Could not generate feedback: {feedback['error']}")
        return

    score = feedback.get("overall_score", 0)
    col1, col2 = st.columns([1, 3])

    with col1:
        st.metric("Score", f"{score:.0f}/100")
    with col2:
        if score >= 70:
            st.success("Great work! Strong rhetorical technique.")
        elif score >= 50:
            st.info("Good effort! Room for improvement.")
        else:
            st.warning("Keep practicing!")

    strengths = feedback.get("strengths", [])
    if strengths:
        st.markdown("### Strengths")
        for s in strengths:
            st.markdown(f"✅ {s}")

    improvements = feedback.get("areas_for_improvement", [])
    if improvements:
        st.markdown("### Areas for Improvement")
        for i in improvements:
            st.markdown(f"💡 {i}")

    specific = feedback.get("specific_feedback", {})
    if specific:
        st.markdown("### Category Scores")
        cols = st.columns(len(specific))
        for col, (category, data) in zip(cols, specific.items()):
            with col:
                emoji = {"ethos": "🎓", "pathos": "❤️", "logos": "🧠"}.get(category, "📊")
                st.metric(f"{emoji} {category.title()}", f"{data.get('score', 0):.0f}")
                st.caption(data.get("note", ""))

    st.markdown("---")
    if st.button("Try Again"):
        st.session_state.gym_submission = None
        st.rerun()


def render_rhetoric_gym():
    """Main entry point for the Rhetoric Gym feature."""
    st.markdown("# Rhetoric Gym")
    st.markdown("Practice rhetorical techniques and get instant feedback.")

    if "gym_current_exercise" not in st.session_state:
        st.session_state.gym_current_exercise = None
    if "gym_submission" not in st.session_state:
        st.session_state.gym_submission = None

    exercises = load_exercises()

    if not exercises:
        st.warning("No exercises found.")
        st.markdown("Add exercises to `data/exercises.yaml` to get started.")
        return

    if st.session_state.gym_current_exercise:
        exercise = next(
            (e for e in exercises if e.get("id") == st.session_state.gym_current_exercise),
            None
        )
        if exercise:
            render_practice_interface(exercise)
        else:
            st.session_state.gym_current_exercise = None
            st.rerun()
    else:
        selected = render_exercise_library(exercises)
        if selected:
            st.session_state.gym_current_exercise = selected
            st.rerun()
