"""
Language and Script Detection Module.

Provides automatic detection of:
- Language (using langdetect + heuristics)
- Writing script (Unicode block analysis)
- Text directionality (LTR/RTL)
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import Counter


class Script(Enum):
    """Unicode script categories."""
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    GREEK = "greek"
    ARABIC = "arabic"
    HEBREW = "hebrew"
    DEVANAGARI = "devanagari"
    TAMIL = "tamil"
    BENGALI = "bengali"
    THAI = "thai"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    KOREAN = "korean"
    UNKNOWN = "unknown"


class TextDirection(Enum):
    """Text directionality."""
    LTR = "ltr"
    RTL = "rtl"
    MIXED = "mixed"


SCRIPT_RANGES = {
    Script.LATIN: [(0x0041, 0x007A), (0x00C0, 0x00FF), (0x0100, 0x017F)],
    Script.CYRILLIC: [(0x0400, 0x04FF), (0x0500, 0x052F)],
    Script.GREEK: [(0x0370, 0x03FF), (0x1F00, 0x1FFF)],
    Script.ARABIC: [(0x0600, 0x06FF), (0x0750, 0x077F)],
    Script.HEBREW: [(0x0590, 0x05FF)],
    Script.DEVANAGARI: [(0x0900, 0x097F)],
    Script.TAMIL: [(0x0B80, 0x0BFF)],
    Script.BENGALI: [(0x0980, 0x09FF)],
    Script.THAI: [(0x0E00, 0x0E7F)],
    Script.CHINESE: [(0x4E00, 0x9FFF), (0x3400, 0x4DBF)],
    Script.JAPANESE: [(0x3040, 0x309F), (0x30A0, 0x30FF)],
    Script.KOREAN: [(0xAC00, 0xD7AF), (0x1100, 0x11FF)],
}

RTL_SCRIPTS = {Script.ARABIC, Script.HEBREW}


@dataclass
class LanguageInfo:
    """Information about detected language and script."""
    language: str
    language_name: str
    script: Script
    scripts: List[Script]
    direction: TextDirection
    confidence: float
    is_multilingual: bool
    original_text_sample: str

    def to_dict(self) -> Dict:
        return {
            "language": self.language,
            "language_name": self.language_name,
            "script": self.script.value,
            "scripts": [s.value for s in self.scripts],
            "direction": self.direction.value,
            "confidence": self.confidence,
            "is_multilingual": self.is_multilingual,
            "original_text_sample": self.original_text_sample,
        }


class LanguageDetector:
    """Detect language and script from text."""

    LANGUAGE_NAMES = {
        "en": "English", "de": "German", "fr": "French", "es": "Spanish",
        "it": "Italian", "pt": "Portuguese", "ru": "Russian", "el": "Greek",
        "la": "Latin", "grc": "Ancient Greek", "zh": "Chinese", "ja": "Japanese",
        "ko": "Korean", "ar": "Arabic", "fa": "Persian", "he": "Hebrew",
        "hi": "Hindi", "sa": "Sanskrit", "th": "Thai",
    }

    SCRIPT_LANGUAGES = {
        Script.ARABIC: ["ar", "fa"],
        Script.HEBREW: ["he"],
        Script.DEVANAGARI: ["hi", "sa"],
        Script.THAI: ["th"],
        Script.CHINESE: ["zh"],
        Script.JAPANESE: ["ja"],
        Script.KOREAN: ["ko"],
        Script.CYRILLIC: ["ru"],
        Script.GREEK: ["el", "grc"],
    }

    def __init__(self):
        self._langdetect = None
        self._langdetect_available = False
        try:
            import langdetect
            self._langdetect = langdetect
            self._langdetect_available = True
        except ImportError:
            pass

    def detect_script(self, char: str) -> Script:
        code_point = ord(char)
        for script, ranges in SCRIPT_RANGES.items():
            for start, end in ranges:
                if start <= code_point <= end:
                    return script
        return Script.UNKNOWN

    def analyze_scripts(self, text: str) -> Dict[Script, int]:
        script_counts: Dict[Script, int] = Counter()
        for char in text:
            if char.isalpha():
                script = self.detect_script(char)
                script_counts[script] += 1
        return dict(script_counts)

    def get_primary_script(self, text: str) -> Script:
        script_counts = self.analyze_scripts(text)
        if not script_counts:
            return Script.UNKNOWN
        known_scripts = {k: v for k, v in script_counts.items() if k != Script.UNKNOWN}
        if not known_scripts:
            return Script.UNKNOWN
        return max(known_scripts, key=known_scripts.get)

    def detect_direction(self, text: str) -> TextDirection:
        scripts = self.analyze_scripts(text)
        total_chars = sum(scripts.values())
        if total_chars == 0:
            return TextDirection.LTR
        rtl_chars = sum(scripts.get(s, 0) for s in RTL_SCRIPTS)
        rtl_ratio = rtl_chars / total_chars
        if rtl_ratio > 0.8:
            return TextDirection.RTL
        elif rtl_ratio > 0.2:
            return TextDirection.MIXED
        return TextDirection.LTR

    def detect_language(self, text: str) -> str:
        if not self._langdetect_available:
            primary_script = self.get_primary_script(text)
            if primary_script in self.SCRIPT_LANGUAGES:
                return self.SCRIPT_LANGUAGES[primary_script][0]
            return "en"
        try:
            from langdetect import detect_langs
            langs = detect_langs(text)
            if langs:
                return langs[0].lang
        except Exception:
            pass
        return "en"

    def detect_language_with_confidence(self, text: str) -> Tuple[str, float]:
        if not self._langdetect_available:
            primary_script = self.get_primary_script(text)
            if primary_script in self.SCRIPT_LANGUAGES:
                return self.SCRIPT_LANGUAGES[primary_script][0], 0.7
            return "en", 0.5
        try:
            from langdetect import detect_langs
            langs = detect_langs(text)
            if langs:
                return langs[0].lang, langs[0].prob
        except Exception:
            pass
        return "en", 0.5

    def detect(self, text: str) -> LanguageInfo:
        script_counts = self.analyze_scripts(text)
        scripts = sorted(script_counts.keys(), key=lambda s: script_counts.get(s, 0), reverse=True)
        scripts = [s for s in scripts if s != Script.UNKNOWN]
        if not scripts:
            scripts = [Script.UNKNOWN]
        primary_script = scripts[0]
        language, confidence = self.detect_language_with_confidence(text)
        if primary_script == Script.CHINESE and language not in ["zh"]:
            if Script.JAPANESE in scripts:
                language, confidence = "ja", 0.8
            else:
                language, confidence = "zh", 0.7
        language_name = self.LANGUAGE_NAMES.get(language, language.title())
        direction = self.detect_direction(text)
        is_multilingual = len(scripts) > 1 and scripts[0] != Script.UNKNOWN
        return LanguageInfo(
            language=language,
            language_name=language_name,
            script=primary_script,
            scripts=scripts,
            direction=direction,
            confidence=confidence,
            is_multilingual=is_multilingual,
            original_text_sample=text[:100] if text else "",
        )


_default_detector: Optional[LanguageDetector] = None


def detect_language(text: str) -> str:
    global _default_detector
    if _default_detector is None:
        _default_detector = LanguageDetector()
    return _default_detector.detect_language(text)


def detect_script(text: str) -> Script:
    global _default_detector
    if _default_detector is None:
        _default_detector = LanguageDetector()
    return _default_detector.get_primary_script(text)


def detect_all(text: str) -> LanguageInfo:
    global _default_detector
    if _default_detector is None:
        _default_detector = LanguageDetector()
    return _default_detector.detect(text)


def is_rtl(text: str) -> bool:
    global _default_detector
    if _default_detector is None:
        _default_detector = LanguageDetector()
    direction = _default_detector.detect_direction(text)
    return direction == TextDirection.RTL


def get_language_name(code: str) -> str:
    return LanguageDetector.LANGUAGE_NAMES.get(code, code.title())
