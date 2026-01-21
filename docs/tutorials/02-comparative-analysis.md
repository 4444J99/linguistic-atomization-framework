# Tutorial 2: Comparative Analysis

Compare multiple texts to understand how rhetorical strategies vary across works, genres, and eras.

---

## What You'll Learn

- How to analyze multiple documents
- How to interpret differences between texts
- Using projects for multi-document workflows
- Meaningful comparisons vs. misleading ones

## Prerequisites

- Completed [Tutorial 1: First Analysis](01-first-analysis.md)
- Multiple documents to compare (or use the included corpus)

---

## The Corpus: Classical to Modern

LingFrame includes a curated corpus for learning and experimentation:

```
corpus/
├── classical/
│   ├── odyssey/          Homer's Odyssey (Butler translation)
│   └── aeneid/           Virgil's Aeneid (Dryden translation)
├── medieval/
│   ├── beowulf/          Beowulf (Gummere translation)
│   ├── canterbury-tales/ Chaucer's Canterbury Tales
│   └── inferno/          Dante's Inferno (Longfellow translation)
├── early-modern/
│   └── tempest/          Shakespeare's The Tempest
└── modern/
    └── (your additions)
```

These texts span 2,500+ years of literary tradition—perfect for exploring how rhetorical strategies evolve.

---

## Quick Comparison: Side-by-Side Analysis

### Step 1: Analyze Each Text

```bash
# Analyze the three great epics
./new_venv/bin/python lingframe.py analyze corpus/classical/odyssey/english_butler.txt \
    --title "Odyssey (Homer)" -o odyssey_analysis.html --json

./new_venv/bin/python lingframe.py analyze corpus/classical/aeneid/english_dryden.txt \
    --title "Aeneid (Virgil)" -o aeneid_analysis.html --json

./new_venv/bin/python lingframe.py analyze corpus/medieval/beowulf/english_gummere.txt \
    --title "Beowulf" -o beowulf_analysis.html --json
```

The `--json` flag exports raw data for deeper comparison.

### Step 2: Quick Score Comparison

Use the quick command to see scores side-by-side:

```bash
./new_venv/bin/python lingframe.py quick corpus/classical/odyssey/english_butler.txt
./new_venv/bin/python lingframe.py quick corpus/classical/aeneid/english_dryden.txt
./new_venv/bin/python lingframe.py quick corpus/medieval/beowulf/english_gummere.txt
```

Example output comparison:

| Text | Overall | Evaluation | Reinforcement | Risk | Growth |
|------|---------|------------|---------------|------|--------|
| Odyssey | 64% | 71% | 62% | 58% | 66% |
| Aeneid | 68% | 69% | 70% | 63% | 69% |
| Beowulf | 61% | 65% | 59% | 54% | 67% |

---

## Interpreting Differences

### What Variations Mean

When comparing texts, differences might indicate:

1. **Genre conventions** - Epic poetry vs. drama vs. prose
2. **Era-specific rhetoric** - Ancient patterns differ from modern
3. **Translation effects** - Translator choices shape detected patterns
4. **Length effects** - Longer texts have more pattern opportunities

### Example: Epic Comparison

Looking at our three epics:

**Odyssey (Homer, ~8th century BCE)**
- Higher Evaluation score: Strong invocation tradition ("Sing, O Muse...")
- Episodic structure creates distinct thematic units
- Oral tradition markers (repetition, epithets)

**Aeneid (Virgil, 1st century BCE)**
- Higher Reinforcement: More developed argumentation style
- Roman rhetorical training shows in structured persuasion
- Political purpose creates clearer thesis elements

**Beowulf (Anonymous, ~8th-11th century CE)**
- Lower Risk score: Germanic heroic tradition less dialectical
- Strong Growth phase: Clear resolution patterns (monster defeated)
- Alliterative verse creates different sentence structures

### Caution: Translation Effects

These are all English translations. The scores reflect:
- Original author's rhetorical choices
- Translator's interpretation
- Target era's literary conventions

Butler's prose Odyssey reads differently than Lattimore's verse translation. Dryden's heroic couplets for the Aeneid differ from Fagles' modern verse.

**When comparing, note your translations.**

---

## Project-Based Comparison

For deeper analysis, create a project that holds multiple documents:

### Step 1: Create Project Structure

```bash
mkdir -p projects/epic-comparison/docs
mkdir -p projects/epic-comparison/data/processed
mkdir -p projects/epic-comparison/visualizations
```

### Step 2: Create Project Configuration

Create `projects/epic-comparison/project.yaml`:

```yaml
project:
  name: "epic-comparison"
  version: "1.0.0"
  description: "Comparative analysis of classical epics"

naming:
  strategy: hybrid

corpus:
  documents:
    - source: "../../corpus/classical/odyssey/english_butler.txt"
      title: "Odyssey (Homer)"
      id: "odyssey"
    - source: "../../corpus/classical/aeneid/english_dryden.txt"
      title: "Aeneid (Virgil)"
      id: "aeneid"
    - source: "../../corpus/medieval/beowulf/english_gummere.txt"
      title: "Beowulf"
      id: "beowulf"

domain:
  profile: base

analysis:
  pipelines:
    - module: semantic
    - module: temporal
    - module: sentiment
    - module: entity
    - module: evaluation

visualization:
  adapters:
    - type: force_graph
      analysis: semantic
    - type: sankey
      analysis: temporal
    - type: sentiment_chart
      analysis: sentiment
```

### Step 3: Run Full Pipeline

```bash
./new_venv/bin/python lingframe.py run -p epic-comparison --visualize --verbose
```

This generates:
- Atomized structures for each document
- All analysis modules for each
- Visualizations combining all texts

---

## Meaningful Comparisons

### Good Comparisons

| Comparison | Why It Works |
|-----------|--------------|
| Same author, different works | Controls for style, shows evolution |
| Same genre, different eras | Shows convention changes |
| Same topic, different positions | Reveals argumentative strategies |
| Original vs. translation | Shows translation choices |
| Draft vs. final | Shows revision patterns |

### Problematic Comparisons

| Comparison | Why It's Tricky |
|-----------|----------------|
| Poetry vs. technical manual | Genre expectations differ fundamentally |
| 500 words vs. 50,000 words | Length skews pattern detection |
| Different languages | LingFrame analyzes English patterns |
| Fiction vs. non-fiction | Rhetorical goals differ |

### Normalizing for Length

Longer texts naturally have more pattern opportunities. When comparing texts of very different lengths:

1. Compare **percentages**, not raw counts
2. Look at **distribution** across phases, not totals
3. Consider **density** (patterns per 1000 words)

---

## Case Study: Comedy vs. Tragedy

Let's compare Shakespeare's Tempest with the epic tradition:

```bash
./new_venv/bin/python lingframe.py quick corpus/early-modern/tempest/original.txt
```

**Key differences from epics:**

| Aspect | Epics | The Tempest |
|--------|-------|-------------|
| Structure | Narrative arc | Five-act dramatic |
| Voice | Third-person narration | Dialogue-driven |
| Length | 10,000-15,000 lines | ~4,000 lines |
| Resolution | Hero's fate | Multiple character arcs |

The Tempest may score differently not because it's "worse" but because:
- Drama uses dialogue, not exposition
- Characters argue, creating more Risk-phase patterns
- Shorter length concentrates patterns differently

---

## Exporting Comparison Data

### JSON for Spreadsheets

```bash
./new_venv/bin/python lingframe.py analyze text.txt --json
```

The JSON file contains structured data you can import into Excel, Google Sheets, or data analysis tools.

### Key Fields for Comparison

```json
{
  "evaluation": {
    "summary": {
      "overall_score": 67.5,
      "phase_scores": {
        "evaluation": 71.2,
        "reinforcement": 65.8,
        "risk": 61.3,
        "growth": 69.4
      }
    },
    "steps": [...]
  }
}
```

Extract `phase_scores` from each text's JSON for tabular comparison.

---

## Exercises

### Exercise 1: Era Comparison

Analyze all corpus texts and chart how these metrics change from Homer to Shakespeare:
- Emotional intensity (sentiment scores)
- Structural complexity (theme count)
- Rhetorical balance (phase score variance)

### Exercise 2: Translation Comparison

Find two different translations of the same work (e.g., multiple Odyssey translations) and compare:
- Do they produce similar scores?
- Where do they diverge most?
- What does this reveal about translation philosophy?

### Exercise 3: Your Own Corpus

Create a comparison project with:
- 3-5 texts on a theme you care about
- A hypothesis about how they'll differ
- Analysis to test your hypothesis

---

## Next Steps

- **[Tutorial 3: Custom Domains](03-custom-domains.md)** - Create specialized analysis profiles
- **[Tutorial 4: Building Modules](04-building-modules.md)** - Extend the framework

---

## Command Reference

```bash
# Analyze with JSON export
./new_venv/bin/python lingframe.py analyze file.txt --json

# Run full project pipeline
./new_venv/bin/python lingframe.py run -p project-name --visualize

# List available projects
./new_venv/bin/python lingframe.py list-projects

# Quick comparison of multiple files
for f in corpus/classical/*/*.txt; do
    echo "=== $f ==="
    ./new_venv/bin/python lingframe.py quick "$f"
done
```
