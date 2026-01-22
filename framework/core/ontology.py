"""
Core Ontology - Domain-agnostic base classes for linguistic analysis.

This module defines the fundamental data structures used throughout the framework:
- Atomization hierarchy (Corpus → Document → Atom levels)
- Domain resources (lexicons, entity patterns)
- Analysis and visualization interfaces (ABCs)

Multilingual Support:
- Documents can specify language (ISO 639-1) and script
- Translation tracking between original and translated documents
- Original titles preserved for non-Latin scripts
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Protocol, Sequence, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .naming import OntologicalNaming, NamingConfig


# =============================================================================
# ATOMIZATION HIERARCHY
# =============================================================================


class AtomLevel(Enum):
    """
    Standard hierarchical levels for text atomization.

    The hierarchy follows: THEME → PARAGRAPH → SENTENCE → WORD → LETTER
    Custom levels can extend this by subclassing or using CUSTOM with metadata.
    """
    THEME = "theme"           # Top-level sections (## headers in markdown)
    PARAGRAPH = "paragraph"   # Text blocks separated by blank lines
    SENTENCE = "sentence"     # Split on sentence-ending punctuation
    WORD = "word"             # Whitespace-separated tokens
    LETTER = "letter"         # Individual characters
    CUSTOM = "custom"         # User-defined level

    @property
    def depth(self) -> int:
        """Return numeric depth (0 = root, higher = more granular)."""
        order = [self.THEME, self.PARAGRAPH, self.SENTENCE, self.WORD, self.LETTER]
        try:
            return order.index(self)
        except ValueError:
            return -1  # CUSTOM


@dataclass
class AtomizationSchema:
    """
    Configuration for how text is atomized into hierarchical units.

    Defines the levels to extract and the patterns/splitters used for each level.
    Supports both legacy ID formats and the new ontological naming system.
    """
    name: str
    levels: List[AtomLevel]
    splitters: Dict[AtomLevel, str] = field(default_factory=dict)  # Level → regex pattern
    id_formats: Dict[AtomLevel, str] = field(default_factory=dict)  # Level → ID format string (legacy)

    # Ontological naming configuration
    naming_strategy: str = "legacy"  # hierarchical | semantic | uuid | hybrid | legacy
    naming_config: Optional[Dict[str, Any]] = None

    # Cached naming system instance
    _naming_system: Optional["OntologicalNaming"] = field(default=None, repr=False)

    def __post_init__(self):
        # Default splitters if not provided
        default_splitters = {
            AtomLevel.THEME: r'^## (.+)$',                     # Markdown ## headers
            AtomLevel.PARAGRAPH: r'\n\n+',                      # Double newlines
            AtomLevel.SENTENCE: r'(?<=[.!?])\s+',               # Sentence boundaries
            AtomLevel.WORD: r'\S+',                             # Non-whitespace runs
            AtomLevel.LETTER: None,                             # Character iteration
        }
        default_formats = {
            AtomLevel.THEME: "T{:03d}",
            AtomLevel.PARAGRAPH: "P{:04d}",
            AtomLevel.SENTENCE: "S{:05d}",
            AtomLevel.WORD: "W{:06d}",
            AtomLevel.LETTER: "L{:08d}",
        }
        for level in self.levels:
            if level not in self.splitters:
                self.splitters[level] = default_splitters.get(level)
            if level not in self.id_formats:
                self.id_formats[level] = default_formats.get(level, f"{level.value[0].upper()}{{:06d}}")

    @property
    def naming_system(self) -> "OntologicalNaming":
        """Get or create the naming system instance."""
        if self._naming_system is None:
            from .naming import create_naming_system
            self._naming_system = create_naming_system(
                strategy=self.naming_strategy,
                config_dict=self.naming_config,
            )
        return self._naming_system

    @property
    def uses_ontological_naming(self) -> bool:
        """Check if schema uses new ontological naming (not legacy)."""
        return self.naming_strategy != "legacy"

    def generate_id(
        self,
        level: AtomLevel,
        counter: int,
        parent_id: Optional[str] = None,
        semantic_hint: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """
        Generate a unique ID for an atom at the given level.

        Args:
            level: The atom level
            counter: Counter value for this level
            parent_id: Parent atom's ID (for hierarchical strategies)
            semantic_hint: Semantic descriptor (e.g., theme title)
            text: Atom text content (for deriving semantic slug)

        Returns:
            Generated atom ID string
        """
        if self.uses_ontological_naming:
            return self.naming_system.generate_id(
                level=level.value,
                counter=counter,
                parent_id=parent_id,
                semantic_hint=semantic_hint,
                text=text,
            )

        # Legacy format
        fmt = self.id_formats.get(level, f"{level.value[0].upper()}{{:06d}}")
        return fmt.format(counter)

    def reset_naming(self):
        """Reset naming system counters (call before atomizing a new document)."""
        if self._naming_system is not None:
            self._naming_system.reset()

    @classmethod
    def default(cls) -> AtomizationSchema:
        """Return the default 5-level schema (theme → letter) with legacy naming."""
        return cls(
            name="default",
            levels=[
                AtomLevel.THEME,
                AtomLevel.PARAGRAPH,
                AtomLevel.SENTENCE,
                AtomLevel.WORD,
                AtomLevel.LETTER,
            ],
            naming_strategy="legacy",
        )

    @classmethod
    def with_ontological_naming(
        cls,
        strategy: str = "hybrid",
        naming_config: Optional[Dict[str, Any]] = None,
    ) -> AtomizationSchema:
        """
        Return default schema with ontological naming enabled.

        Args:
            strategy: Naming strategy (hierarchical, semantic, uuid, hybrid)
            naming_config: Optional naming configuration dict

        Returns:
            AtomizationSchema with ontological naming
        """
        return cls(
            name="ontological",
            levels=[
                AtomLevel.THEME,
                AtomLevel.PARAGRAPH,
                AtomLevel.SENTENCE,
                AtomLevel.WORD,
                AtomLevel.LETTER,
            ],
            naming_strategy=strategy,
            naming_config=naming_config,
        )


@dataclass
class Atom:
    """
    A single atomic unit of text at any hierarchical level.

    Atoms form a tree structure: each atom may contain child atoms of a deeper level.
    """
    id: str
    level: AtomLevel
    text: str
    parent_id: Optional[str] = None
    children: List[Atom] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Back-references for convenient traversal
    theme_id: Optional[str] = None
    paragraph_id: Optional[str] = None
    sentence_id: Optional[str] = None
    word_id: Optional[str] = None

    @property
    def child_count(self) -> int:
        return len(self.children)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize atom to dictionary (for JSON export)."""
        result = {
            "id": self.id,
            "level": self.level.value,
            "text": self.text,
        }
        if self.parent_id:
            result["parent_id"] = self.parent_id
        if self.metadata:
            result["metadata"] = self.metadata
        if self.children:
            # Use level-specific key names for backward compatibility
            child_key = f"{self.children[0].level.value}s" if self.children else "children"
            result[child_key] = [c.to_dict() for c in self.children]
            result[f"{self.children[0].level.value}_count"] = len(self.children)
        # Add back-references
        for ref_name in ["theme_id", "paragraph_id", "sentence_id", "word_id"]:
            ref_val = getattr(self, ref_name)
            if ref_val and ref_name != f"{self.level.value}_id":
                result[ref_name] = ref_val
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Atom:
        """Deserialize atom from dictionary."""
        level = AtomLevel(data["level"]) if isinstance(data.get("level"), str) else data.get("level", AtomLevel.CUSTOM)
        atom = cls(
            id=data["id"],
            level=level,
            text=data.get("text", ""),
            parent_id=data.get("parent_id"),
            metadata=data.get("metadata", {}),
            theme_id=data.get("theme_id"),
            paragraph_id=data.get("paragraph_id"),
            sentence_id=data.get("sentence_id"),
            word_id=data.get("word_id"),
        )
        # Load children from level-specific keys
        for child_level in AtomLevel:
            child_key = f"{child_level.value}s"
            if child_key in data:
                atom.children = [cls.from_dict(c) for c in data[child_key]]
                break
        return atom


