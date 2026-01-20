"""
Upload Component - Document upload interface with drag-and-drop.
"""

import streamlit as st
from pathlib import Path

from .analysis_engine import AnalysisState


def extract_text_from_upload(uploaded_file) -> str:
    """Extract text from an uploaded file."""
    file_type = uploaded_file.name.split(".")[-1].lower()

    if file_type == "txt" or file_type == "md":
        return uploaded_file.read().decode("utf-8")

    elif file_type == "pdf":
        try:
            from framework.loaders import PDFLoader
            import tempfile

            # Save to temp file for PDF loader
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = Path(tmp.name)

            loader = PDFLoader()
            text = loader.extract_text(tmp_path)

            # Clean up
            tmp_path.unlink()
            return text

        except ImportError:
            st.error("PDF support requires pdfplumber. Install with: pip install pdfplumber")
            return ""

    elif file_type == "docx":
        try:
            import docx
            import io

            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())

        except ImportError:
            st.error("DOCX support requires python-docx. Install with: pip install python-docx")
            return ""

    else:
        # Try as plain text
        try:
            return uploaded_file.read().decode("utf-8")
        except Exception:
            st.error(f"Unable to read file format: .{file_type}")
            return ""


def render_upload_section():
    """Render the document upload interface."""
    # Centered container
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("""
        <div class="upload-container">
            <div class="upload-icon">📄</div>
            <div class="upload-text">Drop your document here</div>
            <div class="upload-hint">PDF, TXT, MD, or DOCX</div>
        </div>
        """, unsafe_allow_html=True)

        # File uploader
        uploaded_file = st.file_uploader(
            "Upload document",
            type=["pdf", "txt", "md", "docx"],
            help="Supported formats: PDF, TXT, Markdown, DOCX",
            label_visibility="collapsed",
        )

        if uploaded_file is not None:
            # Extract document title from filename
            doc_title = uploaded_file.name.rsplit(".", 1)[0]
            doc_title = doc_title.replace("-", " ").replace("_", " ").title()

            # Allow title override
            with st.expander("📝 Document Options", expanded=False):
                doc_title = st.text_input(
                    "Document Title",
                    value=doc_title,
                    help="This will appear in your report"
                )

            # Extract text
            with st.spinner("Reading document..."):
                text = extract_text_from_upload(uploaded_file)

            if text:
                word_count = len(text.split())
                st.success(f"✓ Loaded **{uploaded_file.name}** ({word_count:,} words)")

                # Analyze button
                if st.button("🔍 Analyze My Writing", use_container_width=True, type="primary"):
                    st.session_state.uploaded_text = text
                    st.session_state.document_title = doc_title
                    st.session_state.analysis_state = AnalysisState.ANALYZING
                    st.rerun()
            else:
                st.error("Could not extract text from document. Please try another file.")

        # Or paste text directly
        st.markdown("---")
        st.markdown("<p style='text-align: center; color: #6c757d;'>Or paste your text directly</p>",
                    unsafe_allow_html=True)

        with st.expander("📋 Paste Text", expanded=False):
            pasted_text = st.text_area(
                "Paste your writing here",
                height=200,
                placeholder="Paste your essay, article, or any text you want analyzed...",
                label_visibility="collapsed",
            )

            if pasted_text:
                doc_title = st.text_input(
                    "Give your document a title",
                    value="My Document",
                    key="paste_title"
                )

                word_count = len(pasted_text.split())
                st.info(f"{word_count:,} words")

                if st.button("🔍 Analyze This Text", use_container_width=True):
                    st.session_state.uploaded_text = pasted_text
                    st.session_state.document_title = doc_title
                    st.session_state.analysis_state = AnalysisState.ANALYZING
                    st.rerun()

    # Help section
    st.markdown("---")
    with st.expander("❓ What will I learn about my writing?"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            **Understanding Your Writing**
            - How effectively you use logic and evidence
            - Your emotional impact on readers
            - How you establish credibility

            **Finding Vulnerabilities**
            - Blind spots you might not see
            - Where critics could attack
            """)
        with col2:
            st.markdown("""
            **Discovering Opportunities**
            - Emerging patterns worth developing
            - Quick wins for immediate improvement
            - Structural changes for bigger impact

            **Actionable Recommendations**
            - Specific suggestions, not vague advice
            - Prioritized by impact
            """)
