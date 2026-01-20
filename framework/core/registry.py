"""
Registry - Plugin registration and discovery system.

Provides a central registry for analysis modules, visualization adapters,
domain profiles, and atomization schemas. Supports both programmatic
registration and auto-discovery from packages.
"""

from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar

from .ontology import (
    AnalysisModule,
    AtomizationSchema,
    DomainProfile,
    VisualizationAdapter,
)

T = TypeVar("T")


class Registry:
    """
    Central registry for framework plugins and resources.

    Stores and retrieves:
    - Analysis modules (semantic, temporal, sentiment, entity)
    - Visualization adapters (D3, Plotly, Chart.js)
    - Domain profiles (military, medical, legal, etc.)
    - Atomization schemas (default, custom)
    """

    def __init__(self):
        self._analysis_modules: Dict[str, Type[AnalysisModule]] = {}
        self._visualization_adapters: Dict[str, Type[VisualizationAdapter]] = {}
        self._domain_profiles: Dict[str, DomainProfile] = {}
        self._schemas: Dict[str, AtomizationSchema] = {}

        # Register default schema
        self._schemas["default"] = AtomizationSchema.default()

    # =========================================================================
    # Analysis Modules
    # =========================================================================

    def register_analysis(
        self,
        name: Optional[str] = None,
    ) -> Callable[[Type[AnalysisModule]], Type[AnalysisModule]]:
        """
        Decorator to register an analysis module.

        Usage:
            @registry.register_analysis("semantic")
            class SemanticAnalysis(AnalysisModule):
                ...
        """
        def decorator(cls: Type[AnalysisModule]) -> Type[AnalysisModule]:
            module_name = name or getattr(cls, "name", cls.__name__.lower())
            self._analysis_modules[module_name] = cls
            return cls
        return decorator

    def get_analysis(self, name: str) -> Optional[Type[AnalysisModule]]:
        """Get an analysis module class by name."""
        return self._analysis_modules.get(name)

    def list_analysis_modules(self) -> List[str]:
        """List all registered analysis module names."""
        return list(self._analysis_modules.keys())

    def create_analysis(self, name: str, **kwargs) -> AnalysisModule:
        """Create an instance of an analysis module."""
        cls = self.get_analysis(name)
        if cls is None:
            raise KeyError(f"Analysis module '{name}' not found. Available: {self.list_analysis_modules()}")
        return cls(**kwargs)

    # =========================================================================
    # Visualization Adapters
    # =========================================================================

    def register_adapter(
        self,
        name: Optional[str] = None,
    ) -> Callable[[Type[VisualizationAdapter]], Type[VisualizationAdapter]]:
        """
        Decorator to register a visualization adapter.

        Usage:
            @registry.register_adapter("force_graph")
            class ForceGraphAdapter(VisualizationAdapter):
                ...
        """
        def decorator(cls: Type[VisualizationAdapter]) -> Type[VisualizationAdapter]:
            adapter_name = name or getattr(cls, "name", cls.__name__.lower())
            self._visualization_adapters[adapter_name] = cls
            return cls
        return decorator

    def get_adapter(self, name: str) -> Optional[Type[VisualizationAdapter]]:
        """Get a visualization adapter class by name."""
        return self._visualization_adapters.get(name)

    def list_adapters(self) -> List[str]:
        """List all registered adapter names."""
        return list(self._visualization_adapters.keys())

    def create_adapter(self, name: str, **kwargs) -> VisualizationAdapter:
        """Create an instance of a visualization adapter."""
        cls = self.get_adapter(name)
        if cls is None:
            raise KeyError(f"Adapter '{name}' not found. Available: {self.list_adapters()}")
        return cls(**kwargs)

    # =========================================================================
    # Domain Profiles
    # =========================================================================

    def register_domain(self, profile: DomainProfile) -> None:
        """Register a domain profile."""
        self._domain_profiles[profile.name] = profile

    def get_domain(self, name: str) -> Optional[DomainProfile]:
        """Get a domain profile by name."""
        return self._domain_profiles.get(name)

    def list_domains(self) -> List[str]:
        """List all registered domain profile names."""
        return list(self._domain_profiles.keys())

    # =========================================================================
    # Atomization Schemas
    # =========================================================================

    def register_schema(self, schema: AtomizationSchema) -> None:
        """Register an atomization schema."""
        self._schemas[schema.name] = schema

    def get_schema(self, name: str) -> Optional[AtomizationSchema]:
        """Get an atomization schema by name."""
        return self._schemas.get(name)

    def list_schemas(self) -> List[str]:
        """List all registered schema names."""
        return list(self._schemas.keys())

    # =========================================================================
    # Auto-discovery
    # =========================================================================

    def discover_modules(self, package_path: str) -> int:
        """
        Auto-discover and register modules from a package.

        Looks for submodules with classes that inherit from AnalysisModule
        or VisualizationAdapter and auto-registers them.

        Args:
            package_path: Dotted package path (e.g., "framework.analysis")

        Returns:
            Number of modules discovered and registered
        """
        count = 0
        try:
            package = importlib.import_module(package_path)
        except ImportError:
            return 0

        if not hasattr(package, "__path__"):
            return 0

        for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
            try:
                module = importlib.import_module(f"{package_path}.{modname}")

                # Check for AnalysisModule subclasses
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, AnalysisModule)
                        and attr is not AnalysisModule
                    ):
                        name = getattr(attr, "name", attr.__name__.lower())
                        if name not in self._analysis_modules:
                            self._analysis_modules[name] = attr
                            count += 1

                    elif (
                        isinstance(attr, type)
                        and issubclass(attr, VisualizationAdapter)
                        and attr is not VisualizationAdapter
                    ):
                        name = getattr(attr, "name", attr.__name__.lower())
                        if name not in self._visualization_adapters:
                            self._visualization_adapters[name] = attr
                            count += 1

            except ImportError:
                continue

        return count

    def discover_domains(self, domains_dir: Path) -> int:
        """
        Auto-discover domain profiles from YAML files in a directory.

        Expected structure:
            domains_dir/
                military/
                    lexicon.yaml
                    patterns.yaml
                medical/
                    ...

        Args:
            domains_dir: Path to domains directory

        Returns:
            Number of domains discovered
        """
        # Import here to avoid circular dependency and yaml requirement at import time
        try:
            import yaml
        except ImportError:
            return 0

        from .ontology import DomainLexicon, EntityPattern, EntityPatternSet

        count = 0
        if not domains_dir.exists():
            return 0

        for domain_path in domains_dir.iterdir():
            if not domain_path.is_dir():
                continue

            domain_name = domain_path.name
            profile = DomainProfile(name=domain_name)

            # Load lexicon
            lexicon_file = domain_path / "lexicon.yaml"
            if lexicon_file.exists():
                with open(lexicon_file, "r", encoding="utf-8") as f:
                    lexicon_data = yaml.safe_load(f) or {}
                lex = DomainLexicon(
                    name=lexicon_data.get("name", f"{domain_name}_lexicon"),
                    terms=lexicon_data.get("terms", {}),
                    description=lexicon_data.get("description", ""),
                )
                profile.lexicons.append(lex)

            # Load patterns
            patterns_file = domain_path / "patterns.yaml"
            if patterns_file.exists():
                with open(patterns_file, "r", encoding="utf-8") as f:
                    patterns_data = yaml.safe_load(f) or {}
                patterns = []
                for label, pattern in patterns_data.get("patterns", {}).items():
                    patterns.append(EntityPattern(label=label, pattern=pattern))
                pattern_set = EntityPatternSet(
                    name=patterns_data.get("name", f"{domain_name}_patterns"),
                    patterns=patterns,
                    description=patterns_data.get("description", ""),
                )
                profile.entity_patterns.append(pattern_set)

            if profile.lexicons or profile.entity_patterns:
                self.register_domain(profile)
                count += 1

        return count

    # =========================================================================
    # Utilities
    # =========================================================================

    def clear(self) -> None:
        """Clear all registrations (except default schema)."""
        self._analysis_modules.clear()
        self._visualization_adapters.clear()
        self._domain_profiles.clear()
        self._schemas = {"default": AtomizationSchema.default()}

    def summary(self) -> Dict[str, List[str]]:
        """Return summary of all registered components."""
        return {
            "analysis_modules": self.list_analysis_modules(),
            "visualization_adapters": self.list_adapters(),
            "domain_profiles": self.list_domains(),
            "schemas": self.list_schemas(),
        }


# Global registry instance
registry = Registry()
