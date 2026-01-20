"""
Pipeline - Analysis orchestration system.

Coordinates the flow from source documents through atomization,
analysis modules, and visualization generation. Supports configuration
via YAML project files.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .atomizer import Atomizer
from .naming import OutputNaming, OutputNamingConfig
from .ontology import (
    AnalysisModule,
    AnalysisOutput,
    AtomizationSchema,
    Corpus,
    DomainProfile,
    VisualizationAdapter,
)
from .registry import Registry, registry as global_registry


@dataclass
class PipelineConfig:
    """
    Configuration for a complete analysis pipeline.

    Typically loaded from a project.yaml file.
    """
    project_name: str
    corpus_config: Dict[str, Any] = field(default_factory=dict)
    atomization_schema: str = "default"
    domain_profile: Optional[str] = None
    analysis_pipelines: List[Dict[str, Any]] = field(default_factory=list)
    visualization_adapters: List[Dict[str, Any]] = field(default_factory=list)
    output_dir: Path = field(default_factory=lambda: Path("data"))

    # Ontological naming configuration
    naming_strategy: str = "legacy"  # hierarchical | semantic | uuid | hybrid | legacy
    naming_config: Optional[Dict[str, Any]] = None
    output_naming_config: Optional[Dict[str, Any]] = None

    # Version tracking for output files
    version: str = "v1"

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_dir: Optional[Path] = None) -> PipelineConfig:
        """Create config from dictionary (e.g., parsed YAML)."""
        base = base_dir or Path(".")

        # Parse output directory
        output_dir = base / data.get("output_dir", "data")
        # Also check nested output config
        output_config = data.get("output", {})
        if "data_dir" in output_config:
            output_dir = base / output_config["data_dir"]

        # Parse corpus config
        corpus_config = data.get("corpus", {})
        if "documents" in corpus_config:
            # Resolve document paths relative to base_dir
            for doc in corpus_config["documents"]:
                if "source" in doc:
                    doc["source"] = str(base / doc["source"])

        # Parse naming configuration
        naming_config_data = data.get("naming", data.get("atomization", {}).get("naming", {}))
        naming_strategy = naming_config_data.get("strategy", "legacy")

        # Parse output naming configuration
        output_naming_data = data.get("output_naming", {})

        return cls(
            project_name=data.get("project", {}).get("name", "unnamed"),
            corpus_config=corpus_config,
            atomization_schema=data.get("atomization", {}).get("schema", "default"),
            domain_profile=data.get("domain", {}).get("profile"),
            analysis_pipelines=data.get("analysis", {}).get("pipelines", []),
            visualization_adapters=data.get("visualization", {}).get("adapters", []),
            output_dir=output_dir,
            naming_strategy=naming_strategy,
            naming_config=naming_config_data if naming_config_data else None,
            output_naming_config=output_naming_data if output_naming_data else None,
            version=data.get("version", data.get("project", {}).get("version", "v1")),
        )

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> PipelineConfig:
        """Load config from YAML file."""
        try:
            import yaml
        except ImportError:
            raise ImportError("PyYAML is required for YAML config loading. Run: pip install pyyaml")

        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return cls.from_dict(data, base_dir=yaml_path.parent)

    @property
    def output_naming(self) -> OutputNaming:
        """Get output naming system based on config."""
        if self.output_naming_config:
            config = OutputNamingConfig.from_dict(self.output_naming_config)
        else:
            config = OutputNamingConfig()
        return OutputNaming(config)

    @property
    def uses_ontological_naming(self) -> bool:
        """Check if config uses ontological naming (not legacy)."""
        return self.naming_strategy != "legacy"

    def get_output_filename(
        self,
        module_name: str,
        descriptor: Optional[str] = None,
        extension: str = "json",
    ) -> str:
        """
        Generate output filename for an analysis module.

        Args:
            module_name: Analysis module name (e.g., "semantic")
            descriptor: Optional content descriptor override
            extension: File extension

        Returns:
            Generated filename
        """
        if self.uses_ontological_naming or self.output_naming_config:
            return self.output_naming.generate_filename(
                project_name=self.project_name,
                module_name=module_name,
                descriptor=descriptor,
                version=self.version,
                extension=extension,
            )
        # Legacy naming
        return f"{module_name}_data.{extension}"


@dataclass
class PipelineResult:
    """Result of running a complete pipeline."""
    corpus: Corpus
    analyses: Dict[str, AnalysisOutput] = field(default_factory=dict)
    visualizations: Dict[str, Path] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


class Pipeline:
    """
    Analysis pipeline orchestrator.

    Coordinates the complete flow:
    1. Load/atomize corpus
    2. Run analysis modules
    3. Generate visualizations
    4. Export results
    """

    def __init__(
        self,
        config: Optional[PipelineConfig] = None,
        registry: Optional[Registry] = None,
    ):
        """
        Initialize pipeline.

        Args:
            config: Pipeline configuration
            registry: Registry instance (defaults to global registry)
        """
        self.config = config
        self.registry = registry or global_registry
        self._corpus: Optional[Corpus] = None
        self._domain: Optional[DomainProfile] = None
        self._analyses: Dict[str, AnalysisOutput] = {}

    def load_corpus(
        self,
        source: Optional[Path] = None,
        atomize: bool = True,
    ) -> Corpus:
        """
        Load or atomize the corpus.

        Args:
            source: Path to source document or pre-atomized JSON
            atomize: If True, atomize source; if False, load pre-atomized JSON

        Returns:
            Loaded Corpus
        """
        if source and source.suffix == ".json" and not atomize:
            # Load pre-atomized
            self._corpus = Atomizer.load_json(source)
            return self._corpus

        # Get schema
        schema_name = self.config.atomization_schema if self.config else "default"
        schema = self.registry.get_schema(schema_name) or AtomizationSchema.default()

        # Apply ontological naming configuration if specified in config
        if self.config and self.config.naming_strategy != "legacy":
            schema.naming_strategy = self.config.naming_strategy
            if self.config.naming_config:
                schema.naming_config = self.config.naming_config

        atomizer = Atomizer(schema)

        if source:
            # Single document
            doc = atomizer.atomize_document(source)
            self._corpus = Corpus(
                name=source.stem,
                documents=[doc],
                schema=schema,
            )
        elif self.config and self.config.corpus_config.get("documents"):
            # Multiple documents from config
            docs_config = self.config.corpus_config["documents"]
            self._corpus = atomizer.atomize_corpus(
                name=self.config.project_name,
                document_configs=docs_config,
            )
        else:
            raise ValueError("No source document or corpus config provided")

        return self._corpus

    def load_domain(self, profile_name: Optional[str] = None) -> Optional[DomainProfile]:
        """
        Load domain profile.

        Args:
            profile_name: Name of profile in registry (or from config)

        Returns:
            DomainProfile or None
        """
        name = profile_name or (self.config.domain_profile if self.config else None)
        if name:
            self._domain = self.registry.get_domain(name)
        return self._domain

    def run_analysis(
        self,
        module_name: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run a single analysis module.

        Args:
            module_name: Name of registered analysis module
            config: Optional module-specific configuration

        Returns:
            AnalysisOutput from the module
        """
        if self._corpus is None:
            raise RuntimeError("Corpus not loaded. Call load_corpus() first.")

        module = self.registry.create_analysis(module_name)
        output = module.analyze(self._corpus, self._domain, config)

        self._analyses[module_name] = output
        return output

    def run_all_analyses(self) -> Dict[str, AnalysisOutput]:
        """
        Run all analysis modules defined in config.

        Returns:
            Dict mapping module names to their outputs
        """
        if not self.config or not self.config.analysis_pipelines:
            return {}

        for pipeline_config in self.config.analysis_pipelines:
            module_name = pipeline_config.get("module")
            if module_name:
                module_config = pipeline_config.get("config", {})
                try:
                    self.run_analysis(module_name, module_config)
                except KeyError as e:
                    print(f"Warning: {e}")

        return self._analyses

    def generate_visualization(
        self,
        adapter_name: str,
        analysis_name: str,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate a visualization for an analysis output.

        Args:
            adapter_name: Name of registered visualization adapter
            analysis_name: Name of analysis to visualize
            output_path: Path for output file
            config: Optional adapter-specific configuration

        Returns:
            Path to generated visualization
        """
        if analysis_name not in self._analyses:
            raise ValueError(f"Analysis '{analysis_name}' not found. Run analysis first.")

        analysis = self._analyses[analysis_name]
        adapter = self.registry.create_adapter(adapter_name)

        return adapter.generate(analysis, output_path, config)

    def export_analysis(
        self,
        analysis_name: str,
        output_path: Path,
        indent: int = 2,
    ) -> Path:
        """
        Export analysis results to JSON.

        Args:
            analysis_name: Name of analysis to export
            output_path: Destination file path
            indent: JSON indentation

        Returns:
            Path to exported file
        """
        if analysis_name not in self._analyses:
            raise ValueError(f"Analysis '{analysis_name}' not found.")

        analysis = self._analyses[analysis_name]
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis.to_dict(), f, indent=indent, ensure_ascii=False)

        return output_path

    def export_all_analyses(
        self,
        output_dir: Optional[Path] = None,
        use_ontological_naming: Optional[bool] = None,
    ) -> Dict[str, Path]:
        """
        Export all analysis results to JSON files.

        Args:
            output_dir: Directory for output files (defaults to config output_dir)
            use_ontological_naming: Override for ontological naming (defaults to config)

        Returns:
            Dict mapping analysis names to output paths
        """
        out_dir = output_dir or (self.config.output_dir / "processed" if self.config else Path("data/processed"))
        out_dir.mkdir(parents=True, exist_ok=True)

        # Determine naming mode
        ontological = use_ontological_naming
        if ontological is None and self.config:
            ontological = self.config.uses_ontological_naming or bool(self.config.output_naming_config)

        paths = {}
        for name, analysis in self._analyses.items():
            if ontological and self.config:
                # Use ontological naming
                filename = self.config.get_output_filename(name)
                output_path = out_dir / filename
            else:
                # Legacy naming
                output_path = out_dir / f"{name}_data.json"

            paths[name] = self.export_analysis(name, output_path)

        return paths

    def run(
        self,
        source: Optional[Path] = None,
        export: bool = True,
        visualize: bool = False,
        verbose: bool = False,
    ) -> PipelineResult:
        """
        Run the complete pipeline.

        Args:
            source: Optional source document (overrides config)
            export: Export analysis results to JSON
            visualize: Generate visualizations
            verbose: Print progress messages

        Returns:
            PipelineResult with all outputs
        """
        result = PipelineResult(corpus=Corpus(name=""))
        result.started_at = datetime.now()

        # Step 1: Load corpus
        if verbose:
            print("Loading/atomizing corpus...")

        if source:
            atomize = source.suffix != ".json"
            result.corpus = self.load_corpus(source, atomize=atomize)
        elif self.config:
            result.corpus = self.load_corpus()
        else:
            raise ValueError("No source or config provided")

        if verbose:
            print(f"  Corpus: {result.corpus.name}")
            print(f"  Documents: {result.corpus.total_documents}")

        # Step 2: Load domain
        if verbose:
            print("Loading domain profile...")
        self.load_domain()
        if self._domain and verbose:
            print(f"  Domain: {self._domain.name}")

        # Step 3: Run analyses
        if verbose:
            print("Running analyses...")

        if self.config and self.config.analysis_pipelines:
            result.analyses = self.run_all_analyses()
        if verbose:
            print(f"  Completed: {list(result.analyses.keys())}")

        # Step 4: Export
        if export:
            if verbose:
                print("Exporting results...")
            output_paths = self.export_all_analyses()
            result.metadata["exported_files"] = {k: str(v) for k, v in output_paths.items()}

            # Also export atomized corpus
            if self.config:
                corpus_path = self.config.output_dir / "raw" / f"{self.config.project_name}_atomized.json"
            else:
                corpus_path = Path("data/raw/corpus_atomized.json")
            corpus_path.parent.mkdir(parents=True, exist_ok=True)

            atomizer = Atomizer()
            atomizer.export_json(result.corpus, corpus_path)
            result.metadata["corpus_file"] = str(corpus_path)

        # Step 5: Generate visualizations
        if visualize and self.config and self.config.visualization_adapters:
            if verbose:
                print("Generating visualizations...")
            vis_dir = self.config.output_dir.parent / "visualizations"
            vis_dir.mkdir(parents=True, exist_ok=True)

            for viz_config in self.config.visualization_adapters:
                adapter_type = viz_config.get("type")
                analysis_name = viz_config.get("analysis")
                if adapter_type and analysis_name and analysis_name in result.analyses:
                    try:
                        output_path = vis_dir / f"{analysis_name}_{adapter_type}.html"
                        path = self.generate_visualization(
                            adapter_type,
                            analysis_name,
                            output_path,
                            viz_config.get("config"),
                        )
                        result.visualizations[f"{analysis_name}_{adapter_type}"] = path
                    except KeyError as e:
                        if verbose:
                            print(f"  Warning: {e}")

        result.completed_at = datetime.now()
        if verbose:
            print(f"Pipeline completed in {result.duration_seconds:.2f}s")

        return result

    @property
    def corpus(self) -> Optional[Corpus]:
        """Get the loaded corpus."""
        return self._corpus

    @property
    def analyses(self) -> Dict[str, AnalysisOutput]:
        """Get all completed analyses."""
        return self._analyses.copy()
