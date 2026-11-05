from __future__ import annotations

import re
import wave
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from nexus_babel.services.text_utils import sha256_file

TEXT_EXT = {".md", ".txt", ".yaml", ".yml"}
PDF_EXT = {".pdf"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp"}
AUDIO_EXT = {".wav", ".mp3", ".flac"}


def detect_modality(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXT:
        return "text"
    if ext in PDF_EXT:
        return "pdf"
    if ext in IMAGE_EXT:
        return "image"
    if ext in AUDIO_EXT:
        return "audio"
    return "binary"


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    chunks = []
    for page in reader.pages:
        chunks.append(page.extract_text() or "")
    return "\n".join(chunks)


def pdf_page_count(path: Path) -> int:
    reader = PdfReader(str(path))
    return len(reader.pages)


def extract_image_metadata(path: Path) -> dict[str, Any]:
    metadata = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "ocr_spans": [],
        "caption_candidate": path.stem.replace("-", " ").replace("_", " ").strip(),
        "embedding_ref": f"image:{sha256_file(path)[:16]}",
    }
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as img:
            metadata.update({"width": img.width, "height": img.height, "mode": img.mode})
    except Exception:
        metadata.update({"width": None, "height": None})
    return metadata


def extract_audio_metadata(path: Path) -> dict[str, Any]:
    metadata = {
        "filename": path.name,
        "size_bytes": path.stat().st_size,
        "transcription_segments": [],
        "prosody_summary": {},
    }
    if path.suffix.lower() == ".wav":
        with wave.open(str(path), "rb") as wav:
            frames = wav.getnframes()
            rate = wav.getframerate()
            duration = frames / float(rate) if rate else 0.0
            metadata.update(
                {
                    "sample_rate": rate,
                    "channels": wav.getnchannels(),
                    "duration_seconds": duration,
                    "transcription_segments": [
                        {
                            "start": 0.0,
                            "end": round(duration, 3),
                            "text": "",
                            "speaker": "speaker_0",
                        }
                    ],
                    "prosody_summary": {
                        "avg_intensity": None,
                        "tempo_hint": None,
                    },
                }
            )
    return metadata


def derive_text_segments(text: str, *, is_pdf: bool) -> dict[str, Any]:
    paragraphs = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    heading_candidates = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if len(stripped) <= 80 and (stripped.isupper() or stripped == stripped.title()):
            heading_candidates.append(stripped)
    citation_markers = []
    citation_markers.extend(re.findall(r"\[[0-9]{1,3}\]", text))
    citation_markers.extend(re.findall(r"\([A-Z][A-Za-z]+,\s*[0-9]{4}\)", text))
    paragraph_blocks = [
        {"index": idx + 1, "char_count": len(block), "preview": block[:160]}
        for idx, block in enumerate(paragraphs[:200])
    ]
    return {
        "paragraph_blocks": paragraph_blocks,
        "heading_candidates": heading_candidates[:100],
        "citation_markers": citation_markers[:100],
        "pdf_like_layout": bool(is_pdf),
    }


def derive_modality_status(modality: str, projection_warning: str | None, segments: dict[str, Any]) -> str:
    if projection_warning:
        return "partial"
    if modality in {"text", "pdf"}:
        return "complete" if int(segments.get("char_count", 0)) > 0 else "partial"
    if modality == "image":
        return "complete" if segments.get("width") and segments.get("height") else "partial"
    if modality == "audio":
        return "complete" if float(segments.get("duration_seconds", 0.0)) > 0 else "partial"
    return "pending"
