# Contributing to LingFrame

Thank you for your interest in contributing to LingFrame! This document provides guidelines for contributing to the project.

---

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Setup](#development-setup)
4. [Project Architecture](#project-architecture)
5. [Contribution Types](#contribution-types)
6. [Coding Standards](#coding-standards)
7. [Testing](#testing)
8. [Documentation](#documentation)
9. [Pull Request Process](#pull-request-process)

---

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Acknowledge the heuristic nature of analysis (avoid overclaiming)
- Prioritize scholarly accuracy over marketing appeal

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git
- Familiarity with linguistic analysis concepts

### Quick Setup

```bash
# Clone the repository
git clone <repo-url>
cd linguistic-atomization-framework

# Create virtual environment
python3 -m venv new_venv
source new_venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# Install NLP models
python -m spacy download en_core_web_sm
```

### Verify Setup

```bash
# Run the CLI
python lingframe.py --help

# Run a quick analysis
python lingframe.py quick docs/sample.txt
```

---

## Development Setup

### Directory Structure

```
linguistic-atomization-framework/
├── framework/              # Core framework code
│   ├── core/               # Ontology, atomization, naming
│   ├── analysis/           # Analysis modules
│   ├── visualization/      # Visualization adapters
│   ├── output/             # Report formatters
│   ├── generation/         # Revision suggestions (planned)
│   ├── domains/            # Domain profiles
│   └── llm/                # LLM integration
├── app/                    # Streamlit web interface
├── cli/                    # Command-line interfaces
├── tests/                  # Test suite
├── docs/                   # Documentation
└── projects/               # Sample analysis projects
```

### Key Files

| File | Purpose |
|------|---------|
| `framework/core/ontology.py` | Core data structures (Atom, Corpus, etc.) |
| `framework/core/atomizer.py` | Text atomization engine |
| `framework/core/registry.py` | Component registration system |
| `framework/analysis/base.py` | Base class for analysis modules |
| `framework/visualization/base.py` | Base class for visualizations |

---

## Project Architecture

### Core Concepts

**Atoms**: Hierarchical text units (Theme → Paragraph → Sentence → Word → Letter)

**Corpus**: Collection of atoms with metadata

**Analysis Module**: Component that analyzes a corpus and produces structured output

**Visualization Adapter**: Component that transforms analysis output into visual format

**Domain Profile**: Domain-specific lexicons and patterns

### Registry System

All components register with the global registry:

```python
from framework.core.registry import registry

@registry.register_analysis("my_analysis")
class MyAnalysis(BaseAnalysisModule):
    ...

@registry.register_adapter("my_viz")
class MyVizAdapter(BaseVisualizationAdapter):
    ...
```

---

## Contribution Types

### 1. Analysis Modules

Add new analysis capabilities:

```python
# framework/analysis/my_analysis.py
from framework.analysis.base import BaseAnalysisModule
from framework.core.registry import registry
from framework.core.ontology import AnalysisOutput, Corpus, DomainProfile

@registry.register_analysis("my_analysis")
class MyAnalysis(BaseAnalysisModule):
    """
    Brief description of what this analyzes.

    NOTE: Document methodology and limitations.
    """

    name = "my_analysis"
    description = "Short description for registry"

    def analyze(
        self,
        corpus: Corpus,
        domain: DomainProfile,
        config: dict
    ) -> AnalysisOutput:
        # Your analysis logic
        data = self._perform_analysis(corpus)

        return self.make_output(
            data=data,
            summary={"key_metric": value}
        )

    def _perform_analysis(self, corpus: Corpus) -> dict:
        # Use self.iter_atoms() to traverse the hierarchy
        for level, atom in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            # Process each atom
            pass
        return results
```

### 2. Visualization Adapters

Add new visualization types:

```python
# framework/visualization/adapters/my_viz.py
from framework.visualization.base import BaseVisualizationAdapter
from framework.core.registry import registry

@registry.register_adapter("my_viz")
class MyVizAdapter(BaseVisualizationAdapter):
    """Interactive visualization for my_analysis results."""

    name = "my_viz"
    description = "Description for registry"
    supported_analysis = ["my_analysis"]

    def generate(
        self,
        analysis_output: AnalysisOutput,
        config: dict
    ) -> str:
        data = analysis_output.data
        return self._render_template("my_viz.html", data=data)
```

### 3. Domain Profiles

Add domain-specific customization:

```yaml
# framework/domains/legal/lexicon.yaml
formal_terms:
  whereas: 0.3
  hereby: 0.2
  pursuant: 0.1
  notwithstanding: 0.2

# framework/domains/legal/patterns.yaml
entities:
  case_citation:
    pattern: '\d+\s+[A-Z][a-z]+\.?\s+\d+'
    label: LEGAL_CITATION
  statute:
    pattern: '\d+\s+U\.S\.C\.\s+§?\s*\d+'
    label: STATUTE
```

### 4. Bug Fixes

- Describe the bug clearly
- Include steps to reproduce
- Provide a minimal test case if possible
- Reference related issues

### 5. Documentation

- Fix typos and clarify explanations
- Add examples and use cases
- Update theoretical documentation
- Improve API documentation

### 6. Tests

- Add unit tests for analysis modules
- Add integration tests for pipelines
- Add validation tests against expected outputs

---

## Coding Standards

### Style

- Follow PEP 8 for Python code
- Use type hints for function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and small

### Documentation Requirements

Every analysis module must document:

1. **What it analyzes**: Clear description of the analysis focus
2. **Methodology**: How the analysis works (patterns, algorithms)
3. **Limitations**: What the analysis cannot do
4. **Output format**: Structure of the returned data

Example:

```python
class MyAnalysis(BaseAnalysisModule):
    """
    Analyzes X in text using Y methodology.

    Methodology:
    - Pattern matching against predefined list of Z markers
    - Density calculation at sentence and paragraph levels
    - Aggregation using weighted averaging

    Limitations:
    - Cannot detect contextual usage
    - May produce false positives for X
    - English-only

    Output:
    - data["findings"]: List of detected patterns
    - data["metrics"]: Density calculations by level
    - summary["total_count"]: Total pattern count
    """
```

### Honest Claims

LingFrame prioritizes scholarly accuracy. When writing documentation:

- Use "detects patterns" not "understands"
- Use "heuristic indicator" not "measurement"
- Acknowledge limitations explicitly
- Avoid overclaiming capabilities

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_evaluation.py

# Run with coverage
pytest --cov=framework tests/
```

### Writing Tests

```python
# tests/test_my_analysis.py
import pytest
from framework.analysis.my_analysis import MyAnalysis
from framework.core.ontology import Corpus

class TestMyAnalysis:
    def setup_method(self):
        self.module = MyAnalysis()

    def test_basic_analysis(self):
        corpus = self._create_test_corpus("Sample text")
        result = self.module.analyze(corpus, domain=None, config={})

        assert result is not None
        assert "findings" in result.data

    def test_edge_case_empty_text(self):
        corpus = self._create_test_corpus("")
        result = self.module.analyze(corpus, domain=None, config={})

        assert result.data["findings"] == []
```

---

## Documentation

### Types of Documentation

1. **Code docstrings**: Inline documentation for functions/classes
2. **README.md**: User-facing overview and quick start
3. **CLAUDE.md**: Developer guide for AI assistants
4. **docs/**: Extended documentation
   - `theory.md`: Theoretical foundation
   - `limitations.md`: Scope and limitations
   - `methodology.md`: Detailed methodology

### Documentation Standards

- Write for the reader (scholars, developers, or both)
- Include examples
- Link to related documentation
- Keep theoretical claims honest

---

## Pull Request Process

### Before Submitting

1. **Test your changes**: Ensure all tests pass
2. **Update documentation**: Add/update relevant docs
3. **Check style**: Follow coding standards
4. **Write clear commit messages**: Describe what and why

### PR Template

```markdown
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Checklist
- [ ] Tests pass locally
- [ ] Documentation updated
- [ ] Methodology/limitations documented (for analysis modules)
- [ ] No overclaiming in documentation
```

### Review Process

1. Submit PR with clear description
2. Address reviewer feedback
3. Ensure CI passes
4. Maintainer merges after approval

---

## Areas Seeking Contributions

### High Priority

- **Validation studies**: Compare LingFrame scores to expert ratings
- **Test coverage**: Especially for evaluation module
- **Generation layer**: Revision suggestions from findings
- **Non-Western rhetorical frameworks**: Expand beyond Aristotelian tradition

### Medium Priority

- Domain profiles for specific fields (legal, medical, scientific)
- Additional visualization types
- Multi-language support
- Performance optimization

### Research Contributions

- Empirical validation of heuristics
- Comparison with other tools (AntConc, Voyant, LIWC)
- Case studies with before/after analysis

---

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones
- Join discussions in relevant issues

---

*Thank you for contributing to LingFrame!*
