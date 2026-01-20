"""
PDF Loader - Extract text from PDF documents with structure preservation.

Uses pdfplumber for text extraction and PyMuPDF (fitz) for font metadata
to detect section headings based on font size.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class PDFLoader:
    """
    Load and extract text from PDF documents with structure detection.

    Detects section headings via font size heuristics and inserts markdown
    headers (##) so the atomizer treats sections as themes.
    """

    def __init__(
        self,
        min_heading_font_size: float = 14.0,
        heading_patterns: Optional[List[str]] = None,
        skip_front_matter_pages: int = 1,
    ):
        """
        Initialize PDF loader.

        Args:
            min_heading_font_size: Minimum font size to consider as heading.
            heading_patterns: Regex patterns for explicit heading detection.
            skip_front_matter_pages: Number of pages to skip for front matter (title, author info).
        """
        self.min_heading_font_size = min_heading_font_size
        self.heading_patterns = heading_patterns or [
            r"^Chapter\s+\d+",
            r"^CHAPTER\s+\d+",
            r"^Part\s+\w+",
            r"^PART\s+\w+",
            r"^\d+\.\s+[A-Z]",
        ]
        self.skip_front_matter_pages = skip_front_matter_pages
        self._pdfplumber = None
        self._fitz = None

    def _ensure_imports(self):
        """Lazy import PDF libraries."""
        if self._pdfplumber is None:
            try:
                import pdfplumber
                self._pdfplumber = pdfplumber
            except ImportError:
                raise ImportError(
                    "pdfplumber is required for PDF extraction. "
                    "Install with: pip install pdfplumber"
                )

        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                # fitz is optional - used for font metadata
                self._fitz = False

    def _is_heading_by_pattern(self, text: str) -> bool:
        """Check if text matches a heading pattern."""
        text = text.strip()
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return True
        return False

    def _is_heading_by_heuristics(
        self,
        text: str,
        font_size: Optional[float] = None,
        is_bold: bool = False,
    ) -> bool:
        """
        Detect if a line is likely a section heading using heuristics.

        Args:
            text: Line text
            font_size: Font size (if available from PyMuPDF)
            is_bold: Whether text is bold

        Returns:
            True if likely a heading
        """
        text = text.strip()
        if not text:
            return False

        # Reject obvious non-headings
        # Phone numbers
        if re.match(r"^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}$", text):
            return False
        # Email addresses
        if "@" in text and "." in text:
            return False
        # URLs
        if text.startswith(("http://", "https://", "www.")):
            return False
        # Single word that's just a number with many digits (not a chapter number)
        if re.match(r"^\d{5,}$", text):
            return False
        # Lines that look like addresses (contain "St", "Ave", "Apt", etc.)
        if re.search(r"\b(St|Ave|Blvd|Rd|Dr|Apt|Suite|Floor)\b", text, re.IGNORECASE):
            return False

        # Pattern match takes precedence
        if self._is_heading_by_pattern(text):
            return True

        # Font size heuristic (if available)
        if font_size and font_size >= self.min_heading_font_size:
            # Large font + short line = likely heading
            if len(text) < 60:
                return True

        # Heuristics for title-style headings (like "Calls of Duty", "Stateside")
        # Short line that's title-cased and not ending with punctuation that
        # suggests continuation
        if len(text) < 50:
            # Not ending with continuation punctuation
            if not text.rstrip().endswith((",", ";", "-", ":")):
                # Either all caps, title case, or bold
                words = text.split()
                if len(words) <= 5:
                    # Check for title case or all caps
                    is_title_case = all(
                        w[0].isupper() or not w[0].isalpha() for w in words if w
                    )
                    is_all_caps = text.isupper() and len(text) > 2
                    if is_title_case or is_all_caps or is_bold:
                        # Additional check: not a sentence fragment
                        if not any(text.endswith(p) for p in [".", "!", "?"]):
                            return True

        return False

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF with section markers.

        Detects section headings and inserts markdown ## headers so the
        atomizer treats sections as themes.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Extracted text with markdown section headers
        """
        self._ensure_imports()
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        # Try to use PyMuPDF for font metadata
        font_info = self._extract_font_info(pdf_path) if self._fitz else {}

        sections = []
        current_section_title = None
        current_section_text = []

        with self._pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                # Skip front matter pages (title, author info)
                if page_num <= self.skip_front_matter_pages:
                    continue

                page_text = page.extract_text() or ""

                for line in page_text.split("\n"):
                    line = line.strip()
                    if not line:
                        # Preserve paragraph breaks
                        if current_section_text and current_section_text[-1] != "":
                            current_section_text.append("")
                        continue

                    # Get font info for this line if available
                    line_font_size = font_info.get((page_num, line), {}).get("size")
                    line_is_bold = font_info.get((page_num, line), {}).get("bold", False)

                    # Check if this line is a heading
                    if self._is_heading_by_heuristics(line, line_font_size, line_is_bold):
                        # Save previous section
                        if current_section_title and current_section_text:
                            sections.append((current_section_title, current_section_text))

                        # Start new section
                        current_section_title = line
                        current_section_text = []
                    else:
                        current_section_text.append(line)

        # Save final section
        if current_section_title and current_section_text:
            sections.append((current_section_title, current_section_text))
        elif current_section_text:
            # No sections detected - treat entire document as one section
            sections.append(("Document", current_section_text))

        # Build output with markdown headers
        output_parts = []
        for title, lines in sections:
            # Clean up section text
            text = "\n".join(lines).strip()
            text = re.sub(r"\n{3,}", "\n\n", text)  # Normalize multiple newlines

            if text:  # Only include sections with content
                output_parts.append(f"## {title}\n\n{text}")

        return "\n\n".join(output_parts)

    def _extract_font_info(self, pdf_path: Path) -> Dict[Tuple[int, str], Dict]:
        """
        Extract font metadata using PyMuPDF.

        Args:
            pdf_path: Path to PDF

        Returns:
            Dict mapping (page_num, text) to font info
        """
        if not self._fitz:
            return {}

        font_info = {}
        try:
            doc = self._fitz.open(pdf_path)
            for page_num, page in enumerate(doc, start=1):
                blocks = page.get_text("dict")["blocks"]
                for block in blocks:
                    if "lines" not in block:
                        continue
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            if text:
                                font_info[(page_num, text)] = {
                                    "size": span["size"],
                                    "bold": "bold" in span["font"].lower(),
                                }
            doc.close()
        except Exception:
            # Font extraction failed, continue without it
            pass

        return font_info

    def extract_with_structure(self, pdf_path: Path) -> Dict:
        """
        Extract text preserving detailed chapter structure.

        Returns structured data instead of flat markdown text.

        Args:
            pdf_path: Path to PDF file

        Returns:
            Dict with 'metadata' and 'sections' keys
        """
        self._ensure_imports()
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        font_info = self._extract_font_info(pdf_path) if self._fitz else {}

        sections = []
        current_section = {"title": None, "paragraphs": [], "page_start": 1}
        current_paragraph = []

        with self._pdfplumber.open(pdf_path) as pdf:
            metadata = {
                "page_count": len(pdf.pages),
                "source": str(pdf_path),
            }

            for page_num, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text() or ""

                for line in page_text.split("\n"):
                    line = line.strip()

                    if not line:
                        # End of paragraph
                        if current_paragraph:
                            current_section["paragraphs"].append(
                                " ".join(current_paragraph)
                            )
                            current_paragraph = []
                        continue

                    line_font_size = font_info.get((page_num, line), {}).get("size")
                    line_is_bold = font_info.get((page_num, line), {}).get("bold", False)

                    if self._is_heading_by_heuristics(line, line_font_size, line_is_bold):
                        # Save current paragraph
                        if current_paragraph:
                            current_section["paragraphs"].append(
                                " ".join(current_paragraph)
                            )
                            current_paragraph = []

                        # Save current section
                        if current_section["title"] and current_section["paragraphs"]:
                            sections.append(current_section)

                        # Start new section
                        current_section = {
                            "title": line,
                            "paragraphs": [],
                            "page_start": page_num,
                        }
                    else:
                        current_paragraph.append(line)

            # Save final paragraph and section
            if current_paragraph:
                current_section["paragraphs"].append(" ".join(current_paragraph))
            if current_section["title"] and current_section["paragraphs"]:
                sections.append(current_section)
            elif current_section["paragraphs"]:
                current_section["title"] = "Document"
                sections.append(current_section)

        return {
            "metadata": metadata,
            "sections": sections,
        }
