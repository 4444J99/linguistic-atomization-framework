"""
Corpus Observatory - Browse and compare texts in the literary corpus.

Supports multilingual corpus with:
- Western tradition (Latin, Greek, Cyrillic scripts)
- Eastern tradition (Chinese, Japanese, Arabic, Devanagari scripts)
- Original language texts and multiple translations
- Language/script detection and display
"""

import streamlit as st
from pathlib import Path
import re
import yaml
from typing import Optional, Dict, List, Any

# Script to emoji/flag mapping for visual display
SCRIPT_DISPLAY = {
    "latin": "🔤",
    "greek": "🏛️",
    "cyrillic": "🇷🇺",
    "arabic": "🕌",
    "hebrew": "✡️",
    "devanagari": "🕉️",
    "chinese": "🇨🇳",
    "japanese": "🇯🇵",
    "korean": "🇰🇷",
    "thai": "🇹🇭",
    "unknown": "📝",
}

LANGUAGE_NAMES = {
    "en": "English", "de": "German", "fr": "French", "es": "Spanish",
    "it": "Italian", "pt": "Portuguese", "ru": "Russian", "el": "Greek",
    "la": "Latin", "grc": "Ancient Greek", "ang": "Old English", "enm": "Middle English",
    "zh": "Chinese", "ja": "Japanese", "ko": "Korean",
    "ar": "Arabic", "fa": "Persian", "he": "Hebrew",
    "hi": "Hindi", "sa": "Sanskrit", "bn": "Bengali", "ta": "Tamil",
    "th": "Thai", "fro": "Old French", "akk": "Akkadian",
}


def get_script_emoji(script: str) -> str:
    """Get emoji for script type."""
    return SCRIPT_DISPLAY.get(script.lower(), "📝")


def get_language_name(code: str) -> str:
    """Get human-readable language name from code."""
    return LANGUAGE_NAMES.get(code.lower(), code.upper())

def load_corpus_index() -> list[dict]:
    """Load corpus texts by scanning the nested corpus directory structure.
    
    Structure: corpus/{tradition}/{period}/{text}/
    Also reads corpus_index.yaml for metadata about planned texts.
    """
    corpus_dir = Path(__file__).resolve().parent.parent.parent / "corpus"
    texts = []
    
    if not corpus_dir.exists():
        return texts
    
    # Try to load corpus_index.yaml for additional metadata
    index_metadata = {}
    index_path = corpus_dir / "corpus_index.yaml"
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = yaml.safe_load(f)
                # Flatten the nested structure for lookup
                for tradition in ['western', 'eastern']:
                    if tradition in index_data:
                        for period, period_texts in index_data[tradition].items():
                            if isinstance(period_texts, dict):
                                for text_id, text_meta in period_texts.items():
                                    if isinstance(text_meta, dict):
                                        key = f"{tradition}/{period}/{text_id}"
                                        index_metadata[text_id] = text_meta
        except Exception:
            pass

    # Scan both western and eastern traditions, and legacy flat structure
    tradition_dirs = [corpus_dir]
    for tradition in ['western', 'eastern']:
        tradition_path = corpus_dir / tradition
        if tradition_path.exists():
            tradition_dirs.append(tradition_path)
    
    for base_dir in tradition_dirs:
        # Scan period directories
        for period_dir in base_dir.iterdir():
            if not period_dir.is_dir() or period_dir.name.startswith('.'):
                continue
            if period_dir.name in ['western', 'eastern']:
                continue  # Skip tradition directories when scanning from corpus_dir
            
            period_name = period_dir.name.replace("-", " ").title()
            tradition = base_dir.name if base_dir != corpus_dir else "legacy"
            
            # Scan text directories within each period
            for text_dir in period_dir.iterdir():
                if not text_dir.is_dir() or text_dir.name.startswith('.'):
                    continue

                readme_path = text_dir / "README.md"
                text_key = text_dir.name.replace("-", "_")
                index_meta = index_metadata.get(text_key, {})
                
                metadata = {
                    "id": f"{period_dir.name}/{text_dir.name}",
                    "title": index_meta.get("title", text_dir.name.replace("-", " ").title()),
                    "original_title": index_meta.get("original_title"),
                    "path": str(text_dir),
                    "period": period_name,
                    "tradition": tradition.title() if tradition != "legacy" else None,
                    "language": index_meta.get("original_language", "en"),
                    "script": index_meta.get("script", "latin"),
                    "author": index_meta.get("author", "Unknown"),
                    "description": "",
                    "files": [],
                    "translations": index_meta.get("translations", []),
                }

                # Parse README for metadata
                if readme_path.exists():
                    file_content = readme_path.read_text(encoding="utf-8", errors="ignore")
                    
                    # Extract title from first heading
                    title_match = re.search(r'^#\s+(.+)$', file_content, re.MULTILINE)
                    if title_match and not index_meta.get("title"):
                        metadata["title"] = title_match.group(1).strip()
                    
                    # Extract author
                    author_match = re.search(r'\*\*Author[:\*]*\*?\*?\s*(.+)', file_content, re.IGNORECASE)
                    if author_match and metadata["author"] == "Unknown":
                        metadata["author"] = author_match.group(1).strip().rstrip('*')
                    
                    # Extract description
                    desc_match = re.search(r'^#.+\n\n(.+?)(?:\n\n|\n---|\n\*\*)', file_content, re.MULTILINE | re.DOTALL)
                    if desc_match:
                        metadata["description"] = desc_match.group(1).strip()[:200]

                # Find all text files
                text_files = list(text_dir.glob("*.txt"))
                if text_files:
                    metadata["files"] = [
                        {
                            "name": f.stem.replace("_", " ").title(),
                            "path": str(f),
                            "lines": sum(1 for _ in open(f, encoding="utf-8", errors="ignore")),
                            "is_original": "original" in f.name.lower() or metadata["language"] in f.name.lower(),
                        }
                        for f in sorted(text_files)
                    ]
                    # Set primary text file (prefer English translation, then original)
                    english_files = [f for f in text_files if "english" in f.name.lower()]
                    original_files = [f for f in text_files if "original" in f.name.lower()]
                    metadata["text_file"] = str(english_files[0] if english_files else (original_files[0] if original_files else text_files[0]))
                
                # Only add if there are actual text files
                if metadata["files"]:
                    texts.append(metadata)

    return sorted(texts, key=lambda x: (x.get("tradition") or "", x["period"], x["title"]))


