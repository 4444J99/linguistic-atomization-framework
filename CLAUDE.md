# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LingFrame** - A linguistic atomization framework that transforms text into hierarchical structures (theme → paragraph → sentence → word → letter) and runs specialized analysis pipelines generating interactive visualizations.

The framework supports:
- Multiple naming strategies (legacy, hierarchical, semantic, UUID, hybrid)
- Semantic project categorization
- Domain-specific analysis (military, literary, technical, etc.)
- Pluggable analysis modules and visualization adapters

## Build & Run Commands

```bash
# Setup environment
python3 -m venv new_venv
source new_venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm  # or en_core_web_trf for better accuracy
```

### Quick Start (No Technical Knowledge Required)

```bash
# Simple CLI - analyze any document instantly
./new_venv/bin/python lingframe.py analyze essay.pdf           # Opens HTML report in browser
./new_venv/bin/python lingframe.py analyze essay.pdf -o out.html  # Save to specific location
./new_venv/bin/python lingframe.py quick essay.pdf             # Quick console summary

# Web Interface - upload and analyze in browser
./new_venv/bin/python run_web.py
# Then open http://localhost:8501
```

### Project-Based Analysis (Advanced)

```bash
# CLI Commands
./new_venv/bin/python lingframe.py list-projects
./new_venv/bin/python lingframe.py list-categories
./new_venv/bin/python lingframe.py list-modules

# Run full pipeline for a project
./new_venv/bin/python lingframe.py run -p literary-analysis/tomb-unknowns --visualize --verbose

# Individual pipeline stages
./new_venv/bin/python lingframe.py atomize -p literary-analysis/tomb-unknowns
./new_venv/bin/python lingframe.py analyze -p literary-analysis/tomb-unknowns
./new_venv/bin/python lingframe.py visualize -p literary-analysis/tomb-unknowns

# Migrate project to ontological naming
./new_venv/bin/python lingframe.py migrate --project <name> --category <category> --naming hybrid

# View visualizations (requires local server for CORS)
python3 -m http.server 8000
# Then open http://localhost:8000/projects/literary-analysis/tomb-unknowns/visualizations/
```

## Architecture

### Directory Structure
```
linguistic-atomization-framework/
├── framework/
│   ├── core/           # Core components
│   │   ├── naming.py   # Ontological naming system
│   │   ├── ontology.py # Data structures (Atom, Corpus, etc.)
│   │   ├── atomizer.py # Text atomization engine
│   │   ├── pipeline.py # Analysis orchestration
│   │   └── registry.py # Component registry
│   ├── analysis/       # Analysis modules
│   ├── visualization/  # Visualization adapters
│   ├── output/         # Output formatters (narrative reports)
│   ├── domains/        # Domain profiles (military, base)
│   └── schemas/        # Atomization schemas (default.yaml)
├── app/                # Streamlit web interface
│   ├── streamlit_app.py     # Main web entry point
│   └── components/          # UI components
├── cli/                # CLI entry point
│   ├── main.py         # Full CLI with all commands
│   └── simple.py       # Simple one-command interface
├── templates/          # HTML report templates
├── projects/
│   ├── .categories.yaml
│   └── literary-analysis/
│       └── tomb-unknowns/
├── lingframe.py        # Main CLI script
└── run_web.py          # Web app launcher
```

### Naming Strategies
- **legacy**: Flat IDs (T001, P0001, S00001) - backward compatible
- **hierarchical**: Parent-child paths (T001.P001.S001)
- **semantic**: Content-derived slugs (military-town.para-1)
- **uuid**: Globally unique identifiers (T_abc12345)
- **hybrid**: Counter + semantic (T001:military-town.P001.S001)

### Analysis Modules
- `semantic`: TF-IDF based theme network analysis
- `temporal`: Verb tense flow and timeline analysis
- `sentiment`: VADER + domain lexicon sentiment analysis
- `entity`: Named entity recognition (spaCy + regex fallback)

### Visualization Adapters
- `force_graph`: D3.js force-directed semantic network
- `sankey`: Plotly.js Sankey diagram for temporal flow
- `sentiment_chart`: Chart.js sentiment visualization
- `entity_browser`: Interactive entity browser

## Important Patterns

**Ontological Naming**: Configured in `project.yaml`:
```yaml
naming:
  strategy: hybrid  # or legacy, hierarchical, semantic, uuid
```

**Domain Profiles**: Located in `framework/domains/<domain>/`:
- `lexicon.yaml`: Sentiment scoring terms
- `patterns.yaml`: Entity recognition patterns

**Output File Naming**: Pattern `{project}_{module}_{descriptor}_{version}_{timestamp}.json`
- Example: `tomb-unknowns_semantic_theme-network_1.0.0_20260120.json`

**CORS Issue**: Opening HTML files directly (`file://`) causes fetch failures. Always serve via HTTP server.

## Data Schema

### Atomized JSON (Hybrid Naming)
```json
{
  "metadata": {"total_themes": 178, "total_sentences": 2804, ...},
  "themes": [
    {
      "id": "T001:section-title",
      "paragraphs": [
        {
          "id": "T001:section-title.P001",
          "sentences": [
            {
              "id": "T001:section-title.P001.S001",
              "words": [{"id": "T001:section-title.P001.S001.W001", ...}]
            }
          ]
        }
      ]
    }
  ]
}
```

