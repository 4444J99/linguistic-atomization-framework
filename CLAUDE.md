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
`recursive-engine--generative-entity`, `organon-noumenon--ontogenetic-morphe`, `auto-revision-epistemic-engine`, `narratological-algorithmic-lenses`, `call-function--ontological`, `sema-metra--alchemica-mundi`, `cognitive-archaelogy-tribunal`, `a-recursive-root`, `radix-recursiva-solve-coagula-redi`, `.github`, `nexus--babel-alexandria`, `4-ivi374-F0Rivi4`, `cog-init-1-0-`, `my-knowledge-base`, `scalable-lore-expert` ... and 5 more

### Governance
- Foundational theory layer. No upstream dependencies.

*Last synced: 2026-03-20T10:58:25Z*

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


## Active Directives

| Scope | Phase | Name | Description |
|-------|-------|------|-------------|
| system | any | prompting-standards | Prompting Standards |
| system | any | research-standards-bibliography | APPENDIX: Research Standards Bibliography |
| system | any | phase-closing-and-forward-plan | METADOC: Phase-Closing Commemoration & Forward Attack Plan |
| system | any | research-standards | METADOC: Architectural Typology & Research Standards |
| system | any | sop-ecosystem | METADOC: SOP Ecosystem — Taxonomy, Inventory & Coverage |
| system | any | autonomous-content-syndication | SOP: Autonomous Content Syndication (The Broadcast Protocol) |
| system | any | autopoietic-systems-diagnostics | SOP: Autopoietic Systems Diagnostics (The Mirror of Eternity) |
| system | any | background-task-resilience | background-task-resilience |
| system | any | cicd-resilience-and-recovery | SOP: CI/CD Pipeline Resilience & Recovery |
| system | any | community-event-facilitation | SOP: Community Event Facilitation (The Dialectic Crucible) |
| system | any | context-window-conservation | context-window-conservation |
| system | any | conversation-to-content-pipeline | SOP — Conversation-to-Content Pipeline |
| system | any | cross-agent-handoff | SOP: Cross-Agent Session Handoff |
| system | any | cross-channel-publishing-metrics | SOP: Cross-Channel Publishing Metrics (The Echo Protocol) |
| system | any | data-migration-and-backup | SOP: Data Migration and Backup Protocol (The Memory Vault) |
| system | any | document-audit-feature-extraction | SOP: Document Audit & Feature Extraction |
| system | any | dynamic-lens-assembly | SOP: Dynamic Lens Assembly |
| system | any | essay-publishing-and-distribution | SOP: Essay Publishing & Distribution |
| system | any | formal-methods-applied-protocols | SOP: Formal Methods Applied Protocols |
| system | any | formal-methods-master-taxonomy | SOP: Formal Methods Master Taxonomy (The Blueprint of Proof) |
| system | any | formal-methods-tla-pluscal | SOP: Formal Methods — TLA+ and PlusCal Verification (The Blueprint Verifier) |
| system | any | generative-art-deployment | SOP: Generative Art Deployment (The Gallery Protocol) |
| system | any | market-gap-analysis | SOP: Full-Breath Market-Gap Analysis & Defensive Parrying |
| system | any | mcp-server-fleet-management | SOP: MCP Server Fleet Management (The Server Protocol) |
| system | any | multi-agent-swarm-orchestration | SOP: Multi-Agent Swarm Orchestration (The Polymorphic Swarm) |
| system | any | network-testament-protocol | SOP: Network Testament Protocol (The Mirror Protocol) |
| system | any | open-source-licensing-and-ip | SOP: Open Source Licensing and IP (The Commons Protocol) |
| system | any | performance-interface-design | SOP: Performance Interface Design (The Stage Protocol) |
| system | any | pitch-deck-rollout | SOP: Pitch Deck Generation & Rollout |
| system | any | polymorphic-agent-testing | SOP: Polymorphic Agent Testing (The Adversarial Protocol) |
| system | any | promotion-and-state-transitions | SOP: Promotion & State Transitions |
| system | any | recursive-study-feedback | SOP: Recursive Study & Feedback Loop (The Ouroboros) |
| system | any | repo-onboarding-and-habitat-creation | SOP: Repo Onboarding & Habitat Creation |
| system | any | research-to-implementation-pipeline | SOP: Research-to-Implementation Pipeline (The Gold Path) |
| system | any | security-and-accessibility-audit | SOP: Security & Accessibility Audit |
| system | any | session-self-critique | session-self-critique |
| system | any | smart-contract-audit-and-legal-wrap | SOP: Smart Contract Audit and Legal Wrap (The Ledger Protocol) |
| system | any | source-evaluation-and-bibliography | SOP: Source Evaluation & Annotated Bibliography (The Refinery) |
| system | any | stranger-test-protocol | SOP: Stranger Test Protocol |
| system | any | strategic-foresight-and-futures | SOP: Strategic Foresight & Futures (The Telescope) |
| system | any | styx-pipeline-traversal | SOP: Styx Pipeline Traversal (The 7-Organ Transmutation) |
| system | any | system-dashboard-telemetry | SOP: System Dashboard Telemetry (The Panopticon Protocol) |
| system | any | the-descent-protocol | the-descent-protocol |
| system | any | the-membrane-protocol | the-membrane-protocol |
| system | any | theoretical-concept-versioning | SOP: Theoretical Concept Versioning (The Epistemic Protocol) |
| system | any | theory-to-concrete-gate | theory-to-concrete-gate |
| system | any | typological-hermeneutic-analysis | SOP: Typological & Hermeneutic Analysis (The Archaeology) |
| unknown | any | gpt-to-os | SOP_GPT_TO_OS.md |
| unknown | any | index | SOP_INDEX.md |
| unknown | any | obsidian-sync | SOP_OBSIDIAN_SYNC.md |

