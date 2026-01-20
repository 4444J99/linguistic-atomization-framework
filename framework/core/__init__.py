"""
Core framework components: ontology, atomizer, pipeline, registry, naming, recursion, and reproducibility.

Components:
- ontology: Core data structures (Atom, Corpus, etc.)
- atomizer: Text atomization engine
- registry: Component registration system
- pipeline: Analysis orchestration
- naming: Ontological naming strategies
- recursion: Iterative analysis loop
- reproducibility: Analysis verification and replication
"""

from .ontology import (
    AtomLevel,
    AtomizationSchema,
    Atom,
    Document,
    Corpus,
    DomainLexicon,
    EntityPattern,
    EntityPatternSet,
    DomainProfile,
    AnalysisOutput,
    AnalysisModule,
    VisualizationAdapter,
)
from .atomizer import Atomizer
from .registry import Registry, registry
from .pipeline import Pipeline, PipelineConfig
from .naming import (
    NamingStrategy,
    NamingConfig,
    OntologicalNaming,
    OutputNaming,
    OutputNamingConfig,
    ContentDescriptor,
    create_naming_system,
    slugify,
)
from .recursion import (
    RecursionTracker,
    IterationRecord,
    ScoreComparison,
    format_comparison_report,
    format_progress_report,
)
from .reproducibility import (
    ReproducibilityTracker,
    ReproducibilityRecord,
    AnalysisConfig,
    InputFingerprint,
    EnvironmentInfo,
    create_reproducibility_record,
    format_reproducibility_citation,
    LINGFRAME_VERSION,
)

__all__ = [
    # Ontology
    "AtomLevel",
    "AtomizationSchema",
    "Atom",
    "Document",
    "Corpus",
    "DomainLexicon",
    "EntityPattern",
    "EntityPatternSet",
    "DomainProfile",
    "AnalysisOutput",
    "AnalysisModule",
    "VisualizationAdapter",
    # Core components
    "Atomizer",
    "Registry",
    "registry",
    "Pipeline",
    "PipelineConfig",
    # Naming system
    "NamingStrategy",
    "NamingConfig",
    "OntologicalNaming",
    "OutputNaming",
    "OutputNamingConfig",
    "ContentDescriptor",
    "create_naming_system",
    "slugify",
    # Recursion
    "RecursionTracker",
    "IterationRecord",
    "ScoreComparison",
    "format_comparison_report",
    "format_progress_report",
    # Reproducibility
    "ReproducibilityTracker",
    "ReproducibilityRecord",
    "AnalysisConfig",
    "InputFingerprint",
    "EnvironmentInfo",
    "create_reproducibility_record",
    "format_reproducibility_citation",
    "LINGFRAME_VERSION",
]