def render_corpus_browser(texts: list[dict]) -> Optional[str]:
    """Render the corpus browser with filtering."""
    st.markdown("## 📚 Literary Corpus")
    st.markdown("Browse classic texts from antiquity to the modern era.")

    # Filters
    col1, col2 = st.columns(2)
    periods = sorted(set(t["period"] for t in texts))
    
    with col1:
        selected_period = st.selectbox(
            "Filter by Period", 
            ["All Periods"] + periods, 
            key="corpus_period_filter"
        )
    with col2:
        search_query = st.text_input("Search texts", key="corpus_search", placeholder="Search by title or author...")

    # Apply filters
    filtered = texts
    if selected_period != "All Periods":
        filtered = [t for t in filtered if t["period"] == selected_period]
    if search_query:
        query = search_query.lower()
        filtered = [t for t in filtered if query in t["title"].lower() or query in t["author"].lower()]

    # Stats
    st.markdown(f"**{len(filtered)}** texts available")
    
    if not filtered:
        st.info("No texts match the selected filters.")
        return None

    st.markdown("---")
    
    # Display texts in grid
    cols = st.columns(2)
    for i, text in enumerate(filtered):
        with cols[i % 2]:
            with st.container(border=True):
                # Show script emoji and original title if available
                script_emoji = get_script_emoji(text.get('script', 'latin'))
                display_title = text['title']
                if text.get('original_title'):
                    display_title = f"{text['title']} ({text['original_title']})"
                
                st.markdown(f"### {script_emoji} {display_title}")
                st.markdown(f"**{text['author']}**")
                lang_name = get_language_name(text.get('language', 'en'))
                tradition = f" • {text['tradition']}" if text.get('tradition') else ""
                st.caption(f"{text['period']}{tradition} • {lang_name}")
                
                if text.get("description"):
                    st.markdown(f"*{text['description'][:100]}...*" if len(text.get('description', '')) > 100 else f"*{text['description']}*")
                
                # Show available versions
                if text.get("files"):
                    versions = ", ".join(f["name"] for f in text["files"][:3])
                    st.markdown(f"📄 {len(text['files'])} version(s): {versions}")
                
                if st.button("📖 View Text", key=f"view_{text['id']}", use_container_width=True):
                    return text['id']
    
    return None


