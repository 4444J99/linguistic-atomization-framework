# LingFrame Architecture

This document describes the internal architecture of LingFrame, intended for contributors and researchers who want to understand, extend, or embed the framework.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Modules](#core-modules)
3. [Data Flow](#data-flow)
4. [Extension Points](#extension-points)
5. [Design Decisions](#design-decisions)
6. [Module Reference](#module-reference)

---

## System Overview

LingFrame follows a **pipeline architecture** with four phases:

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ ATOMIZE  │ ──► │ ANALYZE  │ ──► │ GENERATE │ ──► │ RECURSE  │
└──────────┘     └──────────┘     └──────────┘     └────┬─────┘
     ▲                                                   │
     └───────────────────────────────────────────────────┘
```

### Phase Descriptions

| Phase | Purpose | Key Components |
|-------|---------|----------------|
| **Atomize** | Decompose text into hierarchical atoms | `Atomizer`, `AtomizationSchema` |
| **Analyze** | Apply analysis modules to atoms | `Pipeline`, `AnalysisModule` |
| **Generate** | Produce revision suggestions | `SuggestionGenerator`, `QuickWinExtractor` |
| **Recurse** | Iterate for progressive improvement | `RecursionTracker` |

---

## Core Modules

### Directory Structure

```
framework/
├── core/                    # Foundation layer
│   ├── ontology.py          # Data structures (Atom, Corpus, Document)
│   ├── atomizer.py          # Text decomposition engine
│   ├── pipeline.py          # Analysis orchestration
│   ├── registry.py          # Component discovery & registration
│   ├── naming.py            # Ontological naming strategies
│   ├── recursion.py         # Iteration tracking
│   └── reproducibility.py   # Analysis audit trails
│
├── analysis/                # Analysis modules
│   ├── base.py              # BaseAnalysisModule interface
│   ├── semantic.py          # TF-IDF theme network
│   ├── temporal.py          # Tense flow analysis
│   ├── sentiment.py         # VADER + domain lexicon
│   ├── entity.py            # Named entity recognition
│   └── evaluation.py        # 9-step rhetorical evaluation
│
├── generation/              # Generative layer
│   ├── suggestions.py       # Revision suggestion engine
│   ├── quick_wins.py        # Top actionable improvements
│   └── revision.py          # Before/after comparison
│
├── visualization/           # Output adapters
│   ├── adapters/            # Per-visualization implementations
│   │   ├── force_graph.py   # D3.js semantic network
│   │   ├── sankey.py        # Plotly temporal flow
│   │   └── ...
│   └── base.py              # VisualizationAdapter interface
│
├── output/                  # Export formatters
│   ├── narrative.py         # Human-readable reports
│   └── scholarly.py         # LaTeX, TEI-XML, CONLL
│
├── domains/                 # Domain profiles
│   └── military/            # Example domain
│       ├── lexicon.yaml     # Sentiment terms
│       └── patterns.yaml    # Entity patterns
│
├── schemas/                 # Atomization configurations
│   └── default.yaml         # Standard schema
│
└── llm/                     # Optional LLM integration
    ├── providers.py         # OpenAI, Anthropic, etc.
    ├── prompts.py           # Prompt library
    └── chain.py             # Prompt chain executor
```

### Component Relationships

```
                    ┌─────────────┐
                    │   Registry  │  ← discovers & registers
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ AnalysisModule│  │ Visualization │  │ DomainProfile │
│   (abstract)  │  │   Adapter     │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
        │
        ├── SemanticAnalysis
        ├── TemporalAnalysis
        ├── SentimentAnalysis
        ├── EntityAnalysis
        └── EvaluationAnalysis
```

---

## Data Flow

### 1. Atomization

```python
# Input: Raw text
text = "The soldier stood at attention..."

# Process: Hierarchical decomposition
atomizer = Atomizer(schema="default")
corpus = atomizer.atomize(text, title="Essay")

# Output: Corpus → Documents → Atoms
#   Corpus
#   └── Document
#       └── Theme (T001)
#           └── Paragraph (P001)
#               └── Sentence (S001)
#                   └── Word (W001)
#                       └── Letter (L001)
```

### 2. Analysis

```python
# Input: Corpus of atoms
# Process: Module-specific analysis
pipeline = Pipeline(config)
results = pipeline.run(corpus)

# Output: AnalysisOutput per module
# {
#   "semantic": { themes, connections, centrality },
#   "temporal": { tense_distribution, flow },
#   "sentiment": { scores, arc },
#   "entity": { entities, references }
# }
```

### 3. Generation

```python
# Input: Analysis findings
# Process: Map findings to suggestions
generator = SuggestionGenerator()
suggestions = generator.generate(analysis_output)

# Output: Prioritized suggestions
# [
#   Suggestion(type=STRENGTHEN, priority=HIGH, ...),
#   Suggestion(type=CLARIFY, priority=MEDIUM, ...),
# ]
```

### 4. Recursion

```python
# Input: Original text + suggestions
# Process: Apply suggestions, re-analyze
tracker = RecursionTracker()
record = tracker.record_iteration(original_scores, revised_scores)

# Output: Iteration record with comparison
# ScoreComparison showing improvement/regression per dimension
```

---

## Extension Points

LingFrame is designed for extension at multiple levels:

### Adding Analysis Modules

```python
# framework/analysis/my_module.py
from framework.analysis.base import BaseAnalysisModule
from framework.core import AnalysisOutput

class MyAnalysis(BaseAnalysisModule):
    name = "my_analysis"
    description = "Custom analysis module"

    def analyze(self, corpus: Corpus, **kwargs) -> AnalysisOutput:
        # Your analysis logic
        return AnalysisOutput(
            module_name=self.name,
            data={"findings": [...]},
            summary={...}
        )
```

Register in `framework/analysis/__init__.py`:
```python
from .my_module import MyAnalysis
__all__ = [..., "MyAnalysis"]
```

### Adding Visualization Adapters

```python
# framework/visualization/adapters/my_viz.py
from framework.visualization.base import VisualizationAdapter

class MyVisualization(VisualizationAdapter):
    name = "my_viz"
    supported_analyses = ["my_analysis"]

    def generate(self, analysis_output: AnalysisOutput) -> str:
        # Generate HTML/JS visualization
        return "<div>...</div>"
```

### Adding Domain Profiles

```yaml
# framework/domains/legal/lexicon.yaml
positive:
  - compliant: 0.6
  - upheld: 0.7
negative:
  - violation: -0.8
  - breach: -0.7
```

```yaml
# framework/domains/legal/patterns.yaml
statutes:
  pattern: '\d+\s+U\.S\.C\.\s+§\s*\d+'
  entity_type: LEGAL_CITATION
```

### Adding Naming Strategies

```python
# framework/core/naming.py
class MyNamingStrategy(NamingStrategy):
    def generate_id(self, atom: Atom, context: NamingContext) -> str:
        # Custom ID generation logic
        return f"CUSTOM_{atom.level}_{atom.index}"
```

---

## Design Decisions

### Why Hierarchical Atomization?

Traditional NLP treats text as flat sequences or simple token lists. LingFrame's hierarchical model:

1. **Preserves structure**: Document → Section → Paragraph → Sentence → Word → Letter
2. **Enables multi-scale analysis**: Patterns emerge at different levels
3. **Supports scholarly citation**: Precise atom references for quotation

### Why Pluggable Modules?

1. **Research flexibility**: Add new analyses without modifying core
2. **Domain adaptation**: Different fields need different tools
3. **Performance**: Only run what you need

### Why Generate → Recurse?

Analysis alone creates "interesting findings." The generative loop:

1. **Closes the gap**: Every finding → actionable suggestion
2. **Enables iteration**: Output feeds back as input
3. **Measures progress**: Quantify improvement over iterations

### Why Reproducibility?

Scholarly work demands verification:

1. **Input fingerprinting**: SHA-256 ensures same text analyzed
2. **Environment capture**: Python/library versions recorded
3. **Configuration snapshot**: Exact settings preserved
4. **Output checksums**: Results can be verified

---

## Module Reference

### Core Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `Atom` | Atomic text unit with level, content, ID | `core/ontology.py` |
| `Corpus` | Collection of documents | `core/ontology.py` |
| `Document` | Single text with atoms | `core/ontology.py` |
| `Atomizer` | Text → hierarchical atoms | `core/atomizer.py` |
| `Pipeline` | Orchestrates analysis | `core/pipeline.py` |
| `Registry` | Component discovery | `core/registry.py` |

### Analysis Classes

| Class | Purpose | Key Output |
|-------|---------|------------|
| `SemanticAnalysis` | Theme network extraction | Themes, connections, centrality |
| `TemporalAnalysis` | Tense flow mapping | Tense distribution, timeline |
| `SentimentAnalysis` | Emotion tracking | VADER scores, emotion arc |
| `EntityAnalysis` | Named entity recognition | Entities, references |
| `EvaluationAnalysis` | 9-step rhetorical evaluation | Dimensional scores |

### Generation Classes

| Class | Purpose | Key Output |
|-------|---------|------------|
| `SuggestionGenerator` | Map findings to fixes | Prioritized suggestions |
| `QuickWinExtractor` | Top 3 improvements | Quick wins with evidence |
| `RevisionComparator` | Before/after view | Change tracking, metrics |

### Support Classes

| Class | Purpose | Location |
|-------|---------|----------|
| `RecursionTracker` | Track iterations | `core/recursion.py` |
| `ReproducibilityTracker` | Audit trails | `core/reproducibility.py` |
| `NarrativeExporter` | Human reports | `output/narrative.py` |
| `LaTeXExporter` | Academic output | `output/scholarly.py` |

---

## Dependency Graph

```
                        framework/__init__.py
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
            core/          analysis/      generation/
                │              │              │
    ┌───────────┼───────────┐  │              │
    ▼           ▼           ▼  │              │
ontology    atomizer    pipeline ◄───────────┘
    │           │           │
    └───────────┴───────────┘
                │
                ▼
           registry ◄──── visualization/
                              │
                              ▼
                          output/
```

### External Dependencies

| Package | Purpose | Optional? |
|---------|---------|-----------|
| `spacy` | NLP processing | No |
| `vaderSentiment` | Sentiment analysis | No |
| `pyyaml` | Configuration | No |
| `numpy` | Numerical ops | No |
| `openai` | LLM integration | Yes |
| `anthropic` | LLM integration | Yes |

---

## Configuration

### Project Configuration (`project.yaml`)

```yaml
project:
  name: "my-analysis"
  version: "1.0.0"

naming:
  strategy: hybrid  # legacy | hierarchical | semantic | uuid | hybrid

corpus:
  documents:
    - source: "docs/essay.pdf"
      title: "My Essay"

domain:
  profile: military  # or: base, literary, technical, custom

analysis:
  pipelines:
    - module: semantic
    - module: evaluation
      options:
        use_llm: true

visualization:
  adapters:
    - type: force_graph
      analysis: semantic
```

### Atomization Schema (`schemas/default.yaml`)

```yaml
levels:
  - name: theme
    delimiter: "\n\n\n"
  - name: paragraph
    delimiter: "\n\n"
  - name: sentence
    pattern: "[.!?]+"
  - name: word
    pattern: "\\s+"
  - name: letter
    pattern: ""
```

---

## Performance Considerations

### Memory Usage

- Atoms are lightweight dataclasses
- Large documents use lazy loading where possible
- Visualization data is generated on-demand

### Parallelization

- Analysis modules are independent → can run in parallel
- Current implementation is sequential (contributions welcome)

### Caching

- TF-IDF vectors cached per corpus
- spaCy models loaded once per session
- LLM responses not cached (determinism concerns)

---

## Testing Architecture

```
tests/
├── test_atomizer.py       # Core atomization tests
├── test_semantic.py       # Semantic analysis tests
├── test_temporal.py       # Temporal analysis tests
├── test_sentiment.py      # Sentiment analysis tests
├── test_entity.py         # Entity analysis tests
├── test_evaluation.py     # Evaluation module tests
├── test_generation.py     # Generation layer tests
├── test_reproducibility.py # Reproducibility tests
├── test_scholarly.py      # Scholarly export tests
└── conftest.py            # Shared fixtures
```

Run all tests:
```bash
pytest tests/ -v
```

Run specific module:
```bash
pytest tests/test_evaluation.py -v
```

---

## Future Architecture

Planned improvements (contributions welcome):

1. **Async Pipeline**: Parallel module execution
2. **Streaming**: Process large documents in chunks
3. **Plugin System**: External module discovery
4. **Remote Analysis**: API-based module execution
5. **Caching Layer**: Configurable result caching

---

## See Also

- [Theory & Methodology](theory.md) - Linguistic foundations
- [Limitations](limitations.md) - Scope and constraints
- [Contributing](../CONTRIBUTING.md) - How to contribute
- [README](../README.md) - Quick start guide
