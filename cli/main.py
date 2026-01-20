#!/usr/bin/env python3
"""
CLI Main Entry Point - Command-line interface for the framework.

Usage:
    lingframe run --project tomb-of-the-unknowns
    lingframe atomize --project tomb-of-the-unknowns
    lingframe analyze --project tomb-of-the-unknowns --module semantic
    lingframe visualize --project tomb-of-the-unknowns
    lingframe list-modules
    lingframe list-projects
    lingframe migrate --project tomb-of-the-unknowns --category literary-analysis --naming hybrid
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def get_framework_root() -> Path:
    """Get the framework root directory."""
    return Path(__file__).resolve().parent.parent


def get_projects_dir() -> Path:
    """Get the projects directory."""
    return get_framework_root() / "projects"


def load_categories() -> Dict[str, Any]:
    """Load project categories configuration."""
    categories_path = get_projects_dir() / ".categories.yaml"
    if not categories_path.exists():
        return {"categories": {}, "aliases": {}, "default_category": "literary-analysis"}

    try:
        import yaml
        with open(categories_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        return {"categories": {}, "aliases": {}, "default_category": "literary-analysis"}


def resolve_category(category: str) -> str:
    """Resolve category alias to full category name."""
    cats = load_categories()
    aliases = cats.get("aliases", {})
    return aliases.get(category, category)


def find_project_path(project_name: str) -> Optional[Path]:
    """
    Find project directory, checking both flat and category-based structures.

    Args:
        project_name: Project name or category/project path

    Returns:
        Path to project directory or None if not found
    """
    projects_dir = get_projects_dir()

    # Check if it's a category/project path
    if "/" in project_name:
        parts = project_name.split("/", 1)
        category = resolve_category(parts[0])
        proj_name = parts[1]
        project_path = projects_dir / category / proj_name
        if project_path.exists() and (project_path / "project.yaml").exists():
            return project_path

    # Check flat structure first
    flat_path = projects_dir / project_name
    if flat_path.exists() and (flat_path / "project.yaml").exists():
        return flat_path

    # Search in category directories
    for category_dir in projects_dir.iterdir():
        if category_dir.is_dir() and not category_dir.name.startswith("."):
            project_path = category_dir / project_name
            if project_path.exists() and (project_path / "project.yaml").exists():
                return project_path

    return None


def load_project_config(project_name: str) -> Tuple[dict, Path]:
    """
    Load project configuration from YAML.

    Args:
        project_name: Project name or category/project path

    Returns:
        Tuple of (config dict, project directory path)
    """
    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required. Run: pip install pyyaml")
        sys.exit(1)

    project_dir = find_project_path(project_name)
    if project_dir is None:
        print(f"Error: Project not found: {project_name}")
        print("Use 'lingframe list-projects' to see available projects.")
        sys.exit(1)

    config_path = project_dir / "project.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f), project_dir


def get_project_dir(project_name: str) -> Path:
    """Get project directory path (for backward compatibility)."""
    project_dir = find_project_path(project_name)
    if project_dir is None:
        # Fall back to legacy flat structure
        return get_projects_dir() / project_name
    return project_dir


def setup_framework():
    """Initialize framework and register components."""
    # Add framework to path
    framework_root = get_framework_root()
    sys.path.insert(0, str(framework_root))

    # Import and setup
    from framework.core import registry
    from framework.domains import DOMAINS_DIR

    # Discover domains
    registry.discover_domains(DOMAINS_DIR)

    # Import analysis modules to trigger registration
    from framework.analysis import (
        SemanticAnalysis,
        TemporalAnalysis,
        SentimentAnalysis,
        EntityAnalysis,
        EvaluationAnalysis,
    )

    # Import visualization adapters to trigger registration
    from framework.visualization import (
        ForceGraphAdapter,
        SankeyAdapter,
        SentimentChartAdapter,
        EntityBrowserAdapter,
        EvaluationDashboardAdapter,
    )

    return registry


def cmd_run(args: argparse.Namespace) -> int:
    """Run complete pipeline for a project."""
    print(f"Running pipeline for project: {args.project}")
    print("=" * 60)

    config, project_dir = load_project_config(args.project)
    reg = setup_framework()

    from framework.core import Pipeline, PipelineConfig

    # Create pipeline config
    pipeline_config = PipelineConfig.from_dict(config, base_dir=project_dir)

    # Run pipeline
    pipeline = Pipeline(config=pipeline_config, registry=reg)
    result = pipeline.run(
        export=True,
        visualize=args.visualize,
        verbose=args.verbose,
    )

    print("\nPipeline completed!")
    print(f"  Duration: {result.duration_seconds:.2f}s")
    print(f"  Analyses: {list(result.analyses.keys())}")

    if result.visualizations:
        print(f"  Visualizations: {list(result.visualizations.keys())}")

    return 0


def cmd_atomize(args: argparse.Namespace) -> int:
    """Atomize documents for a project."""
    print(f"Atomizing documents for project: {args.project}")
    print("=" * 60)

    config, project_dir = load_project_config(args.project)
    setup_framework()

    from framework.core import Atomizer, AtomizationSchema

    # Get schema with naming configuration
    schema_name = config.get("atomization", {}).get("schema", "default")
    schema = AtomizationSchema.default()

    # Apply naming configuration from project config
    naming_config = config.get("naming", {})
    if naming_config:
        strategy = naming_config.get("strategy", "legacy")
        schema.naming_strategy = strategy
        if strategy != "legacy":
            schema.naming_config = naming_config
            print(f"  Using naming strategy: {strategy}")

    atomizer = Atomizer(schema)

    # Process documents
    docs_config = config.get("corpus", {}).get("documents", [])
    for doc_config in docs_config:
        source = project_dir / doc_config["source"]
        print(f"\nAtomizing: {source}")

        doc = atomizer.atomize_document(
            source_path=source,
            document_id=doc_config.get("id"),
            title=doc_config.get("title"),
            author=doc_config.get("author"),
        )

        # Create corpus and export
        from framework.core import Corpus

        corpus = Corpus(
            name=doc_config.get("title", args.project),
            documents=[doc],
            schema=schema,
        )

        output_dir = project_dir / config.get("output", {}).get("raw_dir", "data/raw")
        # Use project directory name (not full path) for output filename
        project_name = project_dir.name
        output_path = output_dir / f"{project_name}_atomized.json"

        atomizer.export_json(corpus, output_path)
        print(f"Exported: {output_path}")

        # Show stats
        from framework.core.ontology import AtomLevel

        print(f"  Themes: {corpus.count_atoms(AtomLevel.THEME)}")
        print(f"  Paragraphs: {corpus.count_atoms(AtomLevel.PARAGRAPH)}")
        print(f"  Sentences: {corpus.count_atoms(AtomLevel.SENTENCE)}")
        print(f"  Words: {corpus.count_atoms(AtomLevel.WORD)}")

    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run analysis modules for a project."""
    print(f"Running analysis for project: {args.project}")
    print("=" * 60)

    config, project_dir = load_project_config(args.project)
    reg = setup_framework()

    from framework.core import Atomizer, Pipeline

    # Load atomized corpus
    raw_dir = project_dir / config.get("output", {}).get("raw_dir", "data/raw")
    # Use project directory name (not full path) for filename
    project_name = project_dir.name
    corpus_path = raw_dir / f"{project_name}_atomized.json"

    if not corpus_path.exists():
        print(f"Error: Atomized corpus not found: {corpus_path}")
        print("Run 'lingframe atomize' first.")
        return 1

    corpus = Atomizer.load_json(corpus_path)
    print(f"Loaded corpus: {corpus.name}")

    # Load domain profile
    domain_name = config.get("domain", {}).get("profile")
    domain = reg.get_domain(domain_name) if domain_name else None
    if domain:
        print(f"Using domain: {domain.name}")

    # Get modules to run
    if args.module:
        modules_to_run = [{"module": args.module}]
    else:
        modules_to_run = config.get("analysis", {}).get("pipelines", [])

    # Run analyses
    processed_dir = project_dir / config.get("output", {}).get("processed_dir", "data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)

    for pipeline_config in modules_to_run:
        module_name = pipeline_config.get("module")
        module_config = pipeline_config.get("config", {})

        print(f"\nRunning: {module_name}")

        try:
            module = reg.create_analysis(module_name)
            output = module.analyze(corpus, domain, module_config)

            # Export
            output_path = processed_dir / f"{module_name}_data.json"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output.to_dict(), f, indent=2, ensure_ascii=False)

            print(f"  Exported: {output_path}")

        except KeyError as e:
            print(f"  Error: {e}")

    return 0