def render_text_detail(text: dict):
    """Render detailed view of a single text."""
    st.markdown(f"## {text['title']}")
    st.markdown(f"**{text['author']}** • {text['period']}")
    
    if text.get("description"):
        st.markdown(text["description"])
    
    st.markdown("---")
    
    # Version selector
    if text.get("files") and len(text["files"]) > 1:
        file_options = {f["name"]: f["path"] for f in text["files"]}
        selected_version = st.selectbox(
            "Select version",
            list(file_options.keys()),
            key="version_select"
        )
        text_path = file_options[selected_version]
    elif text.get("text_file"):
        text_path = text["text_file"]
        selected_version = Path(text_path).stem.replace("_", " ").title()
    else:
        st.warning("No text file available for this entry.")
        return
    
    # Load and display text preview
    try:
        with open(text_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        lines = content.split("\n")
        st.markdown(f"**{selected_version}** • {len(lines):,} lines • {len(content):,} characters")
        
        # Preview
        st.markdown("### Preview")
        preview_lines = min(50, len(lines))
        preview = "\n".join(lines[:preview_lines])
        st.text_area(
            "Text preview (first 50 lines)",
            preview,
            height=400,
            key="text_preview",
            label_visibility="collapsed"
        )
        
        if len(lines) > preview_lines:
            st.caption(f"Showing {preview_lines} of {len(lines):,} lines")
        
        # Actions
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "📥 Download Full Text",
                content,
                file_name=Path(text_path).name,
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            if st.button("🔬 Analyze with LingFrame", use_container_width=True):
                st.session_state.uploaded_text = content
                st.session_state.document_title = text["title"]
                st.session_state.analysis_state = "ANALYZING"
                st.switch_page("app/streamlit_app.py")
                
    except Exception as e:
        st.error(f"Error loading text: {e}")


def render_comparison(texts: list[dict]):
    """Render side-by-side text comparison."""
    st.markdown("## 🔀 Compare Texts")
    
    if len(texts) < 2:
        st.info("Need at least 2 texts in corpus for comparison.")
        return
    
    col1, col2 = st.columns(2)
    
    text_options = {f"{t['title']} ({t['author']})": t for t in texts}
    
    with col1:
        text1_key = st.selectbox("First Text", list(text_options.keys()), key="compare_text1")
        text1 = text_options[text1_key]
        
    with col2:
        remaining = [k for k in text_options.keys() if k != text1_key]
        text2_key = st.selectbox("Second Text", remaining, key="compare_text2")
        text2 = text_options[text2_key]
    
    st.markdown("---")
    
    # Load both texts
    col1, col2 = st.columns(2)
    
    for col, text in [(col1, text1), (col2, text2)]:
        with col:
            st.markdown(f"### {text['title']}")
            st.caption(f"{text['author']} • {text['period']}")
            
            if text.get("text_file"):
                try:
                    with open(text["text_file"], "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    lines = content.split("\n")
                    st.markdown(f"**{len(lines):,}** lines")
                    st.text_area(
                        "Preview",
                        "\n".join(lines[:30]),
                        height=300,
                        key=f"compare_preview_{text['id']}",
                        label_visibility="collapsed"
                    )
                except Exception as e:
                    st.error(f"Error loading: {e}")


def render_corpus_observatory():
    """Main entry point for the Corpus Observatory page."""
    texts = load_corpus_index()
    
    if not texts:
        st.warning("No corpus texts found. Check that the corpus/ directory exists.")
        st.markdown("""
        **Expected structure:**
        ```
        corpus/
        ├── classical/
        │   ├── odyssey/
        │   └── aeneid/
        ├── medieval/
        │   ├── beowulf/
        │   └── inferno/
        └── ...
        ```
        """)
        return
    
    # Initialize session state
    if "corpus_view" not in st.session_state:
        st.session_state.corpus_view = "browse"
    if "selected_text" not in st.session_state:
        st.session_state.selected_text = None
    
    # Navigation tabs
    tab1, tab2, tab3 = st.tabs(["📚 Browse", "📖 Read", "🔀 Compare"])
    
    with tab1:
        selected = render_corpus_browser(texts)
        if selected:
            st.session_state.selected_text = selected
            st.session_state.corpus_view = "detail"
            st.rerun()
    
    with tab2:
        if st.session_state.selected_text:
            text = next((t for t in texts if t["id"] == st.session_state.selected_text), None)
            if text:
                if st.button("← Back to Browse"):
                    st.session_state.selected_text = None
                    st.rerun()
                render_text_detail(text)
            else:
                st.info("Select a text from the Browse tab to read it here.")
        else:
            st.info("Select a text from the Browse tab to read it here.")
    
    with tab3:
        render_comparison(texts)
