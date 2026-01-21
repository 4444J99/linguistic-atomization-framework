"""
Corpus Observatory - Browse and compare texts in the literary corpus.
"""

import streamlit as st
from pathlib import Path
import re
from typing import Optional


def load_corpus_index() -> list[dict]:
    """Load corpus texts by scanning the corpus directory."""
    corpus_dir = Path(__file__).resolve().parent.parent.parent / "corpus"
    texts = []

    if not corpus_dir.exists():
        return texts

    for text_dir in corpus_dir.iterdir():
        if not text_dir.is_dir() or text_dir.name.startswith('.'):
            continue

        readme_path = text_dir / "README.md"
        metadata = {
            "id": text_dir.name,
            "title": text_dir.name.replace("-", " ").title(),
            "path": str(text_dir),
            "period": "Unknown",
            "language": "Unknown",
            "author": "Unknown",
            "description": "",
        }

        if readme_path.exists():
            content = readme_path.read_text(encoding="utf-8", errors="ignore")
            title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if title_match:
                metadata["title"] = title_match.group(1).strip()
            author_match = re.search(r'\*\*Author[:\*]*\*?\*?\s*(.+)', content, re.IGNORECASE)
            if author_match:
                metadata["author"] = author_match.group(1).strip()
            period_match = re.search(r'\*\*Period[:\*]*\*?\*?\s*(.+)', content, re.IGNORECASE)
            if period_match:
                metadata["period"] = period_match.group(1).strip()
            lang_match = re.search(r'\*\*Language[:\*]*\*?\*?\s*(.+)', content, re.IGNORECASE)
            if lang_match:
                metadata["language"] = lang_match.group(1).strip()

        for ext in [".txt", ".md"]:
            text_files = list(text_dir.glob(f"*{ext}"))
            if text_files:
                main_file = [f for f in text_files if f.name != "README.md"]
                if main_file:
                    metadata["text_file"] = str(main_file[0])
                    break

        texts.append(metadata)

    return sorted(texts, key=lambda x: x["title"])


def render_corpus_browser(texts: list[dict]) -> Optional[str]:
    """Render the corpus browser with filtering."""
    st.markdown("## Literary Corpus")
    st.markdown("Browse classic texts from the literary corpus.")

    col1, col2 = st.columns(2)
    periods = sorted(set(t["period"] for t in texts))
    languages = sorted(set(t["language"] for t in texts))

    with col1:
        selected_period = st.selectbox("Filter by Period", ["All"] + periods, key="corpus_period_filter")
    with col2:
        selected_language = st.selectbox("Filter by Language", ["All"] + languages, key="corpus_language_filter")

    filtered = texts
    if selected_period != "All":
        filtered = [t for t in filtered if t["period"] == selected_period]
    if selected_language != "All":
        filtered = [t for t in filtered if t["language"] == selected_language]

    if not filtered:
        st.info("No texts match the selected filters.")
        return None

    st.markdown("---")
    cols = st.columns(3)

    for i, text in enumerate(filtered):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(f"### {text['title']}")
                st.markdown(f"**{text['author']}**")
                st.markdown(f"*{text['period']} | {text['language']}*")
                if st.button("View Details", key=f"view_{text['id']}"):
                    return text['id']
    return None


def render_text_detail(text: dict):
    """Render detailed view of a single text."""
    st.markdown(f"## {text['title']}")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Author:** {text['author']}")
        st.markdown(f"**Period:** {text['period']}")
        st.markdown(f"**Language:** {text['language']}")
    with col2:
        if st.button("Back to Browser"):
            st.session_state.corpus_selected_text = None
            st.rerun()
        if st.button("Add to Comparison"):
            if "corpus_comparison" not in st.session_state:
                st.session_state.corpus_comparison = []
            if text['id'] not in st.session_state.corpus_comparison:
                st.session_state.corpus_comparison.append(text['id'])
                st.success(f"Added {text['title']} to comparison")

    if "text_file" in text:
        st.markdown("---")
        st.markdown("### Preview")
        try:
            with open(text["text_file"], "r", encoding="utf-8", errors="ignore") as f:
                preview = f.read(2000)
                st.text_area("Text Preview", preview, height=300, disabled=True)
        except Exception as e:
            st.warning(f"Could not load preview: {e}")

        st.markdown("---")
        st.markdown("### Quick Stats")
        try:
            with open(text["text_file"], "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            col1, col2, col3 = st.columns(3)
            col1.metric("Words", f"{len(content.split()):,}")
            col2.metric("Lines", f"{len(content.splitlines()):,}")
            col3.metric("Characters", f"{len(content):,}")
        except Exception:
            pass


def render_comparison(texts: list[dict]):
    """Render side-by-side comparison of texts."""
    st.markdown("## Text Comparison")

    if "corpus_comparison" not in st.session_state or len(st.session_state.corpus_comparison) < 2:
        st.info("Select at least 2 texts from the browser to compare.")
        if st.button("Back to Browser"):
            st.session_state.corpus_view = "browser"
            st.rerun()
        return

    text_lookup = {t["id"]: t for t in texts}
    compare_texts = [text_lookup[tid] for tid in st.session_state.corpus_comparison[:2] if tid in text_lookup]

    if len(compare_texts) < 2:
        st.error("Could not find selected texts.")
        return

    col1, col2 = st.columns(2)
    for col, text in zip([col1, col2], compare_texts):
        with col:
            st.markdown(f"### {text['title']}")
            st.markdown(f"*{text['author']}*")
            if "text_file" in text:
                try:
                    with open(text["text_file"], "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    st.metric("Words", f"{len(content.split()):,}")
                    st.metric("Lines", f"{len(content.splitlines()):,}")
                except Exception:
                    pass

    if st.button("Clear Comparison"):
        st.session_state.corpus_comparison = []
        st.session_state.corpus_view = "browser"
        st.rerun()


def render_corpus_observatory():
    """Main entry point for the Corpus Observatory feature."""
    st.markdown("# Corpus Observatory")

    if "corpus_view" not in st.session_state:
        st.session_state.corpus_view = "browser"
    if "corpus_selected_text" not in st.session_state:
        st.session_state.corpus_selected_text = None

    texts = load_corpus_index()

    if not texts:
        st.warning("No texts found in corpus directory.")
        return

    tab1, tab2 = st.tabs(["Browse", "Compare"])

    with tab1:
        if st.session_state.corpus_selected_text:
            text = next((t for t in texts if t["id"] == st.session_state.corpus_selected_text), None)
            if text:
                render_text_detail(text)
            else:
                st.session_state.corpus_selected_text = None
                st.rerun()
        else:
            selected = render_corpus_browser(texts)
            if selected:
                st.session_state.corpus_selected_text = selected
                st.rerun()

    with tab2:
        render_comparison(texts)