@dataclass
class Document:
    """
    A single source document within a corpus.

    A document has metadata and a root atom (typically THEME level).
    Supports multiple languages and writing scripts for multilingual corpora.
    """
    id: str
    source_path: Path
    format: str = "markdown"  # markdown, plain, html, etc.
    title: Optional[str] = None
    author: Optional[str] = None
    root_atoms: List[Atom] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Multilingual support
    language: Optional[str] = None         # ISO 639-1 code (e.g., "en", "zh", "ar")
    script: Optional[str] = None           # Writing script (e.g., "latin", "chinese", "arabic")
    original_title: Optional[str] = None   # Title in original script (for non-Latin)
    translation_of: Optional[str] = None   # Document ID this is a translation of
    translator: Optional[str] = None       # Translator name for translations

    def to_dict(self) -> Dict[str, Any]:
        """Serialize document for JSON export."""
        result = {
            "id": self.id,
            "source_path": str(self.source_path),
            "format": self.format,
            "title": self.title,
            "author": self.author,
            "themes": [atom.to_dict() for atom in self.root_atoms],
            "metadata": self.metadata,
        }
        # Add multilingual fields if present
        if self.language:
            result["language"] = self.language
        if self.script:
            result["script"] = self.script
        if self.original_title:
            result["original_title"] = self.original_title
        if self.translation_of:
            result["translation_of"] = self.translation_of
        if self.translator:
            result["translator"] = self.translator
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Document:
        """Deserialize document from dictionary."""
        doc = cls(
            id=data["id"],
            source_path=Path(data["source_path"]),
            format=data.get("format", "markdown"),
            title=data.get("title"),
            author=data.get("author"),
            metadata=data.get("metadata", {}),
            language=data.get("language"),
            script=data.get("script"),
            original_title=data.get("original_title"),
            translation_of=data.get("translation_of"),
            translator=data.get("translator"),
        )
        # Load root atoms from "themes" key (backward compat) or "root_atoms"
        themes_data = data.get("themes", data.get("root_atoms", []))
        doc.root_atoms = [Atom.from_dict(t) for t in themes_data]
        return doc


