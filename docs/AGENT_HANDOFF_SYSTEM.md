# Multi-Agent Handoff System
Operational playbook for packaging, sending, and receiving work between Gemini, Jules, Copilot, and Code.

## How to Use
- Build a **handoff packet** per agent: required files, short brief, acceptance checklist, and return format.
- Send only the files listed in each packet (avoid entire repo); include current commit hash or file versions.
- On return, run the acceptance checklist before merging outputs.

## Standard Packet Template
1. **Brief**: Goal, success criteria, deadline, and expected outputs (filenames).
2. **Inputs**: Exact paths and line ranges to read; data files; dependencies.
3. **Commands to run**: Copy/paste ready.
4. **Return format**: Files to send back and a short report template.
5. **Acceptance checklist**: What you will verify on receipt.

## Agent Packets

### Gemini (Semantic Network, D3.js)
- **Brief**: Build/upgrade `visualizations/semantic_network.html` from `data/processed/semantic_data.json` (force-directed graph with filters/search/export).
- **Inputs**: `docs/AGENT_WORK_PACKAGES.md` (Gemini section), `scripts/gemini_semantic_network.py`, `data/processed/semantic_data.json`.
- **Commands**: None (front-end only). If data regeneration needed: `python3 scripts/gemini_semantic_network.py`.
- **Return**: Updated `visualizations/semantic_network.html` + short report:
  - What changed (controls, interactions, styling)
  - Data fields used (nodes/edges schema)
  - Manual test notes (load, hover, search, export)
- **Acceptance checklist**:
  - File loads without console errors; links respect similarity threshold.
  - Search highlights node; zoom/pan works; export works or is gracefully disabled.
  - Uses data from `../data/processed/semantic_data.json` (relative path OK offline).

### Jules (Temporal Flow, Plotly)
- **Brief**: Implement timeline, Sankey, and heatmap in `visualizations/temporal_flow.html` from `data/processed/temporal_data.json`.
- **Inputs**: `docs/AGENT_WORK_PACKAGES.md` (Jules section), `scripts/jules_temporal_analysis.py`, `data/processed/temporal_data.json`.
- **Commands**: `python3 scripts/jules_temporal_analysis.py` if data refresh requested.
- **Return**: Updated `visualizations/temporal_flow.html` + short report:
  - Which views implemented; mapping of JSON fields to traces
  - Hover text content; known limitations
- **Acceptance checklist**:
  - All three views render; color legend for tense; hover shows sentence snippets.
  - Handles missing fields with user-friendly messaging; no hard-coded data.

### Copilot (Sentiment Map, Chart.js)
- **Brief**: Emotional arc + heatmap/table in `visualizations/sentiment_map.html` from `data/processed/sentiment_data.json`.
- **Inputs**: `docs/AGENT_WORK_PACKAGES.md` (Copilot section), `scripts/copilot_sentiment_analysis.py`, `data/processed/sentiment_data.json`.
- **Commands**: `python3 scripts/copilot_sentiment_analysis.py` if data refresh requested.
- **Return**: Updated `visualizations/sentiment_map.html` + short report:
  - Datasets used, rolling window settings, peak/valley logic
  - Manual test results (load, tab switches, responsiveness)
- **Acceptance checklist**:
  - Line chart renders; heatmap shows theme/bin data; top sentences link to IDs.
  - Rolling average slider (or documented default); graceful handling of missing data.

### Code (Entity Recognition & Browser)
- **Brief**: Run spaCy entity extraction and build `visualizations/entity_browser.html` using `data/processed/enhanced_atomized.json` + `entity_statistics.json`.
- **Inputs**: `docs/AGENT_WORK_PACKAGES.md` (Code section), `scripts/code_entity_recognition.py`, `data/raw/Tomb_of_the_Unknowns_atomized.json`.
- **Commands**:
  - `pip install -r requirements.txt`
  - `python3 -m spacy download en_core_web_trf` (or `en_core_web_sm` fallback)
  - `python3 scripts/code_entity_recognition.py`
- **Return**: Updated `enhanced_atomized.json`, `entity_statistics.json`, and `visualizations/entity_browser.html` + short report:
  - Model used, entity types, counts, known false positives
  - UI filters/search features implemented
- **Acceptance checklist**:
  - JSONs present and loadable; entity counts sensible (no TODO titles).
  - Browser loads, filters by type, search works; handles empty results cleanly.

## Handoff/Return Workflow
1. Prepare packet (template above) and zip only required files if needed.
2. Send packet with due time and acceptance checklist.
3. On return, run: `python3 -c "import json; json.load(open('data/processed/...'))"` for each JSON; open the HTMLs; note console errors.
4. Capture outcomes in `docs/AGENTIC_WORK_SUMMARY.md` under a dated entry.

## Single-Message Prompts (copy/paste)
- **Gemini**: “Load `docs/AGENT_WORK_PACKAGES.md` (Gemini section), `data/processed/semantic_data.json`. Update `visualizations/semantic_network.html` with force-directed graph, filters (entity type, similarity threshold), search, and export. Return file + report (changes, data fields used, manual test notes).”
- **Jules**: “Use `data/processed/temporal_data.json` to build timeline, Sankey, heatmap in `visualizations/temporal_flow.html` (Plotly). Include hover text with sentence snippets. Return file + report (views, field mapping, test notes).”
- **Copilot**: “Use `data/processed/sentiment_data.json` to build emotional arc + heatmap/table in `visualizations/sentiment_map.html` (Chart.js). Add rolling average (window=10 default). Return file + report (datasets, slider/default, tests).”
- **Code**: “Install spaCy model, run `scripts/code_entity_recognition.py`, then build `visualizations/entity_browser.html` from `data/processed/enhanced_atomized.json` and `entity_statistics.json`. Return updated JSONs + HTML + report (model used, counts, filters/search).”

## Acceptance Log (fill on receipt)
- Date:
- Agent:
- Files received:
- Checks run (data load, UI smoke, console):
- Issues found / follow-ups:
