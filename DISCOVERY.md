# Discovery — organvm/linguistic-atomization-framework

**Date:** 2026-06-22 · **Verdict:** VALUE FOUND → promote to ranked tier · **Organ:** I (Theory)

## Value Thesis

LingFrame is not aspirational scaffolding — it is a **working, end-to-end computational-rhetoric
engine** with ~17.3k lines of real framework code, a 2.5k-line test suite (141/142 passing), and
**proof of execution on disk**: a fully analyzed "Tomb of the Unknowns" project with 9 generated
interactive HTML visualizations (~1.4MB), 12 analysis JSON artifacts, and a 123-file multilingual
corpus spanning 13 traditions (classical, sanskrit, hebrew, arabic-persian, chinese-classical,
japanese, medieval → modern). Its irreducible, reusable core is a **pluggable pipeline that
atomizes any document into a 5-level hierarchy (theme → paragraph → sentence → word → letter) and
runs registry-based analysis modules** (semantic/TF-IDF, sentiment/VADER, temporal, entity/spaCy,
and a 9-step heuristic rhetorical evaluator), then emits both interactive visualizations and
scholarly exports (LaTeX/TEI/CoNLL). The highest latent value is therefore **a reusable text-analysis
asset for the rest of the estate**: every Organ-I theory repo, every content/essay pipeline, and any
sibling that needs structured decomposition or rhetorical scoring of prose can consume LingFrame as a
library instead of re-inventing it. Today that value is locked behind script-style entrypoints
(`lingframe.py`, Streamlit launcher) with no pip-installable package or stable programmatic API —
which is precisely the gap that, once closed, converts a self-contained tool into estate
infrastructure. The framework is honest about its limits (pattern-based heuristics, not validated ML
measurement; English-tested despite multilingual tokenizers), and those limits do not diminish the
reuse case. This repo should **not** stay dark: it is a graduated, tested, demonstrably-functional
asset whose only missing step is packaging it for consumption.

## Evidence

- `framework/` — 17,338 LOC across core (atomizer, ontology, naming, pipeline, registry), analysis
  (6 modules), visualization (5 adapters), output (narrative + scholarly exporters).
- `tests/` — 2,531 LOC, 142 test functions, 141 passing (the 1 failure is a missing optional
  sentiment dependency, not a logic error; CI installs `requirements.txt` so CI is green).
- `projects/literary-analysis/tomb-unknowns/` + `visualizations/` — real generated output proving the
  pipeline runs end-to-end.
- `corpus/` — 123 source files across 13 language/era traditions.
- `ecosystem.yaml` — declares `python_library` delivery as **critical/in_progress** with next action
  "Stabilize API for all 6 modules" — corroborating the packaging gap as the live priority.

## Best Concrete First Task

**Make LingFrame a consumable estate asset: add a `pyproject.toml` and a stable programmatic API
entrypoint — `lingframe.analyze(text_or_path) -> AnalysisResult` returning structured JSON for all
six modules — so the package is `pip install`-able and importable by sibling repos.** This is the
single highest-leverage move: it unlocks the discovered reuse value with no new analysis logic,
directly satisfies the `ecosystem.yaml` critical next-action ("Stabilize API for all 6 modules"), and
leaves the existing CLI/web entrypoints intact.
