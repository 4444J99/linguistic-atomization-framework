# LingFrame

**A Computational Rhetoric Platform for Linguistic Analysis**

[![Status: Research](https://img.shields.io/badge/Status-Research-blue.svg)]()
[![Analysis: Heuristic](https://img.shields.io/badge/Analysis-Heuristic-orange.svg)]()

LingFrame transforms text into hierarchical structures and applies multi-dimensional analysis pipelines to reveal rhetorical patterns, argumentative structure, and compositional dynamics.

---

## What LingFrame Does

LingFrame performs **computational rhetorical analysis** through:

1. **Atomization**: Decomposes text into a hierarchical structure (theme → paragraph → sentence → word → letter)
2. **Multi-dimensional Analysis**: Applies configurable analysis modules across the hierarchy
3. **Pattern Detection**: Identifies linguistic markers, rhetorical strategies, and structural patterns
4. **Visualization**: Generates interactive visualizations of analysis results
5. **Report Generation**: Produces human-readable reports with findings and recommendations

### Analysis Modules

| Module | Approach | Output |
|--------|----------|--------|
| **Heuristic Evaluation** | Pattern matching against rhetorical markers (evidence, emotion, authority) | 9-step assessment with per-level breakdown |
| **Semantic Analysis** | TF-IDF similarity + entity co-occurrence | Theme network, concept clusters |
| **Temporal Analysis** | Verb tense extraction + temporal marker detection | Timeline flow, narrative progression |
| **Sentiment Analysis** | VADER + domain lexicons (EN) / XLM-RoBERTa (multilingual) | Emotional arc, valence/arousal mapping |
| **Entity Analysis** | spaCy NER + domain patterns (15+ languages) | Named entities, co-occurrence matrix |
| **Translation Analysis** | Sentence alignment + embedding comparison | Divergence metrics, semantic fidelity |

### Multilingual Support

LingFrame supports **15+ languages** across **8+ writing systems**:

| Script | Languages | Tokenization |
|--------|-----------|--------------|
| Latin | English, German, French, Spanish, Italian, Portuguese, Latin | Whitespace + NLP |
| Cyrillic | Russian, Ukrainian, Bulgarian | Whitespace + spaCy |
| Greek | Modern Greek, Ancient Greek | Whitespace + spaCy |
| Arabic | Arabic, Persian | CAMeL Tools / Whitespace |
| Hebrew | Hebrew | Whitespace |
| Devanagari | Hindi, Sanskrit | Indic NLP |
| Chinese | Mandarin (Simplified/Traditional) | jieba (NLP) or character-level |
| Japanese | Japanese | fugashi/MeCab or character-level |
| Korean | Korean | KoNLPy or whitespace |
| Thai | Thai | PyThaiNLP |

**CJK Strategy Options**:
- `nlp`: Use language-specific word segmentation (jieba, fugashi, etc.)
- `character`: Character-by-character tokenization for deep analysis
- `hybrid`: NLP segmentation with character fallback

### What LingFrame Is Not

LingFrame is a **heuristic analysis tool**, not:
- A replacement for human rhetorical expertise
- A writing correction or grammar tool
- A generative AI that rewrites your text
- An empirically validated assessment instrument

See [Scope & Limitations](docs/limitations.md) for detailed discussion.

---

## Three User Pathways

### Scholar Pathway
Full platform access for linguistic research, corpus analysis, and methodology development.

```bash
# Project-based corpus analysis
lingframe run -p literary-analysis/corpus-name --visualize --verbose

# Custom analysis pipelines
lingframe atomize -p my-project && lingframe analyze -p my-project
```

### Writer Pathway
Simplified interface for document feedback and revision guidance.

```bash
# Instant analysis with HTML report
lingframe analyze essay.pdf

# Quick console summary
lingframe quick document.txt
```

### Developer Pathway
API access for embedding analysis in applications.

```python
from framework.core.pipeline import Pipeline
from framework.core.atomizer import Atomizer

atomizer = Atomizer(config)
corpus = atomizer.atomize(text)
results = Pipeline(config).run(corpus)
```

---

## Quick Start

### Installation

```bash
git clone <repo-url>
cd linguistic-atomization-framework

python3 -m venv new_venv
source new_venv/bin/activate  # Windows: new_venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm  # or en_core_web_trf for higher accuracy
```

### Basic Usage

```bash
# Analyze a document (opens HTML report in browser)
python lingframe.py analyze document.pdf

# Quick console summary
python lingframe.py quick document.pdf

# Save report to specific location
python lingframe.py analyze document.pdf -o analysis-report.html

# Web interface
python run_web.py  # Opens at http://localhost:8501
```

### Project-Based Analysis

```bash
# List available projects
python lingframe.py list-projects

# Run full pipeline with visualization
python lingframe.py run -p literary-analysis/tomb-unknowns --visualize

# Individual pipeline stages
python lingframe.py atomize -p my-project
python lingframe.py analyze -p my-project
python lingframe.py visualize -p my-project
```

---

## Architecture

```
linguistic-atomization-framework/
├── framework/
│   ├── core/           # Atomization engine, ontology, naming system
│   ├── analysis/       # Analysis modules (evaluation, semantic, temporal, etc.)
│   ├── visualization/  # Visualization adapters (D3.js, Plotly, Chart.js)
│   ├── output/         # Report formatters (narrative, JSON)
│   ├── generation/     # Revision suggestion generation
│   ├── domains/        # Domain profiles (military, literary, technical)
│   └── llm/            # Optional LLM integration
│
├── app/                # Streamlit web interface
├── cli/                # Command-line interfaces
├── projects/           # Analysis projects with configurations
├── templates/          # HTML report templates
└── docs/               # Documentation
```

### Core Concepts

**Hierarchical Atomization**
Text is decomposed into a tree structure: Theme → Paragraph → Sentence → Word → Letter. Each node is an "atom" with metadata, enabling analysis at multiple granularity levels.

**Naming Strategies**
Control how atoms are identified:
- `hybrid` (recommended): `T001:section-title.P001.S001` — readable + unique
- `hierarchical`: `T001.P001.S001` — parent-child paths
- `semantic`: `military-town.para-1.sent-1` — content-derived slugs
- `legacy`: Flat IDs for backward compatibility
- `uuid`: Globally unique identifiers

**Domain Profiles**
Customize analysis for specific fields:
```
framework/domains/military/
├── lexicon.yaml     # Sentiment terms (formal, ceremonial, etc.)
└── patterns.yaml    # Entity patterns (ranks, units, equipment)
```

**Analysis Pipeline**
```
Source Text → Atomization → [Analysis Modules] → Visualization → Report
                                    ↓
                           Generation (suggestions)
                                    ↓
                              [Recursion loop]
```

---

## Analysis Methodology

### Heuristic Evaluation Framework

The evaluation module applies a **9-step heuristic framework** organized into four phases:

| Phase | Steps | Focus |
|-------|-------|-------|
| **Evaluation** | Critique, Logos, Pathos, Ethos | Initial rhetorical assessment |
| **Reinforcement** | Logic Check | Argument flow and transitions |
| **Risk** | Blind Spots, Shatter Points | Vulnerabilities and assumptions |
| **Growth** | Bloom, Evolve | Emergent insights and synthesis |

**How Scoring Works**

Each step produces a score (0-100) based on:
1. Pattern matching against predefined linguistic markers
2. Density calculations at each atomization level
3. Weighted aggregation across levels (Letter: 5%, Word: 15%, Sentence: 35%, Paragraph: 30%, Theme: 15%)

**Important**: These scores are **heuristic indicators**, not validated measurements. They highlight patterns for human interpretation, not definitive quality assessments.

### Linguistic Markers

The framework detects patterns in these categories:

- **Evidence Markers**: Statistics, citations, logical connectors, quantifiers
- **Emotional Markers**: Appeals, urgency language, inclusive pronouns, intensifiers
- **Authority Markers**: Credentials, source citations, trust builders, appropriate hedging
- **Weakness Markers**: Unsupported claims, vagueness, logical fallacies
- **Transition Markers**: Addition, contrast, cause-effect, sequence connectors

See [Theoretical Foundation](docs/theory.md) for underlying linguistic frameworks.

---

## Technology Stack

| Layer | Technology |
|-------|------------|
| **Core** | Python 3.11+, spaCy, NLTK, VADER |
| **Multilingual NLP** | jieba (Chinese), fugashi (Japanese), CAMeL (Arabic), langdetect |
| **Analysis** | scikit-learn (TF-IDF), transformers (XLM-RoBERTa), sentence-transformers |
| **Visualization** | D3.js (force graphs), Plotly.js (Sankey), Chart.js |
| **Web Interface** | Streamlit |
| **PDF Processing** | pdfplumber, PyMuPDF |
| **Unicode** | unidecode (transliteration), pysbd (sentence detection) |
| **LLM Integration** | Optional (Anthropic, OpenAI, local models) |

---

## Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Developer guide with commands and patterns |
| [docs/theory.md](docs/theory.md) | Theoretical foundation and linguistic frameworks |
| [docs/limitations.md](docs/limitations.md) | Scope, limitations, and honest assessment |
| [docs/methodology.md](docs/methodology.md) | Analysis methodology in detail |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines |

---

## Extension Points

### Add an Analysis Module

```python
# framework/analysis/my_analysis.py
from framework.analysis.base import BaseAnalysisModule

class MyAnalysis(BaseAnalysisModule):
    name = "my_analysis"

    def analyze(self, corpus, domain, config):
        # Your analysis logic
        return self.make_output(
            data=results,
            summary={"key_finding": value}
        )
```

### Add a Visualization Adapter

```python
# framework/visualization/adapters/my_viz.py
from framework.visualization.base import BaseVisualizationAdapter

class MyVizAdapter(BaseVisualizationAdapter):
    name = "my_viz"
    analysis_types = ["my_analysis"]

    def generate(self, analysis_output, config):
        return self._render_template("my_viz.html", data=analysis_output)
```

### Add a Domain Profile

```yaml
# framework/domains/legal/lexicon.yaml
formal_terms:
  whereas: 0.3
  hereby: 0.2
  stipulate: 0.1

# framework/domains/legal/patterns.yaml
entities:
  case_citation:
    pattern: '\d+\s+[A-Z][a-z]+\.?\s+\d+'
    label: LEGAL_CITATION
```

---

## Sample Projects

### literary-analysis/tomb-unknowns
Military memorial analysis demonstrating:
- Domain-specific lexicon for military terminology
- Formal tone detection
- Ceremonial language patterns
- Entity recognition for ranks, units, locations

### literary-analysis/MET4MORFOSES
Literary metamorphosis study demonstrating:
- Narrative structure analysis
- Character transformation tracking
- Thematic mapping
- Temporal flow visualization

---

## Roadmap

### Completed
- [x] Hierarchical text atomization with 5 naming strategies
- [x] 5 analysis modules (evaluation, semantic, temporal, sentiment, entity)
- [x] 5 visualization adapters (dashboard, force graph, sankey, chart, browser)
- [x] Narrative report generation
- [x] Web interface (Streamlit) and CLI
- [x] Domain profile system
- [x] Optional LLM integration
- [x] Generation layer (revision suggestions)
- [x] Recursion capability (iterative analysis)
- [x] Test suite (142 tests covering all modules)
- [x] Scholarly documentation (theory.md, methodology.md, architecture.md)
- [x] Validation framework with gold standard annotations
- [x] Scholarly export formats (LaTeX, TEI-XML, CONLL)
- [x] Explainability layer for score transparency
- [x] Reproducibility tracking with checksums
- [x] Revision comparison (before/after analysis)
- [x] GitHub Actions CI/CD workflow
- [x] Corpus Observatory (browse, preview, compare texts)
- [x] Rhetoric Gym (practice exercises with feedback)
- [x] Cross-visualization linking (click-through between views)
- [x] **Multi-language support** (15+ languages, 8+ scripts)
- [x] **Global Canonical Corpus** (44 literary works planned)
- [x] **Cross-translation analysis** (divergence metrics)

### Planned
- [ ] Async pipeline for parallel module execution
- [ ] Plugin system for external module discovery
- [ ] Embedding-based semantic comparison
- [ ] Interactive annotation interface

---

## Citation

If you use LingFrame in academic work, please cite:

```bibtex
@software{lingframe,
  title = {LingFrame: A Computational Rhetoric Platform},
  author = {[Author]},
  year = {2025},
  url = {[repository-url]},
  note = {Heuristic analysis framework for computational rhetoric}
}
```

---

## License

Educational and research use. See LICENSE for details.

---

**LingFrame** — *Computational rhetoric for linguistic scholarship*