@dataclass
class Corpus:
    """
    A collection of documents forming the analysis corpus.

    The corpus is the top-level container holding all documents,
    global metadata, and atomization configuration.
    """
    name: str
    documents: List[Document] = field(default_factory=list)
    schema: AtomizationSchema = field(default_factory=AtomizationSchema.default)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def total_documents(self) -> int:
        return len(self.documents)

    def count_atoms(self, level: AtomLevel) -> int:
        """Count all atoms at a specific level across all documents."""
        def count_recursive(atoms: List[Atom]) -> int:
            total = 0
            for atom in atoms:
                if atom.level == level:
                    total += 1
                total += count_recursive(atom.children)
            return total

        return sum(count_recursive(doc.root_atoms) for doc in self.documents)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize corpus for JSON export (backward-compatible with original format)."""
        # Aggregate statistics
        stats = {
            "total_themes": self.count_atoms(AtomLevel.THEME),
            "total_paragraphs": self.count_atoms(AtomLevel.PARAGRAPH),
            "total_sentences": self.count_atoms(AtomLevel.SENTENCE),
            "total_words": self.count_atoms(AtomLevel.WORD),
            "total_letters": self.count_atoms(AtomLevel.LETTER),
        }

        # For single-document corpora, flatten to match original format
        if len(self.documents) == 1:
            doc = self.documents[0]
            return {
                "metadata": {
                    "title": doc.title or self.name,
                    "author": doc.author or "",
                    "atomized_date": self.created_at.strftime("%Y-%m-%d"),
                    "hierarchy": " → ".join(level.value for level in self.schema.levels),
                    **stats,
                    **self.metadata,
                },
                "themes": [atom.to_dict() for atom in doc.root_atoms],
            }

        # Multi-document format
        return {
            "corpus": {
                "name": self.name,
                "created_at": self.created_at.isoformat(),
                "schema": self.schema.name,
                **stats,
                **self.metadata,
            },
            "documents": [doc.to_dict() for doc in self.documents],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], name: str = "corpus") -> Corpus:
        """Deserialize corpus from dictionary (handles both old and new formats)."""
        # Detect format
        if "corpus" in data:
            # New multi-document format
            corpus_meta = data["corpus"]
            corpus = cls(
                name=corpus_meta.get("name", name),
                metadata=corpus_meta,
            )
            corpus.documents = [Document.from_dict(d) for d in data.get("documents", [])]
        elif "themes" in data:
            # Old single-document format (tomb-of-the-unknowns style)
            meta = data.get("metadata", {})
            doc = Document(
                id="DOC001",
                source_path=Path("unknown"),
                title=meta.get("title"),
                author=meta.get("author"),
            )
            doc.root_atoms = [Atom.from_dict(t) for t in data["themes"]]
            corpus = cls(
                name=meta.get("title", name),
                documents=[doc],
                metadata=meta,
            )
        else:
            corpus = cls(name=name)

        return corpus


# =============================================================================
# DOMAIN RESOURCES
# =============================================================================


@dataclass
class DomainLexicon:
    """
    A domain-specific sentiment/scoring lexicon.

    Maps terms to numeric scores for domain-aware sentiment analysis.
    """
    name: str
    terms: Dict[str, float] = field(default_factory=dict)
    description: str = ""

    def get_score(self, term: str, default: float = 0.0) -> float:
        """Look up score for a term (case-insensitive)."""
        return self.terms.get(term.lower(), default)

    def merge(self, other: DomainLexicon) -> DomainLexicon:
        """Merge another lexicon, with other's terms taking precedence."""
        merged_terms = {**self.terms, **other.terms}
        return DomainLexicon(
            name=f"{self.name}+{other.name}",
            terms=merged_terms,
            description=f"Merged: {self.description}; {other.description}",
        )


