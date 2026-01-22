"""
Atomizer - Generic text atomization engine.

Transforms source documents into hierarchical Atom structures based on
an AtomizationSchema. Supports multiple document formats and customizable
splitting patterns.

Multilingual Support:
- Automatic language and script detection
- Language-specific tokenization (CJK, Arabic, Thai, etc.)
- Configurable CJK strategy (NLP segmentation vs character-level)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .ontology import (
    Atom,
    AtomizationSchema,
    AtomLevel,
    Corpus,
    Document,
)
from .tokenizers import TokenizerFactory, TokenizerConfig, get_tokenizer, tokenize_sentences
from .language import detect_language, detect_script, detect_all
from ..loaders import PDFLoader


class Atomizer:
    """
    Generic atomization engine for parsing text into hierarchical structures.

    The atomizer takes a schema defining the hierarchy levels and splitting
    patterns, then processes documents into Atom trees.

    Supports both legacy flat IDs (T001, P0001) and ontological naming
    (T001:semantic-slug.P001.S001) based on schema configuration.
    """

    def __init__(
        self,
        schema: Optional[AtomizationSchema] = None,
        tokenizer_config: Optional[TokenizerConfig] = None,
    ):
        """
        Initialize atomizer with optional schema and tokenizer config.

        Args:
            schema: AtomizationSchema defining levels and splitters.
                   Defaults to the standard 5-level hierarchy.
            tokenizer_config: Configuration for multi-language tokenization.
                   Controls CJK strategy, punctuation handling, etc.
        """
        self.schema = schema or AtomizationSchema.default()
        self._counters: Dict[AtomLevel, int] = {}
        self._tokenizer_factory = TokenizerFactory(tokenizer_config)
        self._current_language: str = "en"
        self._reset_counters()

    def _reset_counters(self):
        """Reset all ID counters to 1."""
        self._counters = {level: 1 for level in self.schema.levels}
        # Also reset ontological naming system if in use
        self.schema.reset_naming()

    def _next_id(
        self,
        level: AtomLevel,
        parent_id: Optional[str] = None,
        semantic_hint: Optional[str] = None,
        text: Optional[str] = None,
    ) -> str:
        """
        Generate next ID for a level and increment counter.

        Args:
            level: The atom level
            parent_id: Parent atom's ID (for hierarchical strategies)
            semantic_hint: Semantic descriptor (e.g., theme title)
            text: Atom text content (for deriving semantic slug)

        Returns:
            Generated atom ID
        """
        current = self._counters.get(level, 1)
        atom_id = self.schema.generate_id(
            level,
            current,
            parent_id=parent_id,
            semantic_hint=semantic_hint,
            text=text,
        )
        self._counters[level] = current + 1
        return atom_id

    def atomize_text(
        self,
        text: str,
        level: AtomLevel,
        parent_id: Optional[str] = None,
        back_refs: Optional[Dict[str, str]] = None,
        language: Optional[str] = None,
    ) -> List[Atom]:
        """
        Recursively atomize text at the given level and deeper.

        Args:
            text: Source text to atomize
            level: Current hierarchy level
            parent_id: ID of parent atom (for back-reference)
            back_refs: Dict of back-references (theme_id, paragraph_id, etc.)
            language: Language code for tokenization (auto-detected if None)

        Returns:
            List of Atom objects at this level
        """
        # Use provided language or current context
        lang = language or self._current_language
        if back_refs is None:
            back_refs = {}

        atoms = []
        level_idx = self.schema.levels.index(level) if level in self.schema.levels else -1

        # Get splitter pattern for this level
        splitter = self.schema.splitters.get(level)

        if level == AtomLevel.THEME:
            # Special handling for themes (markdown ## headers)
            parts = re.split(splitter, text, flags=re.MULTILINE)
            # First part is preamble (skip if empty), then alternating title/content
            for i in range(1, len(parts), 2):
                if i + 1 >= len(parts):
                    break
                title = parts[i].strip()
                content = parts[i + 1].strip()
                if not content:
                    continue

                # Generate ID with semantic hint from title
                atom_id = self._next_id(
                    level,
                    parent_id=parent_id,
                    semantic_hint=title,
                    text=content,
                )
                atom = Atom(
                    id=atom_id,
                    level=level,
                    text=content,
                    parent_id=parent_id,
                    metadata={"title": title},
                    **{k: v for k, v in back_refs.items() if v},
                )

                # Recurse to next level
                next_level_idx = level_idx + 1
                if next_level_idx < len(self.schema.levels):
                    next_level = self.schema.levels[next_level_idx]
                    child_refs = {**back_refs, "theme_id": atom_id}
                    atom.children = self.atomize_text(
                        content, next_level, atom_id, child_refs, lang
                    )

                atoms.append(atom)

        elif level == AtomLevel.PARAGRAPH:
            # Split on double newlines
            parts = re.split(splitter, text)
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Generate ID with parent context
                atom_id = self._next_id(
                    level,
                    parent_id=parent_id,
                    text=part,
                )
                atom = Atom(
                    id=atom_id,
                    level=level,
                    text=part,
                    parent_id=parent_id,
                    **{k: v for k, v in back_refs.items() if v},
                )

                # Recurse to sentences
                next_level_idx = level_idx + 1
                if next_level_idx < len(self.schema.levels):
                    next_level = self.schema.levels[next_level_idx]
                    child_refs = {**back_refs, "paragraph_id": atom_id}
                    atom.children = self.atomize_text(
                        part, next_level, atom_id, child_refs, lang
                    )

                atoms.append(atom)

        elif level == AtomLevel.SENTENCE:
            # Use language-aware sentence tokenizer when available
            sent_tokenizer = self._tokenizer_factory.get_sentence_tokenizer(lang)
            parts = sent_tokenizer.tokenize(text)
            for part in parts:
                part = part.strip()
                if not part:
                    continue

                # Generate ID with parent context
                atom_id = self._next_id(
                    level,
                    parent_id=parent_id,
                    text=part,
                )
                atom = Atom(
                    id=atom_id,
                    level=level,
                    text=part,
                    parent_id=parent_id,
                    **{k: v for k, v in back_refs.items() if v},
                )

                # Recurse to words
                next_level_idx = level_idx + 1
                if next_level_idx < len(self.schema.levels):
                    next_level = self.schema.levels[next_level_idx]
                    child_refs = {**back_refs, "sentence_id": atom_id}
                    atom.children = self.atomize_text(
                        part, next_level, atom_id, child_refs, lang
                    )

                atoms.append(atom)

        elif level == AtomLevel.WORD:
            # Use language-aware tokenizer for word splitting
            tokenizer = self._tokenizer_factory.get_tokenizer(lang)
            matches = tokenizer.tokenize(text)
            for word_text in matches:
                # Generate ID with parent context
                atom_id = self._next_id(
                    level,
                    parent_id=parent_id,
                    text=word_text,
                )
                atom = Atom(
                    id=atom_id,
                    level=level,
                    text=word_text,
                    parent_id=parent_id,
                    **{k: v for k, v in back_refs.items() if v},
                )

                # Recurse to letters
                next_level_idx = level_idx + 1
                if next_level_idx < len(self.schema.levels):
                    next_level = self.schema.levels[next_level_idx]
                    child_refs = {**back_refs, "word_id": atom_id}
                    atom.children = self.atomize_text(
                        word_text, next_level, atom_id, child_refs, lang
                    )

                atoms.append(atom)

        elif level == AtomLevel.LETTER:
            # Individual characters
            for char in text:
                # Generate ID with parent context
                atom_id = self._next_id(
                    level,
                    parent_id=parent_id,
                    text=char,
                )
                # Skip if ID is empty (letter level disabled in config)
                if not atom_id:
                    continue
                atom = Atom(
                    id=atom_id,
                    level=level,
                    text=char,
                    parent_id=parent_id,
                    metadata={"char": char},
                    **{k: v for k, v in back_refs.items() if v},
                )
                atoms.append(atom)

        return atoms

    def atomize_document(
        self,
        source_path: Path,
        document_id: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Document:
        """
        Atomize a single document file.

        Args:
            source_path: Path to source document
            document_id: Optional document ID (auto-generated if not provided)
            title: Optional title override
            author: Optional author metadata
            language: Language code (auto-detected if None)

        Returns:
            Document with atomized content including language metadata
        """
        self._reset_counters()

        # Detect format from extension
        suffix = source_path.suffix.lower()
        format_map = {
            ".md": "markdown",
            ".markdown": "markdown",
            ".txt": "plain",
            ".html": "html",
            ".htm": "html",
            ".pdf": "pdf",
        }
        doc_format = format_map.get(suffix, "plain")

        # Read content (handle PDF specially)
        if doc_format == "pdf":
            pdf_loader = PDFLoader()
            content = pdf_loader.extract_text(source_path)
        else:
            with open(source_path, "r", encoding="utf-8") as f:
                content = f.read()

        # Detect language and script if not provided
        if language:
            self._current_language = language
            lang_info = detect_all(content)
            script = lang_info.script.value
        else:
            lang_info = detect_all(content)
            self._current_language = lang_info.language
            language = lang_info.language
            script = lang_info.script.value

        # Create document with language metadata
        doc = Document(
            id=document_id or f"DOC{hash(str(source_path)) % 10000:04d}",
            source_path=source_path,
            format=doc_format,
            title=title,
            author=author,
            language=language,
            script=script,
        )

        # Start atomization from first level with language context
        first_level = self.schema.levels[0]
        doc.root_atoms = self.atomize_text(content, first_level, language=language)

        return doc

    def atomize_corpus(
        self,
        name: str,
        document_configs: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Corpus:
        """
        Atomize multiple documents into a corpus.

        Args:
            name: Corpus name
            document_configs: List of dicts with keys: source, id (optional),
                            title (optional), author (optional)
            metadata: Optional corpus-level metadata

        Returns:
            Corpus containing all atomized documents
        """
        corpus = Corpus(
            name=name,
            schema=self.schema,
            metadata=metadata or {},
            created_at=datetime.now(),
        )

        for i, config in enumerate(document_configs):
            source = Path(config["source"])
            doc = self.atomize_document(
                source_path=source,
                document_id=config.get("id", f"DOC{i+1:03d}"),
                title=config.get("title"),
                author=config.get("author"),
            )
            corpus.documents.append(doc)

        return corpus

    def export_json(
        self,
        corpus: Corpus,
        output_path: Path,
        indent: int = 2,
    ) -> Path:
        """
        Export corpus to JSON file.

        Args:
            corpus: Corpus to export
            output_path: Destination file path
            indent: JSON indentation (default 2)

        Returns:
            Path to written file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(corpus.to_dict(), f, indent=indent, ensure_ascii=False)
        return output_path

    @staticmethod
    def load_json(input_path: Path) -> Corpus:
        """
        Load corpus from JSON file.

        Args:
            input_path: Path to JSON file

        Returns:
            Deserialized Corpus
        """
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Corpus.from_dict(data, name=input_path.stem)


