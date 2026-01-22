"""
Multi-Language Tokenizer Factory - Handles word segmentation across scripts.

Provides tokenizers for various writing systems:
- Latin/Cyrillic/Greek: Whitespace-based with regex
- Chinese: jieba (NLP) or character-level
- Japanese: fugashi/MeCab (NLP) or character-level
- Korean: konlpy (NLP) or character-level
- Arabic: camel-tools or whitespace
- Thai: pythainlp or character-level
- Indic scripts: indic-nlp-library or whitespace

CJK Strategy Options:
- "nlp": Use language-specific NLP segmentation (jieba, fugashi, etc.)
- "character": Character-by-character tokenization
- "hybrid": NLP for content words, character for analysis
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class Script(Enum):
    """Unicode script categories."""
    LATIN = "latin"
    CYRILLIC = "cyrillic"
    GREEK = "greek"
    ARABIC = "arabic"
    HEBREW = "hebrew"
    DEVANAGARI = "devanagari"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    KOREAN = "korean"
    THAI = "thai"
    UNKNOWN = "unknown"


class CJKStrategy(Enum):
    """CJK tokenization strategy."""
    NLP = "nlp"              # Use NLP-based segmentation
    CHARACTER = "character"   # Character-by-character
    HYBRID = "hybrid"         # NLP with character fallback


@dataclass
class TokenizerConfig:
    """Configuration for the tokenizer factory."""
    cjk_strategy: CJKStrategy = CJKStrategy.NLP
    preserve_punctuation: bool = True
    lowercase: bool = False
    strip_whitespace: bool = True
    chinese_dict: Optional[str] = None
    japanese_dict: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> TokenizerConfig:
        """Create config from dictionary."""
        config = cls()
        if "cjk_strategy" in data:
            config.cjk_strategy = CJKStrategy(data["cjk_strategy"])
        if "preserve_punctuation" in data:
            config.preserve_punctuation = data["preserve_punctuation"]
        if "lowercase" in data:
            config.lowercase = data["lowercase"]
        if "strip_whitespace" in data:
            config.strip_whitespace = data["strip_whitespace"]
        if "chinese_dict" in data:
            config.chinese_dict = data["chinese_dict"]
        if "japanese_dict" in data:
            config.japanese_dict = data["japanese_dict"]
        return config


class BaseTokenizer(ABC):
    """Abstract base class for language tokenizers."""

    language: str = "unknown"
    script: Script = Script.UNKNOWN

    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()

    @abstractmethod
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words/tokens."""
        pass

    def tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]


class WhitespaceTokenizer(BaseTokenizer):
    """Simple whitespace-based tokenizer for Latin/Cyrillic/Greek scripts."""

    language = "generic"
    script = Script.LATIN

    def tokenize(self, text: str) -> List[str]:
        """Tokenize on whitespace boundaries."""
        if self.config.strip_whitespace:
            text = text.strip()
        tokens = text.split()
        if not self.config.preserve_punctuation:
            tokens = [re.sub(r'[^\w\s]', '', t) for t in tokens]
            tokens = [t for t in tokens if t]
        if self.config.lowercase:
            tokens = [t.lower() for t in tokens]
        return tokens