### Project Configuration (project.yaml)
```yaml
project:
  name: "tomb-unknowns"
  version: "1.0.0"

naming:
  strategy: hybrid

corpus:
  documents:
    - source: "docs/document.pdf"
      title: "Document Title"

domain:
  profile: military

analysis:
  pipelines:
    - module: semantic
    - module: temporal
    - module: sentiment
    - module: entity

visualization:
  adapters:
    - type: force_graph
      analysis: semantic
```

<!-- ORGANVM:AUTO:START -->
## System Context (auto-generated — do not edit)

**Organ:** ORGAN-I (Theory) | **Tier:** standard | **Status:** GRADUATED
**Org:** `organvm-i-theoria` | **Repo:** `linguistic-atomization-framework`

### Edges
- **Produces** → `unspecified`: theory

### Siblings in Theory
`recursive-engine--generative-entity`, `organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `.github`, `nexus--babel-alexandria`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `my-knowledge-base`, `scalable-lore-expert` ... and 10 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-05-23T00:26:31Z*

## Active Handoff Protocol

If `.conductor/active-handoff.md` exists, **READ IT FIRST** before doing any work.
It contains constraints, locked files, conventions, and completed work from the
originating agent. You MUST honor all constraints listed there.

If the handoff says "CROSS-VERIFICATION REQUIRED", your self-assessment will
NOT be trusted. A different agent will verify your output against these constraints.

## Session Review Protocol

At the end of each session that produces or modifies files:
1. Run `organvm session review --latest` to get a session summary
2. Check for unimplemented plans: `organvm session plans --project .`
3. Export significant sessions: `organvm session export <id> --slug <slug>`
4. Run `organvm prompts distill --dry-run` to detect uncovered operational patterns

Transcripts are on-demand (never committed):
- `organvm session transcript <id>` — conversation summary
- `organvm session transcript <id> --unabridged` — full audit trail
- `organvm session prompts <id>` — human prompts only


## System Library

Plans: 269 indexed | Chains: 5 available | SOPs: 8 active
Discover: `organvm plans search <query>` | `organvm chains list` | `organvm sop lifecycle`
Library: `/Users/4jp/Code/organvm/praxis-perpetua/library`


## Active Directives

| Scope | Phase | Name | Description |
|-------|-------|------|-------------|
| system | any | atomic-clock | The Atomic Clock |
| system | any | execution-sequence | Execution Sequence |
| system | any | multi-agent-dispatch | Multi-Agent Dispatch |
| system | any | session-handoff-avalanche | Session Handoff Avalanche |
| system | any | system-loops | System Loops |
| system | any | prompting-standards | Prompting Standards |
| system | any | background-task-resilience | background-task-resilience |
| system | any | context-window-conservation | context-window-conservation |
| system | any | session-self-critique | session-self-critique |
| system | any | the-descent-protocol | the-descent-protocol |
| system | any | the-membrane-protocol | the-membrane-protocol |
| system | any | theory-to-concrete-gate | theory-to-concrete-gate |
| system | any | triangulation-protocol | triangulation-protocol |

Linked skills: SOP-TRIADIC-REVIEW-PROTOCOL, cicd-resilience-and-recovery, continuous-learning-agent, evaluation-to-growth, genesis-dna, multi-agent-workforce-planner, promotion-and-state-transitions, quality-gate-baseline-calibration, repo-onboarding-and-habitat-creation, session-self-critique, structural-integrity-audit, the-membrane-protocol, triple-reference


**Prompting (Anthropic)**: context 200K tokens, format: XML tags, thinking: extended thinking (budget_tokens)


## Atomization Pipeline

Run `organvm atoms pipeline --write && organvm atoms fanout --write` to generate task queue.


## System Density (auto-generated)

AMMOI: 25% | Edges: 0 | Tensions: 0 | Clusters: 0 | Adv: 27 | Events(24h): 37975
Structure: 8 organs / 148 repos / 1654 components (depth 17) | Inference: 0% | Organs: META-ORGANVM:63%, ORGAN-I:53%, ORGAN-II:48%, ORGAN-III:54% +5 more
Last pulse: 2026-05-23T00:26:28 | Δ24h: n/a | Δ7d: n/a


## Dialect Identity (Trivium)

**Dialect:** FORMAL_LOGIC | **Classical Parallel:** Logic | **Translation Role:** The Grammar — defines well-formedness in any dialect

Strongest translations: III (formal), IV (formal), META (formal)

Scan: `organvm trivium scan I <OTHER>` | Matrix: `organvm trivium matrix` | Synthesize: `organvm trivium synthesize`


## Logos Documentation Layer

**Status:** ACTIVE | **Symmetry:** 0.5 (DREAM)

Nature demands a documentation counterpart. This formation maintains its narrative record in `docs/logos/`.

### The Tetradic Counterpart
- **[Telos (Idealized Form)](../docs/logos/telos.md)** — The dream and theoretical grounding.
- **[Pragma (Concrete State)](../docs/logos/pragma.md)** — The honest account of what exists.
- **[Praxis (Remediation Plan)](../docs/logos/praxis.md)** — The attack vectors for evolution.
- **[Receptio (Reception)](../docs/logos/receptio.md)** — The account of the constructed polis.

### Alchemical I/O
- **[Source & Transmutation](../docs/logos/alchemical-io.md)** — Narrative of inputs, process, and returns.



*Compliance: Record exists without implementation.*

<!-- ORGANVM:AUTO:END -->












## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.