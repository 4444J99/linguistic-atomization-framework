# Tutorial 1: Your First Analysis

Learn to analyze any document in under 5 minutes. No coding required.

---

## What You'll Learn

- How to run your first analysis
- How to read the results
- What the scores actually mean

## Prerequisites

- LingFrame installed ([see README](../../README.md))
- A document to analyze (PDF, TXT, MD, or DOCX)

---

## Quick Start: Command Line

The fastest way to analyze a document:

```bash
./new_venv/bin/python lingframe.py analyze your-document.pdf
```

That's it. LingFrame will:
1. Extract text from your document
2. Break it into themes, paragraphs, and sentences
3. Run rhetorical analysis
4. Generate an HTML report
5. Open it in your browser

### Example: Analyzing Shakespeare

Let's try it with The Tempest from our corpus:

```bash
./new_venv/bin/python lingframe.py analyze corpus/early-modern/tempest/original.txt
```

You'll see output like:

```
Analyzing: original.txt
==================================================
  Initializing analysis engine...
  Extracting text from document...
  Extracted 17,432 words
  Analyzing text structure...
  Found 89 themes, 412 paragraphs, 1,847 sentences
  Running heuristic rhetorical analysis...
  Analyzing themes and connections...
  Analyzing emotional tone...
  Generating narrative report...

Analysis complete!
Report: corpus/early-modern/tempest/original_analysis.html
```

Your browser opens with an interactive report.

### Quick Summary (No File Output)

Want just the key points without generating a file?

```bash
./new_venv/bin/python lingframe.py quick corpus/early-modern/tempest/original.txt
```

Output:

```
Quick Analysis: Original
==================================================

Overall Score: 67%

By Phase:
  Growth: 72%
  Evaluation: 68%
  Reinforcement: 65%
  Risk: 61%

Top Recommendations:
  1. Consider adding more concrete evidence to support claims
  2. Vary sentence structure to improve flow
  3. Strengthen transitions between major sections

Run 'lingframe analyze <file>' for a detailed report.
```

---

## Alternative: Web Interface

Prefer clicking to typing? Use the web interface:

```bash
./new_venv/bin/python run_web.py
```

Then open http://localhost:8501 in your browser.

1. **Upload** your document (drag & drop or click to browse)
2. **Click "Analyze"**
3. **Explore** the interactive results

The web interface shows the same analysis with tabs for:
- **Summary**: Overall scores and key findings
- **Details**: Step-by-step breakdown
- **Explore**: Interactive visualizations

---

## Understanding Your Results

### The Four Phases

LingFrame organizes analysis into four phases, each examining different aspects of your writing:

| Phase | What It Examines | Key Questions |
|-------|-----------------|---------------|
| **Evaluation** | Opening moves, thesis clarity | Does the introduction establish purpose? |
| **Reinforcement** | Evidence, support, development | Are claims backed by evidence? |
| **Risk** | Counterarguments, complexity | Does the text acknowledge complications? |
| **Growth** | Conclusions, implications | Does the ending provide closure and insight? |

### What the Scores Mean

Scores are **pattern density indicators**, not grades. They show how much your text exhibits certain rhetorical patterns.

| Score Range | Interpretation |
|-------------|----------------|
| 80-100% | High pattern density - many rhetorical markers present |
| 60-79% | Moderate density - typical for most writing |
| 40-59% | Lower density - may indicate focused/minimal style |
| Below 40% | Sparse patterns - worth investigating why |

**Important**: A lower score isn't necessarily bad. Technical documentation often scores lower on "emotional appeal" because it shouldn't have much. Academic writing might score lower on "personal voice" markers because it uses formal register.

### The Nine Steps

Within each phase, LingFrame checks specific rhetorical elements:

**Evaluation Phase**
1. **Attention Hook** - Does the opening grab interest?
2. **Context Setting** - Is background provided?
3. **Thesis Clarity** - Is the main point clear?

**Reinforcement Phase**
4. **Evidence Quality** - Are claims supported?
5. **Logical Flow** - Do ideas connect coherently?
6. **Voice Consistency** - Is tone maintained?

**Risk Phase**
7. **Counterargument** - Are objections addressed?
8. **Complexity** - Are nuances acknowledged?

**Growth Phase**
9. **Resolution** - Does the ending provide closure?

---

## Reading the Report

### Summary Tab

The summary shows:
- **Overall Score**: Aggregate of all phases
- **Phase Breakdown**: Score per phase with brief interpretation
- **Top Recommendations**: Actionable suggestions

### Details Tab

Expands each of the 9 steps showing:
- What was found (specific patterns detected)
- Confidence level (how certain the detection is)
- Example passages from your text

### Explore Tab

Interactive visualizations:
- **Theme Connections**: Network graph of how ideas relate
- **Emotional Journey**: Sentiment flow through the document
- **Narrative Timeline**: How tense shifts (past/present/future)
- **Entity Browser**: People, places, and things mentioned

---

## Common Questions

### "Why is my score low?"

Low scores indicate fewer detected patterns, not poor writing. Check:
- Is the text very short? (Fewer patterns possible)
- Is it a specific genre? (Technical writing has fewer emotional markers)
- Is it intentionally minimal? (Some styles are sparse by design)

### "The analysis seems wrong"

LingFrame uses heuristics (pattern matching), not AI understanding. It can:
- Miss sarcasm or irony
- Misidentify genre conventions
- Over-weight surface features

Use the scores as a starting point for reflection, not a definitive judgment.

### "How do I improve my score?"

Focus on the **recommendations**, not the numbers. The suggestions point to specific rhetorical elements you might strengthen. But remember: not all writing needs all patterns.

---

## Next Steps

- **[Tutorial 2: Comparative Analysis](02-comparative-analysis.md)** - Compare multiple texts
- **[Tutorial 3: Custom Domains](03-custom-domains.md)** - Create domain-specific analysis
- **[Tutorial 4: Building Modules](04-building-modules.md)** - Extend the framework

---

## Command Reference

```bash
# Full analysis with HTML report
./new_venv/bin/python lingframe.py analyze document.pdf

# Specify output location
./new_venv/bin/python lingframe.py analyze document.pdf -o report.html

# Custom document title
./new_venv/bin/python lingframe.py analyze document.pdf --title "My Essay"

# Also export raw JSON data
./new_venv/bin/python lingframe.py analyze document.pdf --json

# Verbose progress output
./new_venv/bin/python lingframe.py analyze document.pdf --verbose

# Quick console summary (no file)
./new_venv/bin/python lingframe.py quick document.pdf

# Web interface
./new_venv/bin/python run_web.py
```