Linked skills: cicd-resilience-and-recovery, continuous-learning-agent, evaluation-to-growth, genesis-dna, multi-agent-workforce-planner, promotion-and-state-transitions, quality-gate-baseline-calibration, repo-onboarding-and-habitat-creation, structural-integrity-audit


**Prompting (Anthropic)**: context 200K tokens, format: XML tags, thinking: extended thinking (budget_tokens)


## Ecosystem Status

- **delivery**: 0/3 live, 1 planned
- **content**: 0/2 live, 1 planned

Run: `organvm ecosystem show linguistic-atomization-framework` | `organvm ecosystem validate --organ I`


## Entity Identity (Ontologia)

**UID:** `ent_repo_01KKKX3RVH6Z016KF497FKD1E1` | **Matched by:** primary_name

Resolve: `organvm ontologia resolve linguistic-atomization-framework` | History: `organvm ontologia history ent_repo_01KKKX3RVH6Z016KF497FKD1E1`


## Live System Variables (Ontologia)

| Variable | Value | Scope | Updated |
|----------|-------|-------|---------|
| `active_repos` | 1 | global | 2026-03-20 |
| `archived_repos` | 0 | global | 2026-03-20 |
| `ci_workflows` | 1 | global | 2026-03-20 |
| `code_files` | 0 | global | 2026-03-20 |
| `dependency_edges` | 0 | global | 2026-03-20 |
| `operational_organs` | 1 | global | 2026-03-20 |
| `published_essays` | 0 | global | 2026-03-20 |
| `repos_with_tests` | 0 | global | 2026-03-20 |
| `sprints_completed` | 0 | global | 2026-03-20 |
| `test_files` | 0 | global | 2026-03-20 |
| `total_organs` | 1 | global | 2026-03-20 |
| `total_repos` | 1 | global | 2026-03-20 |
| `total_words_formatted` | 0 | global | 2026-03-20 |
| `total_words_numeric` | 0 | global | 2026-03-20 |
| `total_words_short` | 0K+ | global | 2026-03-20 |

Metrics: 9 registered | Observations: 7184 recorded
Resolve: `organvm ontologia status` | Refresh: `organvm refresh`


## System Density (auto-generated)

AMMOI: 54% | Edges: 28 | Tensions: 33 | Clusters: 5 | Adv: 3 | Events(24h): 12929
Structure: 8 organs / 117 repos / 1654 components (depth 17) | Inference: 98% | Organs: META-ORGANVM:66%, ORGAN-I:55%, ORGAN-II:47%, ORGAN-III:56% +4 more
Last pulse: 2026-03-20T10:58:23 | Δ24h: -3.7% | Δ7d: n/a

<!-- ORGANVM:AUTO:END -->


## ⚡ Conductor OS Integration
This repository is a managed component of the ORGANVM meta-workspace.
- **Orchestration:** Use `conductor patch` for system status and work queue.
- **Lifecycle:** Follow the `FRAME -> SHAPE -> BUILD -> PROVE` workflow.
- **Governance:** Promotions are managed via `conductor wip promote`.
- **Intelligence:** Conductor MCP tools are available for routing and mission synthesis.
