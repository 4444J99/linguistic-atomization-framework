"""
Base Analysis Module - Abstract base class for all analysis modules.

Provides common utilities and interface for corpus analysis.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Generator, List, Optional, Tuple

from ..core.ontology import (
    AnalysisModule,
    AnalysisOutput,
    Atom,
    AtomLevel,
    Corpus,
    Document,
    DomainProfile,
)
from ..core.registry import registry


class BaseAnalysisModule(AnalysisModule):
    """
    Base class with common utilities for analysis modules.

    Subclasses should override the `analyze` method and optionally
    the `name` and `description` class attributes.
    """

    name: str = "base"
    description: str = "Base analysis module - subclass to implement specific analysis"

    def __init__(self):
        """Initialize the analysis module."""
        self._config: Dict[str, Any] = {}

    def iter_atoms(
        self,
        corpus: Corpus,
        level: AtomLevel,
    ) -> Generator[Tuple[Document, Atom], None, None]:
        """
        Iterate over all atoms at a specific level.

        Args:
            corpus: The corpus to iterate
            level: The atom level to yield

        Yields:
            Tuples of (document, atom) for each atom at the specified level
        """
        for doc in corpus.documents:
            for atom in self._iter_atoms_recursive(doc.root_atoms, level):
                yield doc, atom

    def _iter_atoms_recursive(
        self,
        atoms: List[Atom],
        level: AtomLevel,
    ) -> Generator[Atom, None, None]:
        """Recursively iterate through atom tree."""
        for atom in atoms:
            if atom.level == level:
                yield atom
            yield from self._iter_atoms_recursive(atom.children, level)

    def get_all_text_at_level(
        self,
        corpus: Corpus,
        level: AtomLevel,
    ) -> List[Tuple[str, str]]:
        """
        Get all text content at a specific level.

        Args:
            corpus: The corpus to process
            level: The atom level to extract

        Returns:
            List of (atom_id, text) tuples
        """
        return [(atom.id, atom.text) for _, atom in self.iter_atoms(corpus, level)]

    def get_theme_texts(self, corpus: Corpus) -> Dict[str, str]:
        """
        Get theme-level text content.

        Returns:
            Dict mapping theme_id to theme text
        """
        return {atom.id: atom.text for _, atom in self.iter_atoms(corpus, AtomLevel.THEME)}

    def get_sentence_data(self, corpus: Corpus) -> List[Dict[str, Any]]:
        """
        Get sentence data with parent references.

        Returns:
            List of sentence info dicts
        """
        sentences = []
        for doc, atom in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            sentences.append({
                "id": atom.id,
                "text": atom.text,
                "theme_id": atom.theme_id,
                "paragraph_id": atom.paragraph_id,
                "document_id": doc.id,
            })
        return sentences

    def make_output(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Create an AnalysisOutput with standard metadata.

        Args:
            data: The analysis results data
            metadata: Optional additional metadata

        Returns:
            AnalysisOutput instance
        """
        return AnalysisOutput(
            module_name=self.name,
            data=data,
            metadata={
                "config": self._config.copy(),
                **(metadata or {}),
            },
            created_at=datetime.now(),
        )

    @abstractmethod
    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run analysis on the corpus.

        Must be implemented by subclasses.
        """
        pass