@dataclass
class EntityPattern:
    """A single named entity pattern for regex-based extraction."""
    label: str           # Entity type (e.g., "MILITARY_TERM", "LOCATION")
    pattern: str         # Regex pattern
    flags: int = re.IGNORECASE

    def compile(self) -> re.Pattern:
        return re.compile(self.pattern, self.flags)


@dataclass
class EntityPatternSet:
    """Collection of entity patterns for a domain."""
    name: str
    patterns: List[EntityPattern] = field(default_factory=list)
    description: str = ""

    def compiled(self) -> Dict[str, re.Pattern]:
        """Return dict of label → compiled regex."""
        return {p.label: p.compile() for p in self.patterns}


@dataclass
class DomainProfile:
    """
    Complete domain configuration combining lexicons and entity patterns.

    A domain profile customizes the analysis for a specific subject area
    (e.g., military, medical, legal).
    """
    name: str
    lexicons: List[DomainLexicon] = field(default_factory=list)
    entity_patterns: List[EntityPatternSet] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def primary_lexicon(self) -> Optional[DomainLexicon]:
        """Return first lexicon or None."""
        return self.lexicons[0] if self.lexicons else None

    @property
    def primary_patterns(self) -> Optional[EntityPatternSet]:
        """Return first pattern set or None."""
        return self.entity_patterns[0] if self.entity_patterns else None

    def merged_lexicon(self) -> DomainLexicon:
        """Merge all lexicons into one (later lexicons override earlier)."""
        if not self.lexicons:
            return DomainLexicon(name=f"{self.name}_empty")
        result = self.lexicons[0]
        for lex in self.lexicons[1:]:
            result = result.merge(lex)
        return result


# =============================================================================
# ANALYSIS AND VISUALIZATION INTERFACES
# =============================================================================


@dataclass
class AnalysisOutput:
    """
    Result container for analysis modules.

    Holds the analysis data plus metadata about how it was generated.
    """
    module_name: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module": self.module_name,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
            **self.data,
        }


class AnalysisModule(ABC):
    """
    Abstract base class for analysis modules.

    Subclasses implement specific analysis logic (semantic, temporal, sentiment, etc.).
    Each module takes a Corpus and optional DomainProfile, returning AnalysisOutput.
    """

    name: str = "base"
    description: str = "Base analysis module"

    @abstractmethod
    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run analysis on the corpus.

        Args:
            corpus: The atomized corpus to analyze
            domain: Optional domain profile for domain-specific processing
            config: Optional configuration overrides

        Returns:
            AnalysisOutput containing the results
        """
        pass

    def validate_corpus(self, corpus: Corpus) -> bool:
        """Check if corpus is suitable for this analysis."""
        return len(corpus.documents) > 0


class VisualizationAdapter(ABC):
    """
    Abstract base class for visualization adapters.

    Adapters take AnalysisOutput and generate visualization artifacts
    (HTML files, JSON for frontend libraries, etc.).
    """

    name: str = "base"
    description: str = "Base visualization adapter"
    supported_analysis: List[str] = []  # Module names this adapter can visualize

    @abstractmethod
    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate visualization artifact.

        Args:
            analysis: The analysis output to visualize
            output_path: Directory to write output files
            config: Optional configuration (colors, sizes, etc.)

        Returns:
            Path to the generated artifact
        """
        pass

    def can_visualize(self, analysis: AnalysisOutput) -> bool:
        """Check if this adapter can visualize the given analysis output."""
        return analysis.module_name in self.supported_analysis or not self.supported_analysis
