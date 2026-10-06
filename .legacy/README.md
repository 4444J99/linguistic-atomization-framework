# Legacy Scripts Archive

These scripts were the original implementation before the LingFrame refactoring.
They have been replaced by the modular framework architecture.

They are kept for historical reference only and **are not runnable**: they read
input data and a `scripts/project_paths.py` helper that are no longer in this
repository (the third-party manuscript they were first written against was
removed in October 2026, together with the manuscript-specific
`atomize_manuscript.py` and `create_standalone_viewer.py`).

## Mapping to New Framework

| Legacy Script | Framework Replacement |
|---------------|----------------------|
| `gemini_semantic_network.py` | `framework/analysis/semantic.py` |
| `jules_temporal_analysis.py` | `framework/analysis/temporal.py` |
| `copilot_sentiment_analysis.py` | `framework/analysis/sentiment.py` |
| `simple_entity_recognition.py` | `framework/analysis/entity.py` |
| `code_entity_recognition.py` | `framework/analysis/entity.py` |
| `create_modern_viz.py` | `framework/visualization/adapters/` |
| `create_visual_analysis.py` | `framework/visualization/adapters/` |
| `view_atomized.py` | Project visualization dashboard |

## Using the New Framework

```bash
# Quick analysis of any text file
lingframe quick tests/fixtures/sample_rhetoric.txt

# Run the full project pipeline on the bundled sample project
lingframe run -p literary-analysis/MET4MORFOSES

# Or individual steps
lingframe atomize -p literary-analysis/MET4MORFOSES
lingframe analyze -p literary-analysis/MET4MORFOSES
lingframe visualize -p literary-analysis/MET4MORFOSES
```

## Archived Date
2026-01-20
