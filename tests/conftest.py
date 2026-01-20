"""
Pytest fixtures for LingFrame tests.
"""

import pytest
from datetime import datetime
from pathlib import Path
from framework.core.ontology import Corpus, Document, Atom, AtomLevel, AtomizationSchema
from framework.core.atomizer import Atomizer


def create_corpus_from_text(text: str, title: str = "Test Document") -> Corpus:
    """
    Helper function to create a corpus from raw text.

    Args:
        text: Source text to atomize
        title: Document title

    Returns:
        Corpus with atomized document
    """
    schema = AtomizationSchema(
        name="test",
        levels=[AtomLevel.THEME, AtomLevel.PARAGRAPH, AtomLevel.SENTENCE],
    )
    atomizer = Atomizer(schema)

    # Create document with a placeholder path for testing
    doc = Document(
        id=f"DOC_{abs(hash(title)) % 10000:04d}",
        source_path=Path(f"/tmp/test_{title.replace(' ', '_')}.txt"),
        format="plain",
        title=title,
    )

    # Atomize text starting from first level
    first_level = schema.levels[0]
    doc.root_atoms = atomizer.atomize_text(text, first_level)

    # Create corpus
    corpus = Corpus(
        name=title,
        documents=[doc],
        schema=schema,
        created_at=datetime.now(),
    )

    return corpus


@pytest.fixture
def sample_text_short():
    """Short sample text for quick tests."""
    return """
    The research demonstrates significant improvements. According to Smith (2023),
    results increased by 40%. However, some critics argue that methodology was flawed.
    Therefore, we must consider alternative approaches.
    """


@pytest.fixture
def sample_text_argumentative():
    """Longer argumentative text for comprehensive tests."""
    return """
    Climate change presents an urgent challenge for our generation. Scientists
    have documented a 1.1°C increase in global temperatures since pre-industrial
    times, with devastating consequences for ecosystems worldwide.

    The evidence is overwhelming. According to the IPCC (2023), greenhouse gas
    emissions must be reduced by 45% by 2030 to limit warming to 1.5°C. This
    requires immediate action from governments, businesses, and individuals.

    Critics argue that economic costs are too high. However, the cost of inaction
    far exceeds the cost of prevention. A study by the World Bank found that
    climate damage could reduce global GDP by 23% by 2100.

    Therefore, we must act now. First, governments should implement carbon pricing.
    Second, businesses must transition to renewable energy. Finally, individuals
    can reduce their carbon footprint through conscious choices.

    In conclusion, the climate crisis demands urgent collective action. The
    scientific evidence is clear, the solutions are available, and the time to
    act is now.
    """


@pytest.fixture
def sample_text_weak():
    """Text with intentional weaknesses for testing detection."""
    return """
    Things are really bad obviously. Everyone knows that stuff is wrong.
    People say it's going to get worse. Clearly, this is a terrible situation
    that we must fix immediately before it's too late.

    Some might disagree but they are wrong. The answer is simple and anyone
    can see it. We just need to do things differently.
    """


@pytest.fixture
def sample_text_emotional():
    """Text with high emotional content."""
    return """
    Imagine a world where every child goes to bed hungry. Feel the desperation
    of families struggling to survive. This heartbreaking reality affects
    millions of souls around the globe.

    We must act now! Together, united as one, we can end this suffering.
    Your help is urgently needed. Don't let another innocent child suffer
    while we stand by. The time for action is today!
    """


@pytest.fixture
def simple_corpus(sample_text_short):
    """Create a simple corpus from short sample text."""
    return create_corpus_from_text(sample_text_short, "Test Document")


@pytest.fixture
def argumentative_corpus(sample_text_argumentative):
    """Create a corpus from argumentative text."""
    return create_corpus_from_text(sample_text_argumentative, "Climate Argument")


@pytest.fixture
def weak_corpus(sample_text_weak):
    """Create a corpus from weak text."""
    return create_corpus_from_text(sample_text_weak, "Weak Text")


@pytest.fixture
def emotional_corpus(sample_text_emotional):
    """Create a corpus from emotional text."""
    return create_corpus_from_text(sample_text_emotional, "Emotional Appeal")


@pytest.fixture
def evaluation_module():
    """Create an evaluation analysis module."""
    from framework.analysis.evaluation import EvaluationAnalysis
    return EvaluationAnalysis()


@pytest.fixture
def suggestion_generator():
    """Create a suggestion generator."""
    from framework.generation.suggestions import SuggestionGenerator
    return SuggestionGenerator()


@pytest.fixture
def quick_win_extractor():
    """Create a quick win extractor."""
    from framework.generation.quick_wins import QuickWinExtractor
    return QuickWinExtractor()