class ChineseTokenizer(BaseTokenizer):
    """Chinese tokenizer using jieba or character-level."""

    language = "chinese"
    script = Script.CHINESE

    def __init__(self, config: Optional[TokenizerConfig] = None):
        super().__init__(config)
        self._jieba = None
        self._jieba_available = False

        if self.config.cjk_strategy != CJKStrategy.CHARACTER:
            try:
                import jieba
                self._jieba = jieba
                self._jieba_available = True
                if self.config.chinese_dict:
                    jieba.load_userdict(self.config.chinese_dict)
            except ImportError:
                self._jieba_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Chinese text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self.config.cjk_strategy == CJKStrategy.CHARACTER:
            return self._tokenize_characters(text)
        if self._jieba_available:
            return self._tokenize_jieba(text)
        return self._tokenize_characters(text)

    def _tokenize_jieba(self, text: str) -> List[str]:
        """Use jieba for word segmentation."""
        tokens = list(self._jieba.cut(text, cut_all=False))
        if not self.config.preserve_punctuation:
            tokens = [t for t in tokens if not self._is_punctuation(t)]
        return [t for t in tokens if t.strip()]

    def _tokenize_characters(self, text: str) -> List[str]:
        """Character-by-character tokenization."""
        tokens = []
        for char in text:
            if char.strip():
                if self.config.preserve_punctuation or not self._is_punctuation(char):
                    tokens.append(char)
        return tokens

    @staticmethod
    def _is_punctuation(char: str) -> bool:
        """Check if character is Chinese or common punctuation."""
        punct = set(',.!?;:\'"()[]{}')
        return char in punct or char.isspace()


class JapaneseTokenizer(BaseTokenizer):
    """Japanese tokenizer using fugashi/MeCab or character-level."""

    language = "japanese"
    script = Script.JAPANESE

    def __init__(self, config: Optional[TokenizerConfig] = None):
        super().__init__(config)
        self._tagger = None
        self._mecab_available = False
        self._use_fugashi = False

        if self.config.cjk_strategy != CJKStrategy.CHARACTER:
            try:
                import fugashi
                self._tagger = fugashi.Tagger()
                self._mecab_available = True
                self._use_fugashi = True
            except ImportError:
                try:
                    from sudachipy import dictionary
                    self._dict = dictionary.Dictionary()
                    self._tagger = self._dict.create()
                    self._mecab_available = True
                except ImportError:
                    self._mecab_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Japanese text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self.config.cjk_strategy == CJKStrategy.CHARACTER:
            return self._tokenize_characters(text)
        if self._mecab_available:
            return self._tokenize_mecab(text)
        return self._tokenize_characters(text)

    def _tokenize_mecab(self, text: str) -> List[str]:
        """Use MeCab/fugashi for word segmentation."""
        if self._use_fugashi:
            tokens = [word.surface for word in self._tagger(text)]
        else:
            from sudachipy import tokenizer as sudachi_tokenizer
            tokens = [m.surface() for m in self._tagger.tokenize(text, sudachi_tokenizer.Tokenizer.SplitMode.C)]
        if not self.config.preserve_punctuation:
            tokens = [t for t in tokens if not self._is_punctuation(t)]
        return [t for t in tokens if t.strip()]

    def _tokenize_characters(self, text: str) -> List[str]:
        """Character-by-character tokenization."""
        return [c for c in text if c.strip() and (self.config.preserve_punctuation or not self._is_punctuation(c))]

    @staticmethod
    def _is_punctuation(char: str) -> bool:
        """Check if character is Japanese or common punctuation."""
        punct = set(',.!?;:\'"()[]{}')
        return char in punct or char.isspace()


class KoreanTokenizer(BaseTokenizer):
    """Korean tokenizer using konlpy or whitespace."""

    language = "korean"
    script = Script.KOREAN

    def __init__(self, config: Optional[TokenizerConfig] = None):
        super().__init__(config)
        self._tagger = None
        self._konlpy_available = False

        if self.config.cjk_strategy != CJKStrategy.CHARACTER:
            try:
                from konlpy.tag import Okt
                self._tagger = Okt()
                self._konlpy_available = True
            except ImportError:
                self._konlpy_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Korean text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self.config.cjk_strategy == CJKStrategy.CHARACTER:
            return [c for c in text if c.strip()]
        if self._konlpy_available:
            tokens = self._tagger.morphs(text)
            if not self.config.preserve_punctuation:
                tokens = [t for t in tokens if t not in ',.!?;:\'"()[]{}']
            return [t for t in tokens if t.strip()]
        return text.split()


