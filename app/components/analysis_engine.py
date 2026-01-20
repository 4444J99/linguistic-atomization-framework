"""
Analysis Engine - Wraps the framework analysis for Streamlit.
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
import sys


class AnalysisState(Enum):
    """Analysis workflow states."""
    READY = "ready"
    ANALYZING = "analyzing"
    COMPLETE = "complete"
    ERROR = "error"


def setup_framework():
    """Initialize framework and register components."""
    framework_root = Path(__file__).resolve().parent.parent.parent
    sys.path.insert(0, str(framework_root))

    from framework.core import registry
    from framework.domains import DOMAINS_DIR

    # Discover domains
    registry.discover_domains(DOMAINS_DIR)

    # Import analysis modules
    from framework.analysis import (
        SemanticAnalysis,
        TemporalAnalysis,
        SentimentAnalysis,
        EntityAnalysis,
        EvaluationAnalysis,
    )

    # Import visualization adapters
    from framework.visualization import (
        ForceGraphAdapter,
        SankeyAdapter,
        SentimentChartAdapter,
        EntityBrowserAdapter,
        EvaluationDashboardAdapter,
    )

    return registry


def run_analysis(
    text: str,
    document_title: str,
) -> Optional[Dict[str, Any]]:
    """
    Run analysis on the text and return results.

    Args:
        text: Document text to analyze
        document_title: Title for the document

    Returns:
        Dict containing analysis results, or None on error
    """
    try:
        from framework.core import Atomizer, AtomizationSchema, Corpus
        from framework.core.ontology import Document, AtomLevel

        # Setup framework
        registry = setup_framework()

        # Create atomization schema
        schema = AtomizationSchema.default()

        # Create atomizer
        atomizer = Atomizer(schema)
        atomizer._reset_counters()

        # Create document and atomize text
        doc = Document(
            id="doc-001",
            source_path=Path("uploaded-text"),
            format="plain",
            title=document_title,
        )

        # Start atomization from first level
        first_level = schema.levels[0]
        doc.root_atoms = atomizer.atomize_text(text, first_level)

        corpus = Corpus(
            name=document_title,
            documents=[doc],
            schema=schema,
        )

        # Get domain profile
        domain = registry.get_domain("base")

        results = {
            "corpus_stats": {
                "themes": corpus.count_atoms(AtomLevel.THEME),
                "paragraphs": corpus.count_atoms(AtomLevel.PARAGRAPH),
                "sentences": corpus.count_atoms(AtomLevel.SENTENCE),
                "words": len(text.split()),
            }
        }

        # Run evaluation analysis (primary)
        eval_module = registry.create_analysis("evaluation")
        eval_output = eval_module.analyze(corpus, domain, {})
        results["evaluation"] = eval_output.to_dict()

        # Run supplementary analyses
        try:
            semantic_module = registry.create_analysis("semantic")
            semantic_output = semantic_module.analyze(corpus, domain, {})
            results["semantic"] = semantic_output.to_dict()
        except Exception:
            pass  # Semantic analysis is optional

        try:
            sentiment_module = registry.create_analysis("sentiment")
            sentiment_output = sentiment_module.analyze(corpus, domain, {})
            results["sentiment"] = sentiment_output.to_dict()
        except Exception:
            pass  # Sentiment analysis is optional

        # Generate narrative report data
        from framework.output import NarrativeReportGenerator

        generator = NarrativeReportGenerator(include_icons=True)
        report = generator.generate(
            evaluation_data=results.get("evaluation", {}),
            document_title=document_title,
            additional_analyses={
                k: v for k, v in results.items()
                if k not in ("evaluation", "corpus_stats")
            },
        )
        results["narrative_report"] = report

        return results

    except Exception as e:
        import traceback
        traceback.print_exc()
        return None
