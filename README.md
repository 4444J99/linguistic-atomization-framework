# LingFrame

**Reveal the architecture of persuasion in your writing.**

> *You can revise forever and still not know if you're improving.*

LingFrame gives you what no grammar checker or AI rewriter can: a map of your own argument showing where it's strong, where it breaks, and exactly what to fix.

---

## The Problem

Every writer knows this feeling: *something's off*, but you can't name it.

You've revised a dozen times. The words are polished. But the argument still doesn't land—and you don't know why. You're flying blind.

**Existing tools miss the architecture:**

| Tool | What It Does | What It Misses |
|------|--------------|----------------|
| **Grammarly** | Fixes commas | How your argument persuades |
| **Hemingway** | Simplifies prose | Emotional arc and logical structure |
| **ChatGPT** | Rewrites your work | A map of *your own* writing |
| **Human editors** | Give feedback | Consistency, availability, affordability |

**What writers actually want:**
- "Show me what's working and what's not"
- "Where does my argument fall apart?"
- "What am I not seeing?"
- "How do I make this stronger?"

---

## The Approach

LingFrame applies **2,000 years of rhetorical wisdom** computationally.

Think of it as an **X-ray for your writing**:

| What the X-Ray Shows | Rhetorical Term | What You Learn |
|---------------------|-----------------|----------------|
| **Bones** | Logos (Logic) | Is your evidence solid? |
| **Blood flow** | Pathos (Emotion) | Does your tone carry? |
| **Structural integrity** | Ethos (Credibility) | Do readers trust you? |
| **Weak points** | Risk Analysis | Where could critics attack? |

### The Analysis Journey

```
UNDERSTAND          REINFORCE           STRESS-TEST         GROW
    │                   │                    │                │
    ▼                   ▼                    ▼                ▼
┌─────────┐       ┌──────────┐        ┌───────────┐     ┌─────────┐
│ Logos   │       │  Logic   │        │  Blind    │     │  Bloom  │
│ Pathos  │       │  Check   │        │  Spots    │     │  Evolve │
│ Ethos   │       │          │        │  Shatter  │     │         │
│ Critique│       │          │        │  Points   │     │         │
└─────────┘       └──────────┘        └───────────┘     └─────────┘
```

### Five Analysis Lenses

| Lens | What It Reveals |
|------|-----------------|
| **Evaluation** | 9-step rhetorical score—logic, emotion, credibility |
| **Semantic** | Theme connections—what concepts link together |
| **Temporal** | Narrative flow—how your timeline unfolds |
| **Sentiment** | Emotional arc—where tone rises and falls |
| **Entity** | Key players—people, places, organizations |

---

## The Outcome

### The Transformation

| Before LingFrame | After LingFrame |
|------------------|-----------------|
| "Something feels off" | "My evidence is thin in paragraphs 3-5" |
| "Is this working?" | "Pathos score: 85. Logos: 50. Add citations." |
| "What would critics say?" | "Three blind spots identified. Here's how to address them." |
| "How do I improve?" | "Quick wins: transitions, evidence, counterarguments" |

### What You Get

```
Overall Score: 71.5/100

WHAT'S WORKING
✓ Strong emotional engagement (Pathos: 85)
✓ No logical fallacies (Shatter Points: 100)
✓ Good thematic coherence (Bloom: 90)

WHAT NEEDS ATTENTION
⚠ Low evidence density (Logos: 50)
⚠ Limited transitions (Logic Check: 54)
⚠ No counterarguments addressed (Blind Spots: 55)

QUICK WINS
1. Add source citations to strengthen credibility
2. Include transition words (therefore, however)
3. Address potential counterarguments
```

### Three Ways to Use It

```bash
# Command line — analyze any document instantly
lingframe analyze essay.pdf

# Web interface — upload and explore in browser
python run_web.py

# Desktop app — standalone application
python -m desktop.app
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
python -m spacy download en_core_web_sm
```

### Basic Usage

```bash
# Instant analysis (opens HTML report)
python lingframe.py analyze document.pdf

# Quick console summary
python lingframe.py quick document.pdf

# Save report to file
python lingframe.py analyze document.pdf -o report.html
```

### Project-Based Analysis

For larger corpora or custom configurations:

```bash
python lingframe.py list-projects
python lingframe.py run -p literary-analysis/tomb-unknowns --visualize
```

See [CLAUDE.md](CLAUDE.md) for full command reference.

---

## Sample Projects

### tomb-unknowns
Military memorial analysis demonstrating domain-specific lexicons, formal tone detection, and entity recognition for ranks and units.

### MET4MORFOSES
Literary metamorphosis study showing narrative structure analysis, character transformation tracking, and thematic mapping.

---

## Architecture

```
linguistic-atomization-framework/
├── framework/
│   ├── core/           # Atomization engine, ontology, naming
│   ├── analysis/       # 5 analysis modules
│   ├── visualization/  # 5 visualization adapters
│   ├── output/         # Narrative report generator
│   └── domains/        # Domain lexicons (military, etc.)
│
├── app/                # Streamlit web interface
├── cli/                # Command-line interfaces
├── desktop/            # Standalone desktop app
├── projects/           # Analysis projects
├── templates/          # HTML report templates
└── lingframe.py        # Main entry point
```

### Key Concepts

**Naming Strategies** — Control how text atoms are identified:
- `hybrid` (default): `T001:section-title.P001.S001` — readable + unique
- `legacy`: `T001.P001.S001` — simple counters
- `semantic`: `military-town.para-1.sent-1` — content-derived

**Domain Profiles** — Customize analysis for specific fields:
- `military/` — Ranks, equipment, ceremonial language
- Custom domains via `lexicon.yaml` + `patterns.yaml`

**Output Formats** — Choose your delivery:
- `narrative` — Coach-like HTML report
- `json` — Structured data for programs
- `interactive` — Full dashboard with visualizations

---

## Technology

| Layer | Stack |
|-------|-------|
| **Analysis** | Python 3.11+, spaCy, VADER, scikit-learn |
| **Visualization** | D3.js, Plotly.js, Chart.js |
| **Web** | Streamlit |
| **Desktop** | PyWebView |
| **PDF** | pdfplumber, PyMuPDF |

---

## Contributing

LingFrame is designed for extension:

**Add an Analysis Module:**
```python
# framework/analysis/my_module.py
class MyAnalysis(BaseAnalysisModule):
    name = "my_analysis"
    def analyze(self, corpus, domain, config):
        return AnalysisOutput(...)
```

**Add a Visualization:**
```python
# framework/visualization/adapters/my_viz.py
class MyVizAdapter(BaseVisualizationAdapter):
    name = "my_viz"
    def generate(self, analysis_output, config):
        return html_content
```

**Add a Domain Profile:**
```
framework/domains/my_domain/
├── lexicon.yaml     # Sentiment terms
└── patterns.yaml    # Entity patterns
```

---

## Roadmap

- [x] Hierarchical text atomization
- [x] 9-step rhetorical evaluation
- [x] 5 analysis modules + visualizations
- [x] Narrative report generation
- [x] Web interface + desktop app
- [ ] Cross-visualization linking
- [ ] Comparative analysis (multiple documents)
- [ ] LLM-enhanced insights
- [ ] API endpoints

---

## License

Educational and research use.

---

**LingFrame** — *See your writing clearly. Fix it precisely.*