def cmd_visualize(args: argparse.Namespace) -> int:
    """Generate visualizations for a project."""
    print(f"Generating visualizations for project: {args.project}")
    print("=" * 60)

    config, project_dir = load_project_config(args.project)
    reg = setup_framework()

    from framework.core.ontology import AnalysisOutput

    processed_dir = project_dir / config.get("output", {}).get("processed_dir", "data/processed")
    viz_dir = project_dir / config.get("output", {}).get("visualizations_dir", "visualizations")
    viz_dir.mkdir(parents=True, exist_ok=True)

    # Get adapters to run
    adapters_config = config.get("visualization", {}).get("adapters", [])

    for adapter_config in adapters_config:
        adapter_type = adapter_config.get("type")
        analysis_name = adapter_config.get("analysis")
        viz_config = adapter_config.get("config", {})

        # Load analysis data
        analysis_path = processed_dir / f"{analysis_name}_data.json"
        if not analysis_path.exists():
            print(f"Skipping {adapter_type}: analysis data not found ({analysis_path})")
            continue

        with open(analysis_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        analysis = AnalysisOutput(
            module_name=data.get("module", analysis_name),
            data=data,
            metadata=data.get("metadata", {}),
        )

        print(f"\nGenerating: {adapter_type} for {analysis_name}")

        try:
            adapter = reg.create_adapter(adapter_type)
            output_path = viz_dir / f"{analysis_name}_{adapter_type}.html"
            adapter.generate(analysis, output_path, viz_config)
            print(f"  Created: {output_path}")

        except KeyError as e:
            print(f"  Error: {e}")

    return 0


def cmd_list_modules(args: argparse.Namespace) -> int:
    """List available modules and adapters."""
    reg = setup_framework()

    summary = reg.summary()

    print("Available Analysis Modules:")
    for name in summary["analysis_modules"]:
        print(f"  - {name}")

    print("\nAvailable Visualization Adapters:")
    for name in summary["visualization_adapters"]:
        print(f"  - {name}")

    print("\nAvailable Domain Profiles:")
    for name in summary["domain_profiles"]:
        print(f"  - {name}")

    print("\nAvailable Schemas:")
    for name in summary["schemas"]:
        print(f"  - {name}")

    return 0


def cmd_list_projects(args: argparse.Namespace) -> int:
    """List available projects."""
    projects_dir = get_projects_dir()
    categories = load_categories().get("categories", {})

    print("Available Projects:")
    print()

    # First, list flat projects (not in categories)
    flat_projects = []
    for project_path in projects_dir.iterdir():
        if project_path.is_dir() and (project_path / "project.yaml").exists():
            flat_projects.append(project_path.name)

    if flat_projects:
        print("  [Uncategorized]")
        for name in sorted(flat_projects):
            print(f"    - {name}")
        print()

    # Then list category-based projects
    for category_name in sorted(categories.keys()):
        category_dir = projects_dir / category_name
        if not category_dir.exists():
            continue

        category_projects = []
        for project_path in category_dir.iterdir():
            if project_path.is_dir() and (project_path / "project.yaml").exists():
                category_projects.append(project_path.name)

        if category_projects:
            desc = categories.get(category_name, {}).get("description", "")
            print(f"  [{category_name}] {desc}")
            for name in sorted(category_projects):
                print(f"    - {category_name}/{name}")
            print()

    return 0


def cmd_list_categories(args: argparse.Namespace) -> int:
    """List available project categories."""
    categories_data = load_categories()
    categories = categories_data.get("categories", {})
    aliases = categories_data.get("aliases", {})

    print("Available Categories:")
    print()

    for name, info in sorted(categories.items()):
        desc = info.get("description", "")
        domains = info.get("domains", [])
        print(f"  {name}")
        if desc:
            print(f"    Description: {desc}")
        if domains:
            print(f"    Domains: {', '.join(domains[:5])}{'...' if len(domains) > 5 else ''}")
        print()

    if aliases:
        print("Aliases:")
        for alias, full_name in sorted(aliases.items()):
            print(f"  {alias} -> {full_name}")

    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    """Migrate existing project to ontological naming."""
    print(f"Migrating project: {args.project}")
    print("=" * 60)

    try:
        import yaml
    except ImportError:
        print("Error: PyYAML is required. Run: pip install pyyaml")
        return 1

    projects_dir = get_projects_dir()
    source_dir = find_project_path(args.project)

    if source_dir is None:
        print(f"Error: Project not found: {args.project}")
        return 1

    # Determine target category and name
    category = resolve_category(args.category) if args.category else None
    new_name = args.new_name or source_dir.name

    # Shorten name if requested
    if args.shorten:
        # Remove common suffixes and convert to shorter form
        new_name = re.sub(r'-of-the-|-of-|-the-', '-', new_name)
        new_name = re.sub(r'^the-', '', new_name)
        new_name = new_name.strip('-')

    # Determine target directory
    if category:
        target_dir = projects_dir / category / new_name
    else:
        target_dir = projects_dir / new_name

    print(f"  Source: {source_dir}")
    print(f"  Target: {target_dir}")
    print(f"  Naming strategy: {args.naming}")

    if target_dir.exists() and target_dir != source_dir:
        print(f"Error: Target directory already exists: {target_dir}")
        return 1

    # Load and update project config
    config_path = source_dir / "project.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Update naming configuration
    if "naming" not in config:
        config["naming"] = {}
    config["naming"]["strategy"] = args.naming

    # Update project name if changed
    if new_name != source_dir.name:
        if "project" not in config:
            config["project"] = {}
        config["project"]["name"] = new_name

    # Add migration metadata
    if "metadata" not in config:
        config["metadata"] = {}
    config["metadata"]["migrated_from"] = str(source_dir.name)
    config["metadata"]["migrated_at"] = datetime.now().isoformat()
    config["metadata"]["naming_strategy"] = args.naming

    if args.dry_run:
        print("\n[DRY RUN] Would perform the following changes:")
        print(f"  - Move {source_dir} -> {target_dir}")
        print(f"  - Update project.yaml with naming.strategy = {args.naming}")
        if args.re_atomize:
            print("  - Re-atomize documents with new naming")
        return 0

    # Create category directory if needed
    if category:
        (projects_dir / category).mkdir(parents=True, exist_ok=True)

    # Move or copy project
    if target_dir != source_dir:
        print(f"\nMoving project to {target_dir}...")
        shutil.move(str(source_dir), str(target_dir))
    else:
        print("\nUpdating project in place...")

    # Write updated config
    config_path = target_dir / "project.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    print(f"  Updated: {config_path}")

    # Re-atomize if requested
    if args.re_atomize:
        print("\nRe-atomizing with new naming strategy...")
        # Use the project name that lingframe commands expect
        if category:
            project_ref = f"{category}/{new_name}"
        else:
            project_ref = new_name

        # Call atomize command
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "cli.main", "atomize", "-p", project_ref],
            cwd=get_framework_root(),
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  Warning: Re-atomization failed: {result.stderr}")
        else:
            print("  Re-atomization complete")

    print("\nMigration complete!")
    if category:
        print(f"  New project path: {category}/{new_name}")
    else:
        print(f"  New project path: {new_name}")

    return 0


