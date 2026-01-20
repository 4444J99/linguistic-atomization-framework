# Scope & Limitations

This document provides an honest assessment of what LingFrame can and cannot do. Understanding these limitations is essential for appropriate use and interpretation of results.

---

## What LingFrame Is

LingFrame is a **heuristic analysis tool** that:

- Decomposes text into hierarchical structures
- Applies pattern-matching rules to detect linguistic markers
- Calculates density metrics across structural levels
- Generates visualizations of detected patterns
- Produces reports with findings and recommendations

## What LingFrame Is Not

### Not a Validated Assessment Instrument

LingFrame's scores have **not been empirically validated** against:
- Human expert judgments
- Established rhetorical assessment frameworks
- Academic writing rubrics
- Professional editing standards

The scores are **heuristic indicators** that highlight patterns for human interpretation. They should not be treated as definitive quality measurements.

### Not a Replacement for Human Expertise

LingFrame cannot:
- Evaluate argument validity (only presence of evidence markers)
- Assess factual accuracy
- Judge appropriateness for audience or context
- Understand authorial intent
- Recognize sophisticated rhetorical strategies beyond pattern matching

A human rhetorician, editor, or domain expert provides qualitative judgment that pattern matching cannot replicate.

### Not a Writing Correction Tool

LingFrame:
- Does not fix grammar or spelling
- Does not rewrite sentences
- Does not generate improved text (yet—this is on the roadmap)
- Does not replace tools like Grammarly or Hemingway Editor

### Not Generative AI

Current LingFrame:
- Analyzes existing text
- Does not produce new text
- Does not suggest specific rewrites
- Does not iterate on its own recommendations

The generation layer is planned but not yet implemented.

---

## Technical Limitations

### Pattern Matching Brittleness

**What it means**: LingFrame uses regex patterns and keyword lists to detect linguistic markers. This approach:

- Produces false positives (detecting patterns that aren't rhetorically meaningful)
- Produces false negatives (missing sophisticated rhetoric that doesn't match patterns)
- Cannot understand semantic meaning or context
- Is sensitive to surface-level variations

**Example**: The pattern for "evidence markers" might flag the word "statistics" in "I don't trust statistics" as positive evidence, missing the negation.

### Fixed Aggregation Weights

**What it means**: Level aggregation uses fixed weights:
- Letter: 5%
- Word: 15%
- Sentence: 35%
- Paragraph: 30%
- Theme: 15%

These weights:
- Don't adapt to document structure or genre
- May not reflect rhetorical importance in all contexts
- Are based on intuition, not empirical research

### English-Only Analysis

**What it means**: LingFrame's patterns, lexicons, and NER models are designed for English. Using it with other languages will produce:
- Incorrect tokenization
- Missed patterns
- Inaccurate sentiment scores
- Entity recognition failures

Multi-language support is not currently available.

### Western Rhetorical Tradition Bias

**What it means**: The rhetorical framework (Logos/Pathos/Ethos) derives from classical Western tradition. This may:
- Miss rhetorical strategies from other traditions
- Impose inappropriate evaluation criteria on non-Western texts
- Privilege certain argument structures over others

### Length Bias

**What it means**: Density-based metrics may favor:
- Longer documents (more opportunities for pattern matches)
- Denser prose styles (more markers per sentence)
- Certain genres over others

Short, intentionally sparse texts may score poorly on metrics designed for argumentative prose.

---

## Interpretive Limitations

### Scores Are Not Quality Judgments

A high Pathos score doesn't mean the emotional appeal is effective—it means emotional markers were detected. Effectiveness depends on:
- Audience
- Context
- Appropriateness
- Execution quality

LingFrame cannot judge these factors.

### Recommendations Are Generic

Current recommendations:
- Point to detected weaknesses
- Suggest categories of improvement
- Do not provide specific fixes
- May not account for genre or context

A recommendation to "add more evidence" doesn't know whether evidence is appropriate for the text type.

### No Semantic Understanding

LingFrame doesn't understand:
- What the text is about
- Whether arguments are logically valid
- Whether evidence supports claims
- Whether emotional appeals are appropriate

It detects patterns, not meaning.

---

## Known Blind Spots

### Things LingFrame Misses

1. **Irony and sarcasm**: Pattern matching treats all text literally
2. **Extended metaphors**: Can't trace metaphorical arguments
3. **Structural parallelism**: Beyond simple pattern detection
4. **Genre conventions**: Doesn't adjust expectations for genre
5. **Audience adaptation**: Can't evaluate audience appropriateness
6. **Cultural references**: Western and general only
7. **Visual rhetoric**: Only analyzes text
8. **Multimodal arguments**: Cannot process images, video, etc.
9. **Intertextuality**: Can't detect references to other texts
10. **Sophisticated fallacies**: Only detects surface-level markers

### Types of Text That May Produce Misleading Results

- Poetry and creative writing (different rhetorical norms)
- Transcribed speech (different markers than written prose)
- Legal documents (domain-specific rhetoric)
- Scientific papers (disciplinary conventions)
- Marketing copy (intentional manipulation)
- Technical documentation (informative vs. persuasive)

---

## Appropriate Use Cases

### Good Fit

- Initial exploration of rhetorical patterns in a text
- Teaching rhetorical concepts with concrete examples
- Corpus analysis to identify patterns across documents
- Research hypothesis generation
- Supplementing human analysis with quantitative indicators

### Poor Fit

- Definitive quality assessment
- High-stakes evaluation (academic grading, hiring decisions)
- Automated content moderation
- Replacing human editorial judgment
- Analyzing non-English text
- Evaluating non-argumentative genres

---

## Comparison with Other Tools

| Tool | Strength | LingFrame Advantage |
|------|----------|---------------------|
| **Grammarly** | Grammar/spelling correction | Rhetorical structure analysis |
| **Hemingway** | Readability | Multi-dimensional analysis |
| **AntConc** | Corpus linguistics | Rhetorical framework |
| **Voyant Tools** | Text visualization | Hierarchical atomization |
| **LIWC** | Validated psychological categories | Rhetorical focus, extensible |
| **ChatGPT** | Natural language feedback | Reproducible, deterministic |

LingFrame does not replace these tools—it complements them with a different analytical lens.

---

## Roadmap for Addressing Limitations

### Planned Improvements

1. **Validation Study**: Compare scores to human expert ratings
2. **Generation Layer**: Specific revision suggestions
3. **Recursion**: Iterative analysis and improvement
4. **Multi-language**: spaCy multilingual models
5. **Genre Adaptation**: Adjust expectations by text type
6. **Explainability**: Link every score to specific evidence

### Community Contributions Welcome

- Domain profiles for specialized fields
- Non-Western rhetorical frameworks
- Validation data from human experts
- Pattern improvements and additions

---

## Conclusion

LingFrame is a research tool for computational rhetorical analysis. It excels at detecting patterns and visualizing structure. It does not replace human judgment, validate quality, or generate improved text.

Use it to explore, not to judge.

---

*This document reflects LingFrame version 1.0. Limitations are actively being addressed. See the [Roadmap](../README.md#roadmap) for planned improvements.*
