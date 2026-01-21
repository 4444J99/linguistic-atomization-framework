# LingFrame Methodology

A practical guide to using LingFrame for scholarly text analysis.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Research Design](#research-design)
3. [Analysis Workflow](#analysis-workflow)
4. [Reproducibility Protocol](#reproducibility-protocol)
5. [Validation Framework](#validation-framework)
6. [Limitations & Appropriate Use](#limitations--appropriate-use)
7. [Citation Guidelines](#citation-guidelines)

---

## Introduction

LingFrame is a computational framework for rhetorical analysis that transforms text into hierarchical structures and applies specialized analysis modules. This document provides guidance for researchers using LingFrame in scholarly work.

### What LingFrame Does

LingFrame automates certain aspects of rhetorical analysis:

1. **Text Atomization**: Decomposes text into hierarchical units (theme → paragraph → sentence → word)
2. **Pattern Detection**: Identifies linguistic markers associated with rhetorical strategies
3. **Visualization**: Generates interactive representations of analytical findings
4. **Reproducibility**: Tracks analysis parameters for replication

### What LingFrame Does NOT Do

LingFrame cannot:
- Evaluate rhetorical effectiveness or persuasiveness
- Assess argument validity or logical soundness
- Judge appropriateness of rhetorical strategies
- Replace human interpretive analysis

Researchers should use LingFrame findings as **evidence for interpretation**, not as **conclusions themselves**.

---

## Research Design

### Appropriate Research Questions

LingFrame is suitable for questions about:

- **Pattern distribution**: "How are emotional appeals distributed across this speech?"
- **Structural relationships**: "What themes cluster together in this corpus?"
- **Comparative analysis**: "How do rhetorical strategies differ between these two texts?"
- **Temporal analysis**: "How does tense usage shift across the narrative?"

### Less Appropriate Research Questions

LingFrame alone cannot address:

- **Effectiveness questions**: "Was this speech persuasive?"
- **Intent questions**: "What did the author mean by this?"
- **Evaluative questions**: "Is this good writing?"

### Mixed Methods Approach

We recommend integrating LingFrame with:

1. **Close reading**: Human analysis of key passages
2. **Contextual research**: Historical, biographical, and cultural context
3. **Audience research**: Reception studies, reader response data
4. **Expert evaluation**: Peer review of interpretations

---

## Analysis Workflow

### Step 1: Corpus Preparation

1. Select texts appropriate to research question
2. Ensure clean, machine-readable format (plain text, PDF, or DOCX)
3. Document source, edition, and any preprocessing

```bash
# Example: Analyze a single document
./lingframe.py analyze essay.pdf

# Example: Set up a project for comparative analysis
./lingframe.py init -p literary-analysis/my-corpus
```

### Step 2: Configuration

Create a project configuration specifying:

```yaml
# project.yaml
project:
  name: "my-corpus"
  version: "1.0.0"

corpus:
  documents:
    - source: "docs/text1.txt"
      title: "First Text"
    - source: "docs/text2.txt"
      title: "Second Text"

domain:
  profile: base  # or: military, literary, academic

analysis:
  pipelines:
    - module: semantic
    - module: temporal
    - module: sentiment
    - module: entity
```

### Step 3: Analysis Execution

```bash
# Run full pipeline
./lingframe.py run -p literary-analysis/my-corpus --visualize

# Or run individual modules
./lingframe.py atomize -p literary-analysis/my-corpus
./lingframe.py analyze -p literary-analysis/my-corpus
./lingframe.py visualize -p literary-analysis/my-corpus
```

### Step 4: Interpretation

1. Review generated visualizations
2. Identify patterns of interest
3. Return to source texts for close reading
4. Contextualize findings within theoretical framework
5. Document interpretive decisions

---

## Reproducibility Protocol

LingFrame generates audit trails for all analyses.

### Analysis Provenance

Each output file includes metadata:

```json
{
  "metadata": {
    "version": "1.0.0",
    "generated_at": "2026-01-20T15:30:00Z",
    "framework_version": "0.1.0",
    "parameters": {
      "domain_profile": "military",
      "naming_strategy": "hybrid"
    }
  }
}
```

### Replication Checklist

For other researchers to replicate your analysis:

1. **Source texts**: Provide exact editions/versions used
2. **Configuration**: Include project.yaml in supplementary materials
3. **Framework version**: Specify LingFrame version (use git commit hash for development versions)
4. **Domain customizations**: Include any custom lexicons or patterns

### Revision Comparison

LingFrame tracks changes across document revisions:

```bash
# Compare two versions of a document
./lingframe.py compare docs/draft_v1.txt docs/draft_v2.txt
```

---

## Validation Framework

### Module-Level Validation

Each analysis module has known limitations:

| Module | Detects | Misses | False Positives |
|--------|---------|--------|-----------------|
| **Sentiment** | Emotional vocabulary, intensifiers | Irony, understatement | Neutral use of emotional words |
| **Semantic** | TF-IDF keyword clusters | Context-dependent meaning | Domain-specific terminology |
| **Temporal** | Verb tense patterns | Modals, conditionals | Irregular verb forms |
| **Entity** | Named entities, references | Pronouns, implicit references | Common nouns matching patterns |

### Recommended Validation Steps

1. **Sample verification**: Manually check 10-20% of flagged items
2. **Domain calibration**: Adjust domain profiles for specialized texts
3. **Comparative baseline**: Analyze texts with known characteristics
4. **Inter-rater reliability**: Have multiple researchers review interpretations

### Reporting Validation

In publications, report:

- Percentage of flagged items manually verified
- Types and frequency of false positives/negatives encountered
- Any domain customizations applied
- Limitations specific to your corpus

---

## Limitations & Appropriate Use

### Known Limitations

1. **Surface-level analysis**: LingFrame detects linguistic markers, not rhetorical effectiveness
2. **Context blindness**: Cannot account for historical, cultural, or situational context
3. **English-centric**: Optimized for English; other languages may produce unreliable results
4. **Genre sensitivity**: Calibrated for persuasive prose; other genres may require adjustment

### Appropriate Claims

**Appropriate**: "LingFrame analysis identified 47 instances of emotional vocabulary in paragraphs 3-7, suggesting the author's use of pathos is concentrated in this section."

**Inappropriate**: "LingFrame proves this speech is highly emotional and persuasive."

### Ethical Considerations

- **Transparency**: Disclose use of computational analysis
- **Human judgment**: Present findings as evidence for interpretation, not conclusions
- **Methodological humility**: Acknowledge framework limitations
- **Reproducibility**: Enable replication of analyses

---

## Citation Guidelines

### Citing LingFrame

```
LingFrame (Version X.X.X) [Computer software]. (Year). 
Retrieved from https://github.com/4444J99/linguistic-atomization-framework
```

### Citing Specific Modules

When analysis relies heavily on a particular module:

```
Sentiment analysis performed using LingFrame's VADER-based sentiment module 
(LingFrame v0.1.0), which combines VADER (Hutto & Gilbert, 2014) with 
domain-specific lexicons.
```

### Citing Theoretical Framework

LingFrame draws on multiple theoretical traditions. Cite original sources:

- **Aristotle's Rhetoric**: Aristotle. (trans. 2004). *Rhetoric*. W. Rhys Roberts, Trans.
- **VADER**: Hutto, C.J. & Gilbert, E.E. (2014). VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text.
- **Rhetorical Structure Theory**: Mann, W.C. & Thompson, S.A. (1988). Rhetorical Structure Theory: Toward a functional theory of text organization.

---

## Appendix: Quick Reference

### Command Reference

| Command | Purpose |
|---------|---------|
| `lingframe.py analyze <file>` | Quick analysis with HTML report |
| `lingframe.py quick <file>` | Console summary only |
| `lingframe.py run -p <project>` | Full project pipeline |
| `lingframe.py compare <v1> <v2>` | Revision comparison |

### Output Files

| Pattern | Content |
|---------|---------|
| `*_semantic_*.json` | Theme network data |
| `*_sentiment_*.json` | Sentiment arc data |
| `*_temporal_*.json` | Tense flow data |
| `*_entity_*.json` | Entity extraction data |

### Visualization Types

| Type | Best For |
|------|----------|
| Force Graph | Theme relationships |
| Sankey Diagram | Temporal flow |
| Line Chart | Sentiment arc |
| Browser | Entity exploration |