class ArabicTokenizer(BaseTokenizer):
    """Arabic tokenizer using camel-tools or whitespace."""

    language = "arabic"
    script = Script.ARABIC

    def __init__(self, config: Optional[TokenizerConfig] = None):
        super().__init__(config)
        self._tokenizer = None
        self._camel_available = False

        try:
            from camel_tools.tokenizers.word import simple_word_tokenize
            self._tokenizer = simple_word_tokenize
            self._camel_available = True
        except ImportError:
            self._camel_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Arabic text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self._camel_available:
            tokens = self._tokenizer(text)
        else:
            tokens = text.split()
        if not self.config.preserve_punctuation:
            punct = set(',.!?;:\'"()[]{}')
            tokens = [t for t in tokens if t not in punct]
        return [t for t in tokens if t.strip()]


class ThaiTokenizer(BaseTokenizer):
    """Thai tokenizer using pythainlp or character-level."""

    language = "thai"
    script = Script.THAI

    def __init__(self, config: Optional[TokenizerConfig] = None):
        super().__init__(config)
        self._tokenize_func = None
        self._pythainlp_available = False

        try:
            from pythainlp.tokenize import word_tokenize
            self._tokenize_func = word_tokenize
            self._pythainlp_available = True
        except ImportError:
            self._pythainlp_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Thai text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self._pythainlp_available:
            tokens = self._tokenize_func(text)
        else:
            tokens = [c for c in text if c.strip()]
        if not self.config.preserve_punctuation:
            tokens = [t for t in tokens if t not in ',.!?()[]{}"\'-']
        return tokens


class IndicTokenizer(BaseTokenizer):
    """Tokenizer for Indic scripts (Devanagari, Tamil, etc.)."""

    language = "hindi"
    script = Script.DEVANAGARI

    def __init__(self, config: Optional[TokenizerConfig] = None, language: str = "hindi"):
        super().__init__(config)
        self.language = language
        self._tokenizer = None
        self._indic_available = False

        try:
            from indicnlp.tokenize import indic_tokenize
            self._tokenizer = indic_tokenize
            self._indic_available = True
        except ImportError:
            self._indic_available = False

    def tokenize(self, text: str) -> List[str]:
        """Tokenize Indic script text."""
        if self.config.strip_whitespace:
            text = text.strip()
        if self._indic_available:
            tokens = self._tokenizer.trivial_tokenize(text, self.language)
        else:
            tokens = text.split()
        if not self.config.preserve_punctuation:
            punct = set(',.!?;:\'"()[]{}')
            tokens = [t for t in tokens if t not in punct]
        return [t for t in tokens if t.strip()]


class SentenceTokenizer:
    """Language-aware sentence tokenizer using pysbd."""

    def __init__(self, language: str = "en"):
        self.language = language
        self._segmenter = None
        self._pysbd_available = False

        try:
            import pysbd
            self._segmenter = pysbd.Segmenter(language=language, clean=False)
            self._pysbd_available = True
        except (ImportError, ValueError):
            self._pysbd_available = False

    def tokenize(self, text: str) -> List[str]:
        """Split text into sentences."""
        if self._pysbd_available:
            return self._segmenter.segment(text)
        pattern = r'(?<=[.!?])\s+'
        sentences = re.split(pattern, text)
        return [s.strip() for s in sentences if s.strip()]


