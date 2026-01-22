"""
Ontological Naming System - Semantically meaningful identifiers for atoms.

Provides multiple naming strategies for atom IDs:
- hierarchical: Parent-child paths (T001.P001.S001)
- semantic: Content-derived slugs (military-town.para-1)
- uuid: Globally unique identifiers
- hybrid: Counter + semantic hint (T001:military-town.P001.S001)
- legacy: Original flat counter format (T001, P0001, S00001)

Also handles output file naming with semantic descriptors.

Unicode Support:
- Uses unidecode for transliterating non-Latin scripts to ASCII slugs
- Examples: "道德經" -> "dao-de-jing", "Война и мир" -> "voina-i-mir"
- Preserves original text in atom metadata while creating ASCII-safe IDs
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

# Optional unidecode for better transliteration
try:
    from unidecode import unidecode as _unidecode
    UNIDECODE_AVAILABLE = True
except ImportError:
    _unidecode = None
    UNIDECODE_AVAILABLE = False


def transliterate_to_ascii(text: str) -> str:
    """
    Transliterate text to ASCII representation.

    Uses unidecode for proper transliteration of non-Latin scripts.
    Falls back to NFKD normalization + ASCII encoding if unidecode unavailable.

    Args:
        text: Unicode text to transliterate

    Returns:
        ASCII representation of the text
    """
    if not text:
        return ""

    if UNIDECODE_AVAILABLE:
        # Use unidecode for proper transliteration
        # e.g., "道德經" -> "Dao De Jing", "Война" -> "Voina"
        return _unidecode(text)
    else:
        # Fallback: NFKD normalization + ASCII encoding
        # This drops characters that can't be decomposed
        normalized = unicodedata.normalize("NFKD", text)
        return normalized.encode("ascii", "ignore").decode("ascii")


class NamingStrategy(Enum):
    """Available atom ID naming strategies."""
    HIERARCHICAL = "hierarchical"   # T001.P001.S001.W001
    SEMANTIC = "semantic"           # military-town.para-1.sent-about-deployment
    UUID = "uuid"                   # abc12345-6789-...
    HYBRID = "hybrid"               # T001:military-town.P001.S001
    LEGACY = "legacy"               # T001, P0001, S00001 (original flat format)


@dataclass
class NamingConfig:
    """Configuration for the naming system."""
    strategy: NamingStrategy = NamingStrategy.HYBRID

    # Format strings for each level (used by hierarchical/hybrid)
    # Placeholders: {counter}, {slug}, {parent}, {level_prefix}
    formats: Dict[str, str] = field(default_factory=lambda: {
        "theme": "{level_prefix}{counter:03d}:{slug}",
        "paragraph": "{parent}.P{counter:03d}",
        "sentence": "{parent}.S{counter:03d}",
        "word": "{parent}.W{counter:03d}",
        "letter": None,  # Skip letters by default (too verbose)
    })

    # Level prefixes for ID generation
    level_prefixes: Dict[str, str] = field(default_factory=lambda: {
        "theme": "T",
        "paragraph": "P",
        "sentence": "S",
        "word": "W",
        "letter": "L",
    })

    # Legacy format strings (for backward compatibility)
    legacy_formats: Dict[str, str] = field(default_factory=lambda: {
        "theme": "T{counter:03d}",
        "paragraph": "P{counter:04d}",
        "sentence": "S{counter:05d}",
        "word": "W{counter:06d}",
        "letter": "L{counter:08d}",
    })

    # Maximum slug length for semantic naming
    max_slug_length: int = 30

    # Whether to include letter-level atoms
    include_letters: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> NamingConfig:
        """Create config from dictionary (e.g., from YAML)."""
        strategy_str = data.get("strategy", "hybrid")
        try:
            strategy = NamingStrategy(strategy_str)
        except ValueError:
            strategy = NamingStrategy.HYBRID

        config = cls(strategy=strategy)

        if "formats" in data:
            config.formats.update(data["formats"])
        if "level_prefixes" in data:
            config.level_prefixes.update(data["level_prefixes"])
        if "max_slug_length" in data:
            config.max_slug_length = data["max_slug_length"]
        if "include_letters" in data:
            config.include_letters = data["include_letters"]

        return config


class OntologicalNaming:
    """
    Generate semantically meaningful atom IDs.

    Supports multiple naming strategies that can be configured per-project.
    The naming system maintains state for counter-based strategies and
    provides utilities for slug generation and format string expansion.
    """

    def __init__(self, config: Optional[NamingConfig] = None):
        """
        Initialize naming system.

        Args:
            config: Naming configuration (defaults to hybrid strategy)
        """
        self.config = config or NamingConfig()
        self._counters: Dict[str, int] = {}
        self._reset_counters()

    def _reset_counters(self):
        """Reset all level counters to 1."""
        levels = ["theme", "paragraph", "sentence", "word", "letter"]
        self._counters = {level: 1 for level in levels}

    @staticmethod
    def slug_from_text(text: str, max_len: int = 30, preserve_original: bool = False) -> str:
        """
        Create URL-safe semantic slug from text.

        Handles all Unicode scripts including CJK, Arabic, Cyrillic, etc.
        Uses unidecode for proper transliteration when available.

        Args:
            text: Source text to slugify
            max_len: Maximum slug length
            preserve_original: If True, returns tuple of (slug, original_text)

        Returns:
            Lowercase hyphenated slug (e.g., "military-town", "dao-de-jing")
        """
        if not text:
            return "unknown"

        # Store original for metadata if needed
        original = text

        # Transliterate to ASCII using unidecode or fallback
        text = transliterate_to_ascii(text)

        # Convert to lowercase
        text = text.lower()

        # Replace spaces and special chars with hyphens
        text = re.sub(r"[^\w\s-]", "", text)
        text = re.sub(r"[\s_]+", "-", text)
        text = re.sub(r"-+", "-", text)

        # Strip leading/trailing hyphens
        text = text.strip("-")

        # Truncate to max length, preserving word boundaries
        if len(text) > max_len:
            truncated = text[:max_len]
            # Try to cut at a word boundary
            last_hyphen = truncated.rfind("-")
            if last_hyphen > max_len // 2:
                truncated = truncated[:last_hyphen]
            text = truncated.rstrip("-")

        return text or "unknown"

    def generate_id(
        self,
        level: str,
        counter: Optional[int] = None,
        parent_id: Optional[str] = None,
        semantic_hint: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """
        Generate ID based on configured strategy.

        Args:
            level: Atom level (theme, paragraph, sentence, word, letter)
            counter: Explicit counter value (auto-incremented if None)
            parent_id: Parent atom's ID (for hierarchical strategies)
            semantic_hint: Semantic descriptor (e.g., theme title)
            text: Atom text content (used to derive semantic slug if hint not provided)

        Returns:
            Generated atom ID string
        """
        # Get or increment counter
        if counter is None:
            counter = self._counters.get(level, 1)
            self._counters[level] = counter + 1

        strategy = self.config.strategy

        # Check if this level should be skipped
        fmt = self.config.formats.get(level)
        if fmt is None and strategy != NamingStrategy.LEGACY:
            # Level disabled in config
            return ""

        if strategy == NamingStrategy.LEGACY:
            return self._generate_legacy(level, counter)
        elif strategy == NamingStrategy.UUID:
            return self._generate_uuid(level)
        elif strategy == NamingStrategy.SEMANTIC:
            return self._generate_semantic(level, counter, parent_id, semantic_hint, text)
        elif strategy == NamingStrategy.HIERARCHICAL:
            return self._generate_hierarchical(level, counter, parent_id)
        else:  # HYBRID (default)
            return self._generate_hybrid(level, counter, parent_id, semantic_hint, text)

    def _generate_legacy(self, level: str, counter: int) -> str:
        """Generate legacy flat ID (T001, P0001, etc.)."""
        fmt = self.config.legacy_formats.get(level, "{level_prefix}{counter:06d}")
        prefix = self.config.level_prefixes.get(level, level[0].upper())

        # Handle format string that might use different placeholder styles
        if "{counter:" in fmt:
            return fmt.format(counter=counter, level_prefix=prefix)
        else:
            # Old Python format style
            return fmt.format(counter)

    def _generate_uuid(self, level: str) -> str:
        """Generate UUID-based ID."""
        prefix = self.config.level_prefixes.get(level, level[0].upper())
        short_uuid = str(uuid.uuid4())[:8]
        return f"{prefix}_{short_uuid}"

    def _generate_semantic(
        self,
        level: str,
        counter: int,
        parent_id: Optional[str],
        semantic_hint: Optional[str],
        text: Optional[str],
    ) -> str:
        """Generate purely semantic ID."""
        # Get slug from hint or text
        if semantic_hint:
            slug = self.slug_from_text(semantic_hint, self.config.max_slug_length)
        elif text:
            # Use first few words of text
            words = text.split()[:5]
            slug = self.slug_from_text(" ".join(words), self.config.max_slug_length)
        else:
            slug = f"{level}-{counter}"

        if parent_id:
            return f"{parent_id}.{slug}"
        return slug

    def _generate_hierarchical(
        self,
        level: str,
        counter: int,
        parent_id: Optional[str],
    ) -> str:
        """Generate hierarchical path ID (T001.P001.S001)."""
        prefix = self.config.level_prefixes.get(level, level[0].upper())

        if level == "theme":
            return f"{prefix}{counter:03d}"
        elif parent_id:
            return f"{parent_id}.{prefix}{counter:03d}"
        else:
            return f"{prefix}{counter:03d}"

    def _generate_hybrid(
        self,
        level: str,
        counter: int,
        parent_id: Optional[str],
        semantic_hint: Optional[str],
        text: Optional[str],
    ) -> str:
        """
        Generate hybrid ID combining counter and semantic hint.

        Format: T001:semantic-slug.P001.S001
        Only theme level gets semantic slug; deeper levels use hierarchical path.
        """
        prefix = self.config.level_prefixes.get(level, level[0].upper())
        fmt = self.config.formats.get(level)

        if not fmt:
            return self._generate_legacy(level, counter)

        # Build substitution context
        ctx = {
            "counter": counter,
            "level_prefix": prefix,
            "parent": parent_id or "",
        }

        # Add semantic slug for theme level
        if level == "theme":
            if semantic_hint:
                ctx["slug"] = self.slug_from_text(semantic_hint, self.config.max_slug_length)
            elif text:
                words = text.split()[:3]
                ctx["slug"] = self.slug_from_text(" ".join(words), self.config.max_slug_length)
            else:
                ctx["slug"] = f"section-{counter}"

        # Handle format string expansion
        try:
            return fmt.format(**ctx)
        except KeyError:
            # Fallback to hierarchical if format fails
            return self._generate_hierarchical(level, counter, parent_id)

    def reset(self):
        """Reset counters (call before atomizing a new document)."""
        self._reset_counters()


# =============================================================================
# OUTPUT FILE NAMING
# =============================================================================


class ContentDescriptor(Enum):
    """
    Semantic descriptors for analysis output types.

    Maps analysis modules to meaningful content descriptors
    used in output filenames.
    """
    # Semantic analysis outputs
    THEME_NETWORK = "theme-network"
    TERM_CLUSTERS = "term-clusters"
    SIMILARITY_MATRIX = "similarity-matrix"

    # Temporal analysis outputs
    TENSE_FLOW = "tense-flow"
    TIMELINE = "timeline"
    VERB_PATTERNS = "verb-patterns"

    # Sentiment analysis outputs
    EMOTION_ARC = "emotion-arc"
    PEAKS_VALLEYS = "peaks-valleys"
    MILITARY_LEXICON = "military-lexicon"

    # Entity analysis outputs
    MILITARY_REFS = "military-refs"
    LOCATIONS = "locations"
    PERSONS = "persons"

    # Generic descriptors
    DATA = "data"
    ANALYSIS = "analysis"


# Module → default descriptor mapping
MODULE_DESCRIPTORS: Dict[str, ContentDescriptor] = {
    "semantic": ContentDescriptor.THEME_NETWORK,
    "temporal": ContentDescriptor.TENSE_FLOW,
    "sentiment": ContentDescriptor.EMOTION_ARC,
    "entity": ContentDescriptor.MILITARY_REFS,
}


@dataclass
class OutputNamingConfig:
    """Configuration for output file naming."""

    # Pattern: {project}_{module}_{descriptor}_{version}_{timestamp}.{ext}
    pattern: str = "{project}_{module}_{descriptor}_{version}_{timestamp}.{ext}"

    # Timestamp format
    timestamp_format: str = "%Y%m%d"

    # Default version
    default_version: str = "v1"

    # Whether to include timestamp
    include_timestamp: bool = True

    # Custom descriptor overrides per module
    descriptor_overrides: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutputNamingConfig:
        """Create config from dictionary."""
        config = cls()
        if "pattern" in data:
            config.pattern = data["pattern"]
        if "timestamp_format" in data:
            config.timestamp_format = data["timestamp_format"]
        if "default_version" in data:
            config.default_version = data["default_version"]
        if "include_timestamp" in data:
            config.include_timestamp = data["include_timestamp"]
        if "descriptors" in data:
            config.descriptor_overrides = data["descriptors"]
        return config


class OutputNaming:
    """
    Generate semantically meaningful output filenames.

    Follows pattern: {project}_{module}_{descriptor}_{version}_{timestamp}.{ext}
    Example: tomb_semantic_theme-network_v1_20260120.json
    """

    def __init__(self, config: Optional[OutputNamingConfig] = None):
        """Initialize output naming system."""
        self.config = config or OutputNamingConfig()

    def generate_filename(
        self,
        project_name: str,
        module_name: str,
        descriptor: Optional[str] = None,
        version: Optional[str] = None,
        extension: str = "json",
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Generate output filename.

        Args:
            project_name: Project identifier (e.g., "tomb")
            module_name: Analysis module name (e.g., "semantic")
            descriptor: Content descriptor (auto-derived if None)
            version: Version string (e.g., "v1")
            extension: File extension
            timestamp: Optional timestamp (defaults to now)

        Returns:
            Generated filename (without path)
        """
        # Get descriptor
        if descriptor is None:
            # Check for override first
            descriptor = self.config.descriptor_overrides.get(module_name)
            if descriptor is None:
                # Use module default
                desc_enum = MODULE_DESCRIPTORS.get(module_name, ContentDescriptor.DATA)
                descriptor = desc_enum.value

        # Get version
        if version is None:
            version = self.config.default_version

        # Get timestamp
        if self.config.include_timestamp:
            ts = timestamp or datetime.now()
            ts_str = ts.strftime(self.config.timestamp_format)
        else:
            ts_str = ""

        # Shorten project name if needed
        project_slug = OntologicalNaming.slug_from_text(project_name, 20)

        # Build filename parts
        parts = {
            "project": project_slug,
            "module": module_name,
            "descriptor": descriptor,
            "version": version,
            "timestamp": ts_str,
            "ext": extension,
        }

        # Generate using pattern
        filename = self.config.pattern.format(**parts)

        # Clean up double underscores from empty parts
        filename = re.sub(r"_+", "_", filename)
        filename = filename.strip("_")

        return filename

    def generate_path(
        self,
        base_dir,
        project_name: str,
        module_name: str,
        **kwargs,
    ):
        """
        Generate full output path.

        Args:
            base_dir: Base output directory (Path or str)
            project_name: Project identifier
            module_name: Analysis module name
            **kwargs: Additional arguments for generate_filename

        Returns:
            Full Path object
        """
        from pathlib import Path

        filename = self.generate_filename(project_name, module_name, **kwargs)
        return Path(base_dir) / filename


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def create_naming_system(
    strategy: str = "hybrid",
    config_dict: Optional[Dict[str, Any]] = None,
) -> OntologicalNaming:
    """
    Create naming system from strategy name and optional config.

    Args:
        strategy: Strategy name (hierarchical, semantic, uuid, hybrid, legacy)
        config_dict: Optional configuration dictionary

    Returns:
        Configured OntologicalNaming instance
    """
    if config_dict:
        config_dict["strategy"] = strategy
        config = NamingConfig.from_dict(config_dict)
    else:
        config = NamingConfig(strategy=NamingStrategy(strategy))

    return OntologicalNaming(config)


def slugify(text: str, max_len: int = 30) -> str:
    """
    Convenience function to create URL-safe slug from text.

    Args:
        text: Source text
        max_len: Maximum length

    Returns:
        Slugified string
    """
    return OntologicalNaming.slug_from_text(text, max_len)
