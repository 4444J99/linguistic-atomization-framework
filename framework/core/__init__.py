"""
Core framework components: ontology, atomizer, pipeline, registry, and naming.
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
]