class TokenizerFactory:
    """Factory for creating language-appropriate tokenizers."""

    TOKENIZERS = {
        "zh": ChineseTokenizer, "chinese": ChineseTokenizer,
        "zh-cn": ChineseTokenizer, "zh-tw": ChineseTokenizer, "cmn": ChineseTokenizer,
        "ja": JapaneseTokenizer, "japanese": JapaneseTokenizer, "jpn": JapaneseTokenizer,
        "ko": KoreanTokenizer, "korean": KoreanTokenizer, "kor": KoreanTokenizer,
        "ar": ArabicTokenizer, "arabic": ArabicTokenizer, "ara": ArabicTokenizer,
        "th": ThaiTokenizer, "thai": ThaiTokenizer, "tha": ThaiTokenizer,
        "hi": IndicTokenizer, "hindi": IndicTokenizer, "hin": IndicTokenizer,
        "sa": IndicTokenizer, "sanskrit": IndicTokenizer,
        "en": WhitespaceTokenizer, "english": WhitespaceTokenizer,
        "de": WhitespaceTokenizer, "german": WhitespaceTokenizer,
        "fr": WhitespaceTokenizer, "french": WhitespaceTokenizer,
        "es": WhitespaceTokenizer, "spanish": WhitespaceTokenizer,
        "it": WhitespaceTokenizer, "italian": WhitespaceTokenizer,
        "pt": WhitespaceTokenizer, "portuguese": WhitespaceTokenizer,
        "ru": WhitespaceTokenizer, "russian": WhitespaceTokenizer,
        "el": WhitespaceTokenizer, "greek": WhitespaceTokenizer,
        "la": WhitespaceTokenizer, "latin": WhitespaceTokenizer,
        "he": WhitespaceTokenizer, "hebrew": WhitespaceTokenizer,
        "fa": ArabicTokenizer, "persian": ArabicTokenizer,
    }

    def __init__(self, config: Optional[TokenizerConfig] = None):
        self.config = config or TokenizerConfig()
        self._cache: Dict[str, BaseTokenizer] = {}

    def get_tokenizer(self, language: str, config: Optional[TokenizerConfig] = None) -> BaseTokenizer:
        """Get tokenizer for the specified language."""
        lang_lower = language.lower()
        cfg = config or self.config

        cache_key = f"{lang_lower}_{id(cfg)}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        tokenizer_class = self.TOKENIZERS.get(lang_lower, WhitespaceTokenizer)

        if tokenizer_class == IndicTokenizer:
            tokenizer = tokenizer_class(cfg, language=lang_lower)
        else:
            tokenizer = tokenizer_class(cfg)

        self._cache[cache_key] = tokenizer
        return tokenizer

    def get_sentence_tokenizer(self, language: str) -> SentenceTokenizer:
        """Get sentence tokenizer for the specified language."""
        pysbd_map = {
            "en": "en", "english": "en", "de": "de", "german": "de",
            "fr": "fr", "french": "fr", "es": "es", "spanish": "es",
            "it": "it", "italian": "it", "pt": "pt", "portuguese": "pt",
            "ru": "ru", "russian": "ru", "zh": "zh", "chinese": "zh",
            "ja": "ja", "japanese": "ja", "ar": "ar", "arabic": "ar",
        }
        lang_code = pysbd_map.get(language.lower(), "en")
        return SentenceTokenizer(language=lang_code)

    @classmethod
    def supported_languages(cls) -> List[str]:
        """Get list of supported language codes."""
        return list(set(cls.TOKENIZERS.keys()))


_default_factory: Optional[TokenizerFactory] = None


def get_tokenizer(language: str, config: Optional[TokenizerConfig] = None) -> BaseTokenizer:
    """Get a tokenizer for the specified language."""
    global _default_factory
    if _default_factory is None:
        _default_factory = TokenizerFactory()
    return _default_factory.get_tokenizer(language, config)


def tokenize(text: str, language: str = "en") -> List[str]:
    """Tokenize text using language-appropriate tokenizer."""
    tokenizer = get_tokenizer(language)
    return tokenizer.tokenize(text)


def tokenize_sentences(text: str, language: str = "en") -> List[str]:
    """Split text into sentences."""
    global _default_factory
    if _default_factory is None:
        _default_factory = TokenizerFactory()
    sent_tokenizer = _default_factory.get_sentence_tokenizer(language)
    return sent_tokenizer.tokenize(text)
