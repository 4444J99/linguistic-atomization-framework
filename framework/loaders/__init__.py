"""
Loaders - Document format-specific text extraction modules.

Provides loaders for various document formats (PDF, DOCX, etc.) that extract
text with structure preservation for atomization.
"""

from .pdf_loader import PDFLoader

__all__ = ["PDFLoader"]
