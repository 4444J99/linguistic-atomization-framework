[![ORGAN-I: Theoria](https://img.shields.io/badge/ORGAN--I-Theoria-311b92?style=flat-square)](https://github.com/organvm-i-theoria)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)]()
[![Tests: 142](https://img.shields.io/badge/tests-142-brightgreen?style=flat-square)]()
[![Corpus: 46 Works](https://img.shields.io/badge/corpus-46%20works-green?style=flat-square)]()
[![Languages: 15+](https://img.shields.io/badge/languages-15%2B-purple?style=flat-square)]()
[![HTML](https://img.shields.io/badge/language-HTML%20%7C%20Python-e34c26?style=flat-square)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow?style=flat-square)](LICENSE)

# LingFrame — Linguistic Atomization Framework

[![CI](https://github.com/organvm-i-theoria/linguistic-atomization-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/organvm-i-theoria/linguistic-atomization-framework/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-pending-lightgrey)](https://github.com/organvm-i-theoria/linguistic-atomization-framework)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://github.com/organvm-i-theoria/linguistic-atomization-framework/blob/main/LICENSE)
[![Organ I](https://img.shields.io/badge/Organ-I%20Theoria-8B5CF6)](https://github.com/organvm-i-theoria)
[![Status](https://img.shields.io/badge/status-active-brightgreen)](https://github.com/organvm-i-theoria/linguistic-atomization-framework)
[![Python](https://img.shields.io/badge/lang-Python-informational)](https://github.com/organvm-i-theoria/linguistic-atomization-framework)


**A computational rhetoric platform that decomposes text into hierarchical atomic units, applies six configurable analysis modules across every level of linguistic granularity, and generates interactive visualizations — spanning 46 canonical works in 15+ languages across 12 literary traditions.**

---

## Table of Contents

- [Why This Exists](#why-this-exists)
- [Philosophical Framework](#philosophical-framework)
- [What LingFrame Does](#what-lingframe-does)
- [The Global Canonical Corpus](#the-global-canonical-corpus)
- [Technical Architecture](#technical-architecture)
- [Installation and Quick Start](#installation-and-quick-start)
- [Three User Pathways](#three-user-pathways)
- [Analysis Methodology](#analysis-methodology)
- [Multilingual Support](#multilingual-support)
- [Extension Points](#extension-points)
- [Sample Projects](#sample-projects)
- [Technology Stack](#technology-stack)
- [Documentation](#documentation)
- [Roadmap](#roadmap)
- [Cross-Organ Context](#cross-organ-context)
- [Citation](#citation)
- [Contributing](#contributing)
- [License](#license)

---

## Why This Exists

Rhetorical analysis — the millennia-old discipline of understanding how language persuades, instructs, moves, and transforms — remains overwhelmingly subjective. A scholar reads a text, identifies patterns through trained intuition, and produces an interpretation that another scholar may read entirely differently. Writers seeking feedback on argumentation quality receive impressionistic assessments. Translation studies rely on bilingual intuition rather than measurable divergence metrics. Comparative literature traces structural parallels across traditions by hand, one passage at a time.

The problem is not that human interpretation lacks value. It is that human interpretation lacks *instruments*. A musician does not abandon their ear when they use a tuner; the tuner reveals what the ear might miss and confirms what the ear suspects. Rhetorical analysis needs its tuner.

LingFrame is that tuner: a computational rhetoric platform that atomizes text into a hierarchical structure — theme, paragraph, sentence, word, letter — and applies configurable analysis pipelines at every level of that hierarchy. It does not replace the scholar's trained eye. It arms the scholar with pattern-detection capabilities that would take weeks to replicate manually, running across texts in 15+ languages spanning four millennia of literary production.

This is not a grammar checker, not a writing assistant, not a generative AI that rewrites your prose. LingFrame is a *heuristic analysis instrument* — it highlights patterns for human interpretation, quantifies what was previously only felt, and makes visible the invisible architectures of language.

---

## Philosophical Framework

### Linguistic Atomization as Epistemological Method

The central idea of LingFrame is deceptively simple: *any text can be decomposed into atoms, and those atoms can be analyzed at multiple levels of granularity simultaneously*. This is linguistic atomization — the systematic breaking of language into its constituent units, not to reduce it, but to reveal the structures that emerge at each scale.

The metaphor is deliberately drawn from physics. Just as matter reveals different properties at the atomic, molecular, and macroscopic scales, language reveals different patterns at the letter, word, sentence, paragraph, and thematic scales. A sentiment arc visible at the paragraph level may be invisible at the sentence level. A rhetorical strategy that operates through word choice (diction) functions differently from one that operates through sentence structure (syntax), even when both serve the same argumentative purpose.

### The Hierarchy of Atoms

LingFrame's atomization model produces a five-level tree:

```
Theme (T)
  └── Paragraph (P)
        └── Sentence (S)
              └── Word (W)
                    └── Letter (L)
```

Each node in this tree is an "atom" — a discrete unit of text carrying metadata about its position, its content, and its relationships to adjacent and parent atoms. Analysis modules traverse this tree, computing metrics at each level and aggregating them upward. The result is not a single score or a single interpretation, but a *multi-dimensional profile* of the text that respects the irreducible complexity of language.

### Why Hierarchical Decomposition Matters

Traditional computational linguistics tends to operate at a single level — bag-of-words models work at the word level, sentiment analyzers at the sentence or document level, topic models at the document level. LingFrame's hierarchical approach means that every analysis module produces results at *every* level simultaneously. This reveals patterns that single-level analysis misses entirely:

- **Cross-level rhetorical strategies**: An author who uses emotionally charged individual words (Word level) within logically structured sentences (Sentence level) within thematically neutral paragraphs (Paragraph level) is executing a specific rhetorical technique — one that only becomes visible when all three levels are examined together.
- **Structural rhythm**: The alternation between long and short paragraphs, between complex and simple sentences, between Latinate and Anglo-Saxon diction — these rhythmic patterns emerge from multi-level analysis and correspond to the "music" of prose that experienced readers feel but rarely quantify.
- **Translation fidelity at scale**: When comparing translations, divergence may occur at different levels — one translator preserves sentence structure but alters word choice; another preserves vocabulary but restructures paragraphs. Hierarchical comparison reveals *where* and *how* translations diverge, not merely *that* they diverge.

### Heuristic Honesty

LingFrame is explicitly a *heuristic* tool. Its scores are pattern-detection indicators, not validated psychometric measurements. The 9-step evaluation framework produces numbers between 0 and 100, but those numbers measure the *density of detectable linguistic markers*, not the "quality" of rhetoric in any absolute sense. A text that scores 30 on Pathos is not necessarily less emotionally effective than one that scores 80 — it may simply employ emotional strategies that LingFrame's current pattern library does not detect.

This philosophical honesty is foundational. LingFrame exists within ORGAN-I: Theoria, the epistemological organ of the organvm system. Theoria's mandate is not to produce convenient answers but to pursue rigorous inquiry — and rigorous inquiry requires acknowledging the boundaries of its instruments. LingFrame's documentation, scoring explanations, and methodology papers all maintain this commitment to epistemic transparency.

---

## What LingFrame Does

LingFrame performs **computational rhetorical analysis** through five interconnected stages:

1. **Atomization** — Decomposes any text (plain text, PDF, uploaded document) into a five-level hierarchical structure using configurable naming strategies. Each atom receives a unique identifier and metadata about its position, content, and linguistic properties.

2. **Multi-Dimensional Analysis** — Applies six configurable analysis modules across the hierarchy. Each module operates independently, producing its own data structures, but all modules share the same atomic tree, enabling cross-module correlation.

3. **Pattern Detection** — Identifies linguistic markers (evidence markers, emotional appeals, authority signals, weakness indicators, transition patterns), rhetorical strategies, and structural patterns that emerge at individual and cross-level scales.

4. **Visualization** — Generates five types of interactive HTML visualizations (force-directed semantic networks, Sankey temporal flows, sentiment charts, entity browsers, evaluation dashboards) with cross-visualization linking that allows click-through navigation between views.

5. **Report Generation** — Produces human-readable narrative reports in HTML with findings, recommendations, and — optionally — revision suggestions generated through the framework's generation layer.

### The Six Analysis Modules

| Module | Method | What It Reveals |
|--------|--------|-----------------|
| **Heuristic Evaluation** | Pattern matching against rhetorical markers for evidence, emotion, authority | A 9-step assessment (Critique, Logos, Pathos, Ethos, Logic Check, Blind Spots, Shatter Points, Bloom, Evolve) with per-level breakdowns and weighted aggregation |
| **Semantic Analysis** | TF-IDF similarity computation + entity co-occurrence mapping | Theme networks showing how concepts cluster and relate across the text; concept density at each hierarchical level |
| **Temporal Analysis** | Verb tense extraction + temporal marker detection | Timeline flow revealing how narrative moves through past, present, and future; tense distribution patterns |
| **Sentiment Analysis** | VADER + domain-specific lexicons (English) / XLM-RoBERTa (multilingual) | Emotional arcs across the text; valence and arousal mapping at sentence, paragraph, and theme levels |
| **Entity Analysis** | spaCy NER + domain-specific regex patterns (15+ languages) | Named entity extraction, co-occurrence matrices, entity density mapping across text sections |
| **Translation Analysis** | Sentence alignment + embedding-based comparison | Divergence metrics between source and translation; semantic fidelity scores at each hierarchical level |

---

## The Global Canonical Corpus

LingFrame ships with a curated corpus of **46 canonical works** across **115 text files** spanning **12 literary traditions** and four millennia of human literary production. All texts are in the public domain.

### Traditions Represented

| Tradition | Works | Example Texts |
|-----------|-------|---------------|
| **Classical Greek & Latin** | Iliad, Odyssey, Aeneid, Metamorphoses | Homer (Butler, 1898), Virgil (Latin original + Dryden, 1697 + Conington, 1866), Ovid |
| **Ancient Near Eastern** | Epic of Gilgamesh | Jastrow (1920), Thompson (1928) |
| **Arabic-Persian** | Quran, Arabian Nights, Rubaiyat, Conference of the Birds | Arabic original + 4 English translations (Pickthall, Rodwell, Sale, Yusuf Ali); Burton (16 vols); Fitzgerald |
| **Chinese Classical** | Tao Te Ching, Analects, Art of War, Journey to the West | Chinese originals + multiple translations (Legge, Goddard, Medhurst, Giles) |
| **Sanskrit** | Bhagavad Gita, Mahabharata, Ramayana, Rigveda | Sanskrit originals + English translations |
| **Hebrew** | Tanakh | Hebrew original + English translations |
| **Japanese** | Tale of Genji, Heike Monogatari, Kojiki, Oku no Hosomichi | Japanese originals + English translations |
| **Medieval European** | Beowulf, Canterbury Tales, Divine Comedy, Song of Roland | Old English, Middle English, Italian originals + translations |
| **Renaissance** | Don Quixote, The Prince, Hamlet, The Tempest | Shakespeare (First Folio, 1623), Machiavelli, Cervantes |
| **Enlightenment** | Candide, Gulliver's Travels, Paradise Lost | Voltaire, Swift, Milton |
| **Romantic** | Frankenstein, Pride and Prejudice, Faust, Les Fleurs du Mal, Eugene Onegin, Les Miserables | Shelley, Austen, Goethe, Baudelaire, Pushkin (Russian original), Hugo |
| **Modern** | Moby-Dick, Crime and Punishment, Madame Bovary, Dubliners, The Trial, We | Melville, Dostoevsky (Russian original), Flaubert, Joyce, Kafka, Zamyatin |

### Corpus Design Principles

The corpus is not a random collection. It is curated to enable specific analytical workflows:

- **Cross-translation comparison**: Major works include the original-language text alongside 2-5 public-domain English translations (e.g., the Quran includes Arabic + 4 translations; the Tao Te Ching includes Chinese + 3 translations). This enables LingFrame's Translation Analysis module to quantify divergence across renderings of the same source.
- **Cross-tradition structural analysis**: Works are selected to span rhetorical traditions — Homeric oral-formulaic composition, Quranic sajʿ (rhymed prose), Chinese classical parallelism, Sanskrit epic metre — enabling comparative rhetorical study across civilizational boundaries.
- **Temporal coverage**: From the Epic of Gilgamesh (c. 2100 BCE) through Joyce's Dubliners (1914), the corpus enables diachronic study of how rhetorical strategies evolve across four millennia.
- **Script diversity**: Texts span 8+ writing systems (Latin, Cyrillic, Greek, Arabic, Hebrew, Devanagari, CJK, Japanese), exercising LingFrame's multilingual tokenization pipeline and validating its script-aware analysis capabilities.

---

## Technical Architecture

### Directory Structure

```
linguistic-atomization-framework/
├── framework/                    # Core library
│   ├── core/                     # Atomization engine
│   │   ├── atomizer.py           # Text → hierarchical atom tree
│   │   ├── ontology.py           # Data structures (Atom, Corpus, etc.)
│   │   ├── naming.py             # 5 naming strategies
│   │   ├── pipeline.py           # Analysis orchestration
│   │   ├── language.py           # Language detection and configuration
│   │   ├── tokenizers.py         # Script-aware tokenization
│   │   ├── registry.py           # Component registry
│   │   ├── recursion.py          # Iterative analysis capability
│   │   └── reproducibility.py    # Checksum tracking
│   ├── analysis/                 # 6 analysis modules
│   │   ├── base.py               # BaseAnalysisModule interface
│   │   ├── evaluation.py         # 9-step heuristic evaluation
│   │   ├── semantic.py           # TF-IDF + entity co-occurrence
│   │   ├── temporal.py           # Verb tense + temporal markers
│   │   ├── sentiment.py          # VADER / XLM-RoBERTa
│   │   ├── entity.py             # spaCy NER + domain patterns
│   │   └── translation.py        # Alignment + embedding comparison
│   ├── visualization/            # 5 visualization adapters
│   │   ├── adapters/             # D3.js, Plotly, Chart.js adapters
│   │   ├── cross_linking.py      # Cross-visualization navigation
│   │   └── base.py               # BaseVisualizationAdapter interface
│   ├── output/                   # Report formatters
│   │   ├── narrative.py          # HTML narrative reports
│   │   └── scholarly.py          # LaTeX, TEI-XML, CoNLL export
│   ├── generation/               # Revision suggestion engine
│   ├── domains/                  # Domain profiles (military, literary, etc.)
│   ├── loaders/                  # PDF and document ingestion
│   ├── llm/                      # Optional LLM integration
│   └── schemas/                  # Atomization schemas (default, Arabic, Chinese, Japanese)
│
├── app/                          # Streamlit web interface
│   ├── streamlit_app.py          # Main web entry point
│   └── components/               # UI components
│       ├── corpus_observatory.py # Browse, preview, compare 46 texts
│       ├── rhetoric_gym.py       # Practice exercises with feedback
│       ├── analysis_engine.py    # Analysis orchestration
│       ├── visualization_bridge.py # Visualization rendering
│       ├── upload.py             # Document upload handler
│       └── results.py            # Results display
│
├── cli/                          # Command-line interfaces
│   ├── main.py                   # Full CLI (atomize, analyze, visualize, migrate, etc.)
│   └── simple.py                 # Simplified one-command interface
│
├── corpus/                       # 46 works, 115 files, 12 traditions
│   ├── classical/                # Greek & Latin
│   ├── arabic-persian/           # Quran, Arabian Nights, Rubaiyat, etc.
│   ├── chinese-classical/        # Tao Te Ching, Analects, Art of War, etc.
│   ├── sanskrit/                 # Bhagavad Gita, Mahabharata, Ramayana, Rigveda
│   ├── hebrew/                   # Tanakh
│   ├── japanese/                 # Tale of Genji, Heike Monogatari, etc.
│   ├── medieval/                 # Beowulf, Canterbury Tales, Divine Comedy, etc.
│   ├── renaissance/              # Don Quixote, Hamlet, The Prince
│   ├── enlightenment/            # Candide, Gulliver's Travels, Paradise Lost
│   ├── romantic/                 # Frankenstein, Faust, Eugene Onegin, etc.
│   ├── modern/                   # Moby-Dick, Crime and Punishment, The Trial, etc.
│   └── early-modern/             # The Tempest
│
├── projects/                     # Analysis projects with configurations
│   └── literary-analysis/        # Sample projects (tomb-unknowns, MET4MORFOSES)
│
├── templates/                    # HTML report templates
├── tests/                        # 142 tests across all modules
├── visualizations/               # Pre-generated interactive visualizations
├── docs/                         # Theory, methodology, limitations, tutorials
├── lingframe.py                  # CLI entry point
└── run_web.py                    # Web app launcher
```

### Core Concepts

**Hierarchical Atomization.** Text is decomposed into a tree structure: Theme -> Paragraph -> Sentence -> Word -> Letter. Each node is an "atom" with an identifier, content, metadata, and parent-child relationships. The atomizer supports configurable detection of theme boundaries (heading patterns, whitespace heuristics) and delegates sentence/word tokenization to language-appropriate pipelines.

**Five Naming Strategies.** Every atom receives a unique identifier. The naming strategy determines how that identifier is constructed:

| Strategy | Example ID | Use Case |
|----------|-----------|----------|
| `hybrid` (recommended) | `T001:section-title.P001.S001` | Readable + unique; best for most analyses |
| `hierarchical` | `T001.P001.S001` | Clean parent-child paths for programmatic access |
| `semantic` | `military-town.para-1.sent-1` | Content-derived slugs for human navigation |
| `legacy` | `T001`, `P0001`, `S00001` | Flat IDs; backward compatibility |
| `uuid` | `T_abc12345` | Globally unique; cross-corpus reference |

**Domain Profiles.** Analysis behavior adapts to textual domain through YAML-defined profiles containing domain-specific sentiment lexicons and entity recognition patterns. The framework ships with military and base (general) profiles, with a documented pattern for creating literary, legal, technical, and other domain profiles.

**Analysis Pipeline.** The processing flow is:

```
Source Text → Atomization → [Analysis Modules] → Visualization → Report
                                    ↓
                           Generation (revision suggestions)
                                    ↓
                              [Recursion loop]
```

The optional recursion loop enables iterative analysis: apply suggestions, re-atomize, re-analyze, compare results. Reproducibility tracking ensures that each iteration is checksummed and can be exactly replicated.

---

## Installation and Quick Start

### Prerequisites

- Python 3.10+ (3.11+ recommended)
- pip or conda for package management
- 500MB+ disk space (corpus texts are included)

### Installation

```bash
git clone https://github.com/organvm-i-theoria/linguistic-atomization-framework.git
cd linguistic-atomization-framework

python3 -m venv new_venv
source new_venv/bin/activate  # Windows: new_venv\Scripts\activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm  # Base English model
# python -m spacy download en_core_web_trf  # Higher accuracy (optional, larger)
```

### Quick Start — Analyze a Document

```bash
# Analyze a PDF or text file — opens interactive HTML report in browser
python lingframe.py analyze document.pdf

# Quick console summary (no browser required)
python lingframe.py quick document.txt

# Save report to specific location
python lingframe.py analyze essay.pdf -o analysis-report.html
```

### Quick Start — Web Interface

```bash
python run_web.py
# Opens at http://localhost:8501
# Features: Corpus Observatory, Rhetoric Gym, document upload, interactive analysis
```

### Quick Start — Project-Based Analysis

```bash
# List available analysis projects
python lingframe.py list-projects

# Run full pipeline on a sample project
python lingframe.py run -p literary-analysis/tomb-unknowns --visualize --verbose

# Individual pipeline stages
python lingframe.py atomize -p literary-analysis/tomb-unknowns
python lingframe.py analyze -p literary-analysis/tomb-unknowns
python lingframe.py visualize -p literary-analysis/tomb-unknowns
```

---

## Three User Pathways

### Scholar Pathway

Full platform access for linguistic research, corpus analysis, and methodology development. Scholars work with the project-based workflow, defining custom analysis pipelines through `project.yaml` configuration files, building domain-specific lexicons, and using the Corpus Observatory to browse and compare texts from the 46-work canonical corpus.

```bash
# Project-based corpus analysis with full visualization
lingframe run -p literary-analysis/corpus-name --visualize --verbose

# Custom pipeline stages
lingframe atomize -p my-project && lingframe analyze -p my-project

# Migrate a project to ontological naming
lingframe migrate --project my-project --category literary-analysis --naming hybrid
```

### Writer Pathway

Simplified interface for document feedback and revision guidance. Writers upload a document (PDF, plain text) and receive an immediate analysis with a narrative report covering rhetorical strengths, weaknesses, and concrete revision suggestions.

```bash
# Instant analysis with HTML report
lingframe analyze essay.pdf

# Quick console summary for iterative editing
lingframe quick document.txt
```

### Developer Pathway

API access for embedding analysis in applications. The framework exposes a clean Python API for atomization, analysis, and visualization, enabling integration into educational platforms, writing tools, and research pipelines.

```python
from framework.core.pipeline import Pipeline
from framework.core.atomizer import Atomizer

atomizer = Atomizer(config)
corpus = atomizer.atomize(text)
results = Pipeline(config).run(corpus)
```

---

## Analysis Methodology

### The 9-Step Heuristic Evaluation Framework

The evaluation module — LingFrame's most distinctive analytical instrument — applies a structured assessment organized into four phases:

| Phase | Steps | Focus |
|-------|-------|-------|
| **Evaluation** | 1. Critique, 2. Logos, 3. Pathos, 4. Ethos | Initial rhetorical assessment across the three Aristotelian appeals plus overall critique |
| **Reinforcement** | 5. Logic Check | Argument flow, transition quality, logical consistency |
| **Risk** | 6. Blind Spots, 7. Shatter Points | Vulnerabilities in reasoning, unstated assumptions, points where the argument is most susceptible to counterattack |
| **Growth** | 8. Bloom, 9. Evolve | Emergent insights — patterns that suggest the text is reaching toward something it has not yet fully articulated; synthesis opportunities |

### How Scoring Works

Each step produces a score (0-100) based on:

1. **Pattern matching** against predefined linguistic markers (evidence markers, emotional markers, authority markers, weakness markers, transition markers)
2. **Density calculations** at each atomization level — how many markers appear per atom at each level of the hierarchy
3. **Weighted aggregation** across levels: Letter (5%), Word (15%), Sentence (35%), Paragraph (30%), Theme (15%)

The weighting reflects the relative rhetorical significance of each level — sentences and paragraphs carry the most rhetorical weight in Western argumentation traditions, while letter-level patterns (alliteration, assonance) contribute subtly but measurably.

### Linguistic Marker Categories

The framework detects patterns across five marker categories:

- **Evidence Markers**: Statistics, citations, logical connectors ("therefore," "because," "studies show"), quantifiers, specific examples
- **Emotional Markers**: Appeals to shared values, urgency language, inclusive pronouns ("we," "our"), intensifiers, sensory language
- **Authority Markers**: Credential references, source citations, trust builders ("research confirms"), appropriate hedging ("likely," "suggests")
- **Weakness Markers**: Unsupported claims, vague quantifiers ("many," "some"), logical fallacies, contradiction indicators
- **Transition Markers**: Addition ("furthermore," "moreover"), contrast ("however," "nevertheless"), cause-effect ("consequently," "therefore"), sequence ("first," "finally")

### Epistemic Transparency

Every score in LingFrame comes with an explanation layer that shows exactly which markers were detected, at which level, and how they were weighted. This is not a black box. The `docs/methodology.md` and `docs/theory.md` documents provide full theoretical grounding for the marker taxonomy, the weighting scheme, and the known limitations of each detection heuristic.

---

## Multilingual Support

LingFrame supports **15+ languages** across **8+ writing systems**, with script-aware tokenization pipelines that adapt to the specific segmentation requirements of each language family.

| Script | Languages | Tokenization Strategy |
|--------|-----------|----------------------|
| **Latin** | English, German, French, Spanish, Italian, Portuguese, Latin | Whitespace + spaCy NLP models |
| **Cyrillic** | Russian, Ukrainian, Bulgarian | Whitespace + spaCy |
| **Greek** | Modern Greek, Ancient Greek | Whitespace + spaCy |
| **Arabic** | Arabic, Persian | CAMeL Tools / whitespace fallback |
| **Hebrew** | Hebrew | Whitespace + script-aware segmentation |
| **Devanagari** | Hindi, Sanskrit | Indic NLP Library |
| **CJK** | Chinese (Simplified/Traditional) | jieba (NLP) or character-level |
| **Japanese** | Japanese | fugashi/MeCab or character-level |
| **Korean** | Korean | KoNLPy or whitespace |
| **Thai** | Thai | PyThaiNLP |

### CJK Strategy Options

For Chinese, Japanese, and Korean texts, LingFrame offers three tokenization strategies:

- **`nlp`**: Language-specific word segmentation (jieba for Chinese, fugashi/MeCab for Japanese, KoNLPy for Korean). Best for semantic analysis where word boundaries matter.
- **`character`**: Character-by-character tokenization. Best for deep structural analysis of character-level patterns, calligraphic analysis, and texts where word segmentation is contested.
- **`hybrid`**: NLP segmentation with character-level fallback for unsegmentable passages. Recommended default for mixed-script or uncertain texts.

Custom atomization schemas for Arabic (`framework/schemas/arabic.yaml`), Chinese (`framework/schemas/chinese.yaml`), and Japanese (`framework/schemas/japanese.yaml`) configure script-specific handling of diacritics, punctuation, and sentence boundaries.

---

## Extension Points

LingFrame is designed for extensibility through three documented extension patterns.

### Add an Analysis Module

```python
# framework/analysis/my_analysis.py
from framework.analysis.base import BaseAnalysisModule

class MyAnalysis(BaseAnalysisModule):
    name = "my_analysis"

    def analyze(self, corpus, domain, config):
        # Traverse the atom tree, compute metrics at each level
        results = self._compute(corpus)
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

Military memorial analysis demonstrating domain-specific analysis capabilities:

- **Domain lexicon**: Military terminology, formal tone detection, ceremonial language patterns
- **Entity recognition**: Ranks, units, locations, equipment — using custom regex patterns defined in `framework/domains/military/`
- **Full pipeline output**: Atomized JSON, 4 analysis outputs (semantic, temporal, sentiment, entity), 5 interactive visualizations, narrative report
- **Use case**: Understanding how official commemorative rhetoric constructs authority, invokes emotion, and manages the tension between individual sacrifice and institutional purpose

### literary-analysis/MET4MORFOSES

Literary metamorphosis study demonstrating creative-analytical applications:

- **Narrative structure analysis**: Tracking transformation arcs across three cycles of a creative manuscript
- **Character transformation tracking**: Entity analysis applied to fictional metamorphosis
- **Thematic mapping**: Semantic network visualization of how transformation themes cluster and evolve
- **Temporal flow**: Sankey diagram showing narrative movement through time

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Core** | Python 3.11+, spaCy, NLTK, VADER | Text processing, NLP, sentiment baseline |
| **Multilingual NLP** | jieba, fugashi, CAMeL Tools, Indic NLP, langdetect | Script-aware tokenization and language detection |
| **Analysis** | scikit-learn (TF-IDF), transformers (XLM-RoBERTa), sentence-transformers | Semantic similarity, multilingual sentiment, embedding comparison |
| **Visualization** | D3.js (force graphs), Plotly.js (Sankey), Chart.js (charts) | Interactive browser-based visualizations |
| **Web Interface** | Streamlit | Corpus Observatory, Rhetoric Gym, upload-and-analyze |
| **PDF Processing** | pdfplumber, PyMuPDF | Document ingestion from PDF format |
| **Unicode** | unidecode, pysbd | Transliteration and sentence boundary detection |
| **LLM Integration** | Anthropic, OpenAI, local models (optional) | Enhanced analysis and revision suggestions |
| **Export** | LaTeX, TEI-XML, CoNLL | Scholarly output formats |

---

## Documentation

| Document | Description |
|----------|-------------|
| [CLAUDE.md](CLAUDE.md) | Developer guide — commands, architecture patterns, data schemas |
| [docs/theory.md](docs/theory.md) | Theoretical foundation — linguistic frameworks, epistemological grounding |
| [docs/methodology.md](docs/methodology.md) | Analysis methodology — marker taxonomy, scoring, weighting |
| [docs/limitations.md](docs/limitations.md) | Scope and limitations — honest assessment of heuristic boundaries |
| [docs/architecture.md](docs/architecture.md) | Technical architecture — component relationships, data flow |
| [docs/tutorials/](docs/tutorials/) | 4 tutorials: first analysis, comparative analysis, custom domains, building modules |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution guidelines — code style, PR process, module development |

---

## Roadmap

### Completed

- [x] Hierarchical text atomization with 5 naming strategies
- [x] 6 analysis modules (evaluation, semantic, temporal, sentiment, entity, translation)
- [x] 5 visualization adapters (dashboard, force graph, Sankey, chart, entity browser)
- [x] Cross-visualization linking (click-through between views)
- [x] Narrative report generation with HTML templates
- [x] Scholarly export formats (LaTeX, TEI-XML, CoNLL)
- [x] Web interface (Streamlit) with Corpus Observatory and Rhetoric Gym
- [x] Dual CLI: full-featured + simplified one-command interface
- [x] Domain profile system (military, literary, technical)
- [x] Optional LLM integration (Anthropic, OpenAI, local models)
- [x] Generation layer (revision suggestions + quick wins)
- [x] Recursion capability (iterative analysis with comparison)
- [x] Explainability layer for score transparency
- [x] Reproducibility tracking with checksums
- [x] 142 tests covering all modules
- [x] Global Canonical Corpus: 46 works, 115 files, 12 traditions, 15+ languages
- [x] Multilingual tokenization (8+ writing systems)
- [x] Cross-translation analysis (divergence metrics, alignment)
- [x] Original-language texts (Greek, Hebrew, Russian, Chinese, Sanskrit, Persian, Japanese, Arabic)
- [x] GitHub Actions CI/CD workflow
- [x] Validation framework with gold standard annotations

### Planned

- [ ] Async pipeline for parallel module execution
- [ ] Plugin system for external module discovery
- [ ] Embedding-based semantic comparison (beyond TF-IDF)
- [ ] Interactive annotation interface
- [ ] Real-time collaborative analysis

---

## Cross-Organ Context

LingFrame is a flagship repository within **ORGAN-I: Theoria** — the epistemological and theoretical foundation of the [organvm](https://github.com/meta-organvm) creative-institutional system. It exemplifies Theoria's mandate: build instruments of rigorous inquiry that make visible the hidden structures of knowledge.

| Organ | Domain | Organization |
|-------|--------|-------------|
| **I — Theoria** | Theory, epistemology, recursion | [`organvm-i-theoria`](https://github.com/organvm-i-theoria) |
| II — Poiesis | Art, generative & experiential | [`organvm-ii-poiesis`](https://github.com/organvm-ii-poiesis) |
| III — Ergon | Commerce, SaaS & products | [`organvm-iii-ergon`](https://github.com/organvm-iii-ergon) |
| IV — Taxis | Orchestration & governance | [`organvm-iv-taxis`](https://github.com/organvm-iv-taxis) |
| V — Logos | Public process & essays | [`organvm-v-logos`](https://github.com/organvm-v-logos) |
| VI — Koinonia | Community & salons | [`organvm-vi-koinonia`](https://github.com/organvm-vi-koinonia) |
| VII — Kerygma | Marketing & distribution | [`organvm-vii-kerygma`](https://github.com/organvm-vii-kerygma) |
| VIII — Meta | Umbrella organization | [`meta-organvm`](https://github.com/meta-organvm) |

### Cross-Organ Relationships

- **ORGAN-II (Poiesis)**: LingFrame's analysis modules can be applied to creative texts produced within Poiesis. The MET4MORFOSES sample project demonstrates this intersection — literary analysis of creative metamorphosis narratives.
- **ORGAN-III (Ergon)**: The framework's analysis capabilities could be productized through Ergon as a SaaS platform, a writing-feedback API, or an educational tool. The three-pathway architecture (Scholar, Writer, Developer) anticipates these commercial applications.
- **ORGAN-V (Logos)**: LingFrame's methodology and findings serve as source material for public-process essays exploring computational approaches to rhetoric, the epistemology of text analysis, and the relationship between measurement and meaning.
- **ORGAN-IV (Taxis)**: The project's `project.yaml` configuration pattern and domain profile system demonstrate the kind of structured governance that Taxis orchestrates across the system.

LingFrame sits at the intersection of computational linguistics and classical rhetoric — a theoretical instrument that demonstrates ORGAN-I's commitment to rigorous, systematic inquiry. Its hierarchical atomization model and heuristic evaluation framework embody the epistemic recursion that defines the Theoria organ: the tool that examines language is itself subject to the same standards of clarity, honesty, and structural integrity that it applies to the texts it analyzes.

---

## Citation

If you use LingFrame in academic work:

```bibtex
@software{lingframe2025,
  title     = {LingFrame: A Computational Rhetoric Platform for Linguistic Atomization},
  author    = {4444j99},
  year      = {2025},
  url       = {https://github.com/organvm-i-theoria/linguistic-atomization-framework},
  note      = {Hierarchical text atomization with 6 analysis modules across 15+ languages}
}
```

---

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines covering code style, PR process, and the module development workflow.

Key areas for contribution:

- **New analysis modules** — extend the `BaseAnalysisModule` interface
- **New visualization adapters** — extend the `BaseVisualizationAdapter` interface
- **Domain profiles** — YAML lexicons and pattern files for new domains (legal, scientific, journalistic, etc.)
- **Corpus additions** — public-domain texts with original-language versions and multiple translations preferred
- **Language support** — tokenization pipelines for additional languages and writing systems

---

## License

MIT License. See [LICENSE](LICENSE) for details.

---

## Author

**[@4444j99](https://github.com/4444j99)**

---

*LingFrame — Computational rhetoric for linguistic scholarship*