def atomize_file(
    source_path: Path,
    output_path: Optional[Path] = None,
    schema: Optional[AtomizationSchema] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    verbose: bool = False,
) -> Corpus:
    """
    Convenience function to atomize a single file.

    Args:
        source_path: Path to source document
        output_path: Optional path to write JSON output
        schema: Optional atomization schema
        title: Optional document title
        author: Optional document author
        verbose: Print progress messages

    Returns:
        Atomized Corpus
    """
    atomizer = Atomizer(schema)

    if verbose:
        print(f"Atomizing: {source_path}")

    doc = atomizer.atomize_document(
        source_path=source_path,
        title=title,
        author=author,
    )

    corpus = Corpus(
        name=title or source_path.stem,
        documents=[doc],
        schema=atomizer.schema,
    )

    if verbose:
        stats = {
            "themes": corpus.count_atoms(AtomLevel.THEME),
            "paragraphs": corpus.count_atoms(AtomLevel.PARAGRAPH),
            "sentences": corpus.count_atoms(AtomLevel.SENTENCE),
            "words": corpus.count_atoms(AtomLevel.WORD),
            "letters": corpus.count_atoms(AtomLevel.LETTER),
        }
        print(f"  Themes: {stats['themes']}")
        print(f"  Paragraphs: {stats['paragraphs']}")
        print(f"  Sentences: {stats['sentences']}")
        print(f"  Words: {stats['words']}")
        print(f"  Letters: {stats['letters']}")

    if output_path:
        atomizer.export_json(corpus, output_path)
        if verbose:
            print(f"Exported: {output_path}")

    return corpus