def cmd_init_notebooks(args: argparse.Namespace) -> int:
    """Initialize Jupyter notebooks for a project."""
    print(f"Initializing notebooks for project: {args.project}")
    print("=" * 60)

    project_dir = find_project_path(args.project)
    if project_dir is None:
        print(f"Error: Project not found: {args.project}")
        return 1

    # Import notebook templates
    from framework.notebooks import TEMPLATES_DIR, AVAILABLE_TEMPLATES

    # Create notebooks directory
    notebooks_dir = project_dir / "notebooks"
    notebooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy templates
    copied = []
    skipped = []

    for template_name in AVAILABLE_TEMPLATES:
        source = TEMPLATES_DIR / template_name
        dest = notebooks_dir / template_name

        if dest.exists() and not args.force:
            skipped.append(template_name)
            continue

        if source.exists():
            shutil.copy2(source, dest)
            copied.append(template_name)
            print(f"  Created: {dest}")

    if skipped:
        print(f"\nSkipped (already exist): {', '.join(skipped)}")
        print("  Use --force to overwrite")

    print(f"\n✅ Notebooks initialized: {notebooks_dir}")
    print("\nAvailable notebooks:")
    for name in AVAILABLE_TEMPLATES:
        print(f"  - {name}")

    print("\nTo use:")
    print(f"  cd {notebooks_dir}")
    print("  jupyter notebook")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        prog="lingframe",
        description="Linguistic Analysis Framework CLI",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # run command
    run_parser = subparsers.add_parser("run", help="Run complete pipeline")
    run_parser.add_argument("--project", "-p", required=True, help="Project name")
    run_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    run_parser.add_argument("--visualize", action="store_true", help="Generate visualizations")
    run_parser.set_defaults(func=cmd_run)

    # atomize command
    atomize_parser = subparsers.add_parser("atomize", help="Atomize documents")
    atomize_parser.add_argument("--project", "-p", required=True, help="Project name")
    atomize_parser.set_defaults(func=cmd_atomize)

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Run analysis")
    analyze_parser.add_argument("--project", "-p", required=True, help="Project name")
    analyze_parser.add_argument("--module", "-m", help="Specific module to run")
    analyze_parser.set_defaults(func=cmd_analyze)

    # visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate visualizations")
    viz_parser.add_argument("--project", "-p", required=True, help="Project name")
    viz_parser.set_defaults(func=cmd_visualize)

    # list-modules command
    list_parser = subparsers.add_parser("list-modules", help="List available modules")
    list_parser.set_defaults(func=cmd_list_modules)

    # list-projects command
    projects_parser = subparsers.add_parser("list-projects", help="List available projects")
    projects_parser.set_defaults(func=cmd_list_projects)

    # list-categories command
    categories_parser = subparsers.add_parser("list-categories", help="List project categories")
    categories_parser.set_defaults(func=cmd_list_categories)

    # migrate command
    migrate_parser = subparsers.add_parser(
        "migrate",
        help="Migrate project to ontological naming",
        description="Migrate an existing project to use ontological naming and/or move to a category."
    )
    migrate_parser.add_argument(
        "--project", "-p",
        required=True,
        help="Project name to migrate"
    )
    migrate_parser.add_argument(
        "--category", "-c",
        help="Target category (e.g., literary-analysis)"
    )
    migrate_parser.add_argument(
        "--naming", "-n",
        choices=["legacy", "hierarchical", "semantic", "uuid", "hybrid"],
        default="hybrid",
        help="Naming strategy (default: hybrid)"
    )
    migrate_parser.add_argument(
        "--new-name",
        help="New project name (optional)"
    )
    migrate_parser.add_argument(
        "--shorten",
        action="store_true",
        help="Automatically shorten project name (e.g., tomb-of-the-unknowns -> tomb-unknowns)"
    )
    migrate_parser.add_argument(
        "--re-atomize",
        action="store_true",
        help="Re-atomize documents with new naming strategy"
    )
    migrate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes"
    )
    migrate_parser.set_defaults(func=cmd_migrate)

    # init-notebooks command
    notebooks_parser = subparsers.add_parser(
        "init-notebooks",
        help="Initialize Jupyter notebooks for a project",
        description="Copy notebook templates to a project's notebooks/ directory."
    )
    notebooks_parser.add_argument(
        "--project", "-p",
        required=True,
        help="Project name"
    )
    notebooks_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing notebooks"
    )
    notebooks_parser.set_defaults(func=cmd_init_notebooks)

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
