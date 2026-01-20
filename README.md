# 📚 Tomb of the Unknowns: Linguistic Analysis

Multi-agent AI-powered linguistic analysis of "Tomb of the Unknowns" with interactive visualizations.

## 🎯 Overview

This project uses 4 specialized AI agents (Gemini, Jules, Copilot, Code) to perform comprehensive linguistic analysis on a hierarchically atomized text, generating interactive HTML visualizations for exploring:

- **Semantic Networks** - Theme relationships and conceptual connections
- **Temporal Flow** - Narrative time progression and tense distribution  
- **Sentiment Analysis** - Emotional landscape with military-customized lexicon
- **Entity Recognition** - Named entities (persons, ranks, locations, equipment)

## 🚀 Quick Start

1. **Open the Dashboard:**
   ```bash
   open visualizations/index.html
   ```

2. **Or view individual visualizations:**
   - `visualizations/semantic_network.html` - Interactive force-directed graph (D3.js)
   - `visualizations/temporal_flow.html` - Timeline, Sankey, heatmap views (Plotly.js)
   - `visualizations/sentiment_map.html` - Emotional arc and theme comparison (Chart.js)
   - `visualizations/entity_browser.html` - Searchable entity database (Vanilla JS)

## 📊 Data Files

- `data/raw/Tomb_of_the_Unknowns_atomized.json` - Hierarchical source data (4 themes, 24 sentences, 225 words)
- `data/processed/semantic_data.json` - Theme similarity matrix (TF-IDF)
- `data/processed/temporal_data.json` - Tense distribution and temporal markers
- `data/processed/sentiment_data.json` - Sentence-level sentiment scores (VADER + custom lexicon)
- `data/processed/enhanced_atomized.json` - Source data + entity annotations
- `data/processed/entity_statistics.json` - Entity frequency and distribution

## 🤖 Analysis Scripts

All scripts live in `scripts/` and are Python 3.14 compatible:

```bash
# Regenerate semantic analysis
python3 scripts/gemini_semantic_network.py

# Regenerate temporal analysis  
python3 scripts/jules_temporal_analysis.py

# Regenerate sentiment analysis
python3 scripts/copilot_sentiment_analysis.py

# Regenerate entity recognition
python3 scripts/simple_entity_recognition.py
```

## 🎨 Features

✅ **Completed (100%)**
- ✓ Hierarchical text atomization
- ✓ 4 AI agent analysis pipelines
- ✓ 4 interactive HTML visualizations
- ✓ Master dashboard with navigation
- ✓ Glassmorphic UI design
- ✓ Real-time search and filtering
- ✓ Responsive layouts

## 🛠️ Technology Stack

- **Backend:** Python 3.14, NLTK, TextBlob, VADER, scikit-learn
- **Frontend:** D3.js v7, Plotly.js v2.27, Chart.js v4.4, Vanilla JS
- **Design:** Glassmorphism, CSS3 gradients, responsive grid

## 📈 Project Structure

```
├── scripts/                          # Python analysis + utility scripts
├── data/
│   ├── raw/                          # Source manuscript JSON
│   ├── processed/                    # Analysis outputs (semantic, temporal, sentiment, entities)
│   └── derived/                      # Human-readable indices/samples
├── visualizations/                   # Dashboard + individual HTML visualizations
├── docs/                             # Planning docs, project notes, source manuscripts (Markdown/PDF)
├── requirements.txt                  # Python dependencies
└── tomb_venv/                        # Local venv (optional, not tracked)
```

## 🎯 Success Metrics

All Phase 1 objectives achieved:
- ✅ 4/4 data analysis scripts executed
- ✅ 4/4 interactive visualizations created
- ✅ Master dashboard integrated
- ✅ All features functional (zoom, pan, search, filter)
- ✅ Performance: <2s load time per visualization
- ✅ Responsive design verified

## 📝 Documentation

- `PROJECT_INDEX.md` - Complete file inventory and coordination
- `AGENT_WORK_PACKAGES.md` - Technical specifications for each agent
- `AGENTIC_WORK_SUMMARY.md` - Quick start guide and data schemas
- `MASTER_COORDINATION.md` - Progress tracking dashboard
- `AGENT_HANDOFF_SYSTEM.md` - Packetized handoff instructions for Gemini, Jules, Copilot, and Code

## 🔮 Future Enhancements (Phase 2)

- Cross-visualization linking (click in one view → highlight in others)
- Unified search across all data sources
- Comparative analysis dashboards
- PDF report generation
- API endpoints for programmatic access
- Additional analyses: readability metrics, word clouds, stylometry

## 📄 License

Educational project - "Tomb of the Unknowns" text analysis

---

**Generated:** November 20, 2025 | **Status:** Phase 1 Complete ✅
