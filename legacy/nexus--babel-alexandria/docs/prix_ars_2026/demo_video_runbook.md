# Prix Ars Demo Video Runbook (3 minutes)

## Goal

Record a <=3 minute MP4 showing:

1. API startup
2. Scripted demo flow in terminal (`scripts/demo_sequence.py`)
3. FastAPI `/docs`
4. Timeline + remix comparison climax
5. Submission visuals (architecture diagram + atomization image)

## Pre-Flight

1. Install deps: `uv sync --extra dev` (or `uv run --extra dev ...`)
2. Verify tests: `uv run --extra dev pytest -q`
3. Generate visuals:
   - `uv run --extra dev python scripts/render_architecture_diagram.py`
   - `uv run --extra dev python scripts/visualize_atoms.py`
4. Dry-run demo script:
   - `uv run --extra dev python scripts/demo_sequence.py --dry-run`

## Recording Sequence (Suggested)

### 0:00 - 0:20 Startup

- Terminal A:
  - `uv run uvicorn nexus_babel.main:app --reload`
- Show `GET /healthz` success (optional quick curl)

### 0:20 - 0:40 API Surface

- Browser:
  - Open `/docs`
  - Scroll endpoints: ingest, analyze, governance, evolve, remix, remix retrieval

### 0:40 - 2:05 Scripted Demo

- Terminal B:
  - `uv run --extra dev python scripts/demo_sequence.py --base-url http://127.0.0.1:8000`
- Keep font size large enough for screen recording.
- Let the script print all ten steps without manual interruption.

### 2:05 - 2:35 Visual Assets

- Show:
  - `artifacts/prix-ars-2026/architecture_9_layer_plexus.png`
  - `artifacts/prix-ars-2026/atomization_visualization.png`

### 2:35 - 3:00 Closing Frame

- Return to terminal output highlighting:
  - remix artifact ID
  - branch timeline replay
  - branch compare distance/hash difference

## Capture Settings (Suggested)

- Resolution: 1920x1080
- Frame rate: 30fps
- Audio: optional (voiceover can be added later)
- Export target: H.264 MP4
- File size target: <=500MB

## Post-Processing Checklist

- Trim pauses >2s
- Ensure terminal text is readable at 100% zoom
- Verify total duration <=3:00
- Confirm final file opens cleanly and plays start-to-finish

## Output Path

- Target output: `artifacts/prix-ars-2026/nexus_babel_prix_ars_demo.mp4`

## Note

The actual desktop/screen recording step is intentionally manual because capture tooling and UI/window choreography depend on the operator's environment and preferred recorder (QuickTime, OBS, Screen Studio, etc.).
