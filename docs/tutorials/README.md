# LingFrame Tutorials

Progressive tutorials from first analysis to framework extension.

---

## Learning Path

| Tutorial | Audience | Time | Description |
|----------|----------|------|-------------|
| [01: First Analysis](01-first-analysis.md) | Everyone | 10 min | Analyze your first document |
| [02: Comparative Analysis](02-comparative-analysis.md) | Researchers | 20 min | Compare multiple texts |
| [03: Custom Domains](03-custom-domains.md) | Power users | 30 min | Create specialized analysis profiles |
| [04: Building Modules](04-building-modules.md) | Developers | 45 min | Extend the framework |

---

## Quick Start

**Just want to analyze a document?**

```bash
./new_venv/bin/python lingframe.py analyze your-document.pdf
```

**Prefer a web interface?**

```bash
./new_venv/bin/python run_web.py
# Open http://localhost:8501
```

---

## Sample Corpus

The tutorials use texts from the included corpus:

```
corpus/
├── classical/
│   ├── odyssey/       Homer's Odyssey (Butler translation)
│   └── aeneid/        Virgil's Aeneid (Dryden translation)
├── medieval/
│   ├── beowulf/       Beowulf (Gummere translation)
│   ├── canterbury-tales/  Chaucer's Canterbury Tales
│   └── inferno/       Dante's Inferno (Longfellow translation)
└── early-modern/
    └── tempest/       Shakespeare's The Tempest
```

These texts are public domain and span 2,500+ years of literary tradition.

---

## Prerequisites

Before starting, ensure you have:

1. **Python 3.9+** installed
2. **LingFrame dependencies** installed:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

See the [main README](../../README.md) for full setup instructions.

---

## Getting Help

- **Documentation**: Check `docs/` for architecture and theory
- **Issues**: Report bugs at the project repository
- **Examples**: See `projects/` for sample project configurations
