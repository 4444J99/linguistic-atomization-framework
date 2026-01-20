# Legacy Scripts Archive

These scripts were the original implementation before the LingFrame refactoring.
They have been replaced by the modular framework architecture.

## Mapping to New Framework

| Legacy Script | Framework Replacement |
|---------------|----------------------|
| `atomize_manuscript.py` | `framework/core/atomizer.py` |
| `gemini_semantic_network.py` | `framework/analysis/semantic.py` |
| `jules_temporal_analysis.py` | `framework/analysis/temporal.py` |
| `copilot_sentiment_analysis.py` | `framework/analysis/sentiment.py` |
| `simple_entity_recognition.py` | `framework/analysis/entity.py` |
| `code_entity_recognition.py` | `framework/analysis/entity.py` |
| `create_modern_viz.py` | `framework/visualization/adapters/` |
| `create_standalone_viewer.py` | `framework/visualization/adapters/` |
| `create_visual_analysis.py` | `framework/visualization/adapters/` |
| `view_atomized.py` | Project visualization dashboard |

## Using the New Framework

```bash
# Run the full pipeline
./new_venv/bin/python lingframe.py run --project tomb-of-the-unknowns

# Or individual steps
./new_venv/bin/python lingframe.py atomize --project tomb-of-the-unknowns
./new_venv/bin/python lingframe.py analyze --project tomb-of-the-unknowns
./new_venv/bin/python lingframe.py visualize --project tomb-of-the-unknowns
```

## Archived Date
2026-01-20
