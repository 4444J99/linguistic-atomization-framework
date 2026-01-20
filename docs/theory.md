# Theoretical Foundation

This document outlines the linguistic and rhetorical frameworks that inform LingFrame's design and methodology.

---

## Overview

LingFrame draws on several traditions in linguistics and rhetoric:

1. **Classical Rhetoric** (Aristotle's Modes of Persuasion)
2. **Systemic Functional Linguistics** (Halliday's Metafunctions)
3. **Rhetorical Structure Theory** (Mann & Thompson)
4. **Discourse Analysis** (Coherence and Cohesion)
5. **Computational Linguistics** (Pattern Matching and NLP)

This document explains how these frameworks inform our approach while acknowledging the significant gap between theoretical ideals and our heuristic implementation.

---

## Classical Rhetoric: Aristotle's Modes of Persuasion

### The Framework

Aristotle's *Rhetoric* (4th century BCE) identifies three modes of persuasion:

- **Logos** (λόγος): Appeal to reason through logic and evidence
- **Pathos** (πάθος): Appeal to emotion and audience disposition
- **Ethos** (ἦθος): Appeal to the speaker's character and credibility

### Our Implementation

LingFrame operationalizes these concepts through pattern detection:

| Mode | What Aristotle Meant | What LingFrame Detects |
|------|---------------------|------------------------|
| **Logos** | Valid reasoning, syllogisms, examples | Statistics, citations, logical connectors |
| **Pathos** | Strategic emotional engagement | Emotional vocabulary, urgency markers, intensifiers |
| **Ethos** | Demonstration of practical wisdom, virtue, goodwill | Authority markers, credentials, hedging |

### Limitations

Aristotle's modes describe strategic communication choices requiring judgment of context, audience, and appropriateness. LingFrame detects *markers* associated with these modes but cannot evaluate:
- Whether the reasoning is actually valid
- Whether emotional appeals are appropriate
- Whether authority is genuine or performative

**Key difference**: Aristotle assessed rhetorical *effectiveness*; LingFrame counts rhetorical *markers*.

### Further Reading

- Aristotle. *Rhetoric*. Translated by W. Rhys Roberts.
- Kennedy, George A. *A New History of Classical Rhetoric*. Princeton UP, 1994.

---

## Systemic Functional Linguistics: Halliday's Metafunctions

### The Framework

M.A.K. Halliday's Systemic Functional Linguistics (SFL) proposes that language serves three simultaneous functions:

- **Ideational**: Representing experience (what the text is about)
- **Interpersonal**: Enacting relationships (writer-reader dynamics)
- **Textual**: Creating coherent discourse (how the text hangs together)

### Relevance to LingFrame

| Metafunction | SFL Focus | LingFrame Parallel |
|--------------|-----------|-------------------|
| **Ideational** | Transitivity, clause types | Entity analysis, semantic networks |
| **Interpersonal** | Mood, modality, appraisal | Sentiment analysis, pathos/ethos markers |
| **Textual** | Theme/rheme, cohesion | Transition analysis, coherence metrics |

### Limitations

SFL requires detailed grammatical analysis of clause structures and systemic choices. LingFrame uses surface-level patterns that approximate but do not replicate SFL analysis. We cannot:
- Perform full transitivity analysis
- Map mood and modality systems
- Analyze thematic progression

### Further Reading

- Halliday, M.A.K. *An Introduction to Functional Grammar*. 4th ed., Routledge, 2014.
- Martin, J.R. and David Rose. *Working with Discourse*. 2nd ed., Continuum, 2007.

---

## Rhetorical Structure Theory (RST)

### The Framework

Mann and Thompson's Rhetorical Structure Theory (1988) proposes that coherent texts have hierarchical rhetorical structures connecting text spans through relations such as:

- **Nucleus-satellite relations**: Background, evidence, elaboration, cause, result
- **Multinuclear relations**: Contrast, list, sequence

RST provides a principled way to analyze how parts of a text relate to each other and contribute to overall purpose.

### Relevance to LingFrame

LingFrame's atomization creates hierarchical structures similar to RST's text organization:

| RST Concept | LingFrame Implementation |
|-------------|--------------------------|
| Text spans | Atoms (theme, paragraph, sentence) |
| Relations | Transition marker analysis |
| Hierarchy | Atomization tree |

### Limitations

RST annotation requires human judgment about rhetorical relations and nuclearity. LingFrame:
- Cannot identify RST relations automatically
- Uses transition markers as proxies for coherence
- Does not build true RST trees

### Further Reading

- Mann, William C. and Sandra A. Thompson. "Rhetorical Structure Theory: Toward a Functional Theory of Text Organization." *Text* 8.3 (1988): 243-281.
- Taboada, Maite and William C. Mann. "Rhetorical Structure Theory: Looking Back and Moving Ahead." *Discourse Studies* 8.3 (2006): 423-459.

---

## Discourse Analysis: Cohesion and Coherence

### The Framework

Halliday and Hasan's *Cohesion in English* (1976) identifies linguistic devices that create textual unity:

- **Reference**: Pronouns, demonstratives
- **Substitution and ellipsis**: Replacing or omitting elements
- **Conjunction**: Additive, adversative, causal, temporal connectors
- **Lexical cohesion**: Repetition, synonymy, collocation

### Relevance to LingFrame

| Cohesion Device | LingFrame Detection |
|-----------------|---------------------|
| Conjunction | Transition markers (addition, contrast, cause-effect) |
| Lexical cohesion | Semantic analysis (TF-IDF, co-occurrence) |
| Reference | Not implemented |

### Limitations

Full cohesion analysis requires:
- Reference resolution (tracking pronouns to antecedents)
- Ellipsis recovery
- Lexical chain analysis

LingFrame only analyzes conjunction through transition markers and lexical patterns through statistical methods.

### Further Reading

- Halliday, M.A.K. and Ruqaiya Hasan. *Cohesion in English*. Longman, 1976.
- Tanskanen, Sanna-Kaisa. *Collaborating Towards Coherence*. John Benjamins, 2006.

---

## Computational Approaches

### Pattern Matching

LingFrame uses regex-based pattern matching to detect linguistic markers. This approach:

**Advantages**:
- Fast and deterministic
- Interpretable (patterns can be inspected)
- Domain-customizable (add patterns for specific fields)

**Disadvantages**:
- No semantic understanding
- High false positive/negative rates
- Cannot capture complex linguistic phenomena

### Statistical NLP

LingFrame incorporates:

- **TF-IDF**: Term frequency-inverse document frequency for theme similarity
- **VADER**: Valence Aware Dictionary for sEntiment Reasoning
- **spaCy NER**: Neural named entity recognition

These provide more sophisticated analysis than pure pattern matching but are still limited compared to human interpretation.

### LLM Integration (Optional)

LingFrame can optionally use large language models to:
- Augment heuristic findings with qualitative insights
- Provide context-aware analysis
- Generate natural language explanations

LLM integration adds qualitative depth but does not replace the fundamental heuristic approach.

---

## The 9-Step Framework: Design Rationale

### Structure

LingFrame's 9-step framework is organized into four phases:

```
EVALUATION         REINFORCEMENT       RISK              GROWTH
    │                   │                │                  │
    ▼                   ▼                ▼                  ▼
┌─────────┐       ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Critique│       │  Logic   │     │ Blind    │     │  Bloom   │
│ Logos   │       │  Check   │     │ Spots    │     │  Evolve  │
│ Pathos  │       │          │     │ Shatter  │     │          │
│ Ethos   │       │          │     │ Points   │     │          │
└─────────┘       └──────────┘     └──────────┘     └──────────┘
```

### Phase Rationale

1. **Evaluation**: Baseline assessment using Aristotelian modes
2. **Reinforcement**: Check argument flow and coherence
3. **Risk**: Identify vulnerabilities and weak points
4. **Growth**: Synthesize findings into recommendations

### Step-by-Step Explanation

| Step | Name | Theoretical Basis | Implementation |
|------|------|-------------------|----------------|
| 1 | Critique | General assessment | Aggregated pattern analysis |
| 2 | Logic Check | Coherence theory | Transition marker density |
| 3 | Logos | Aristotelian logos | Evidence marker detection |
| 4 | Pathos | Aristotelian pathos | Emotional marker detection |
| 5 | Ethos | Aristotelian ethos | Authority marker detection |
| 6 | Blind Spots | Argumentation theory | Assumption marker detection |
| 7 | Shatter Points | Fallacy analysis | Weakness marker detection |
| 8 | Bloom | Emergence theory | Theme connection analysis |
| 9 | Evolve | Synthesis | Recommendation aggregation |

---

## Honest Assessment

### What the Theory Provides

- Conceptual framework for understanding rhetoric
- Categories for organizing analysis
- Vocabulary for discussing findings

### What LingFrame Actually Does

- Pattern matching against predefined lists
- Density calculations
- Statistical aggregation

### The Gap

There is a significant gap between:
- **Theoretical frameworks** that require human judgment, context awareness, and interpretive skill
- **Heuristic implementation** that counts patterns and calculates metrics

LingFrame does not:
- Understand what text means
- Evaluate argument validity
- Assess rhetorical effectiveness
- Judge appropriateness for context

LingFrame does:
- Detect patterns associated with rhetorical strategies
- Calculate pattern density at multiple levels
- Visualize findings for human interpretation
- Generate recommendations based on detected patterns

---

## Future Directions

### Toward Validation

Planned research:
- Compare LingFrame scores to expert human ratings
- Measure inter-annotator agreement on rhetorical quality
- Identify which heuristics correlate with expert judgment

### Toward Generation

Planned development:
- Revision suggestions linked to specific findings
- Alternative phrasings for detected weaknesses
- Recursive analysis of generated improvements

### Toward Deeper Analysis

Potential extensions:
- RST relation detection (neural approaches)
- Coreference resolution for cohesion analysis
- Semantic role labeling for deeper Logos analysis

---

## Bibliography

### Primary Sources

- Aristotle. *Rhetoric*. Translated by W. Rhys Roberts. Available at MIT Classics.
- Halliday, M.A.K. *An Introduction to Functional Grammar*. 4th ed., revised by Christian M.I.M. Matthiessen. Routledge, 2014.
- Halliday, M.A.K. and Ruqaiya Hasan. *Cohesion in English*. Longman, 1976.
- Mann, William C. and Sandra A. Thompson. "Rhetorical Structure Theory." *Text* 8.3 (1988): 243-281.

### Secondary Sources

- Kennedy, George A. *A New History of Classical Rhetoric*. Princeton UP, 1994.
- Martin, J.R. and David Rose. *Working with Discourse*. 2nd ed., Continuum, 2007.
- Taboada, Maite and William C. Mann. "Rhetorical Structure Theory." *Discourse Studies* 8.3 (2006): 423-459.

### Computational Linguistics

- Jurafsky, Daniel and James H. Martin. *Speech and Language Processing*. 3rd ed. draft, 2024.
- Hutto, C.J. and Eric Gilbert. "VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text." ICWSM, 2014.

---

*This document reflects LingFrame's theoretical positioning as of version 1.0. The framework acknowledges the significant gap between theoretical ideals and heuristic implementation.*
