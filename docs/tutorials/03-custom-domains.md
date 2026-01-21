# Tutorial 3: Custom Domains

Create domain-specific analysis profiles for specialized text types like legal documents, medical records, academic papers, or any genre with its own vocabulary.

---

## What You'll Learn

- What domains are and why they matter
- How to create a custom lexicon
- How to define entity patterns
- Using your domain in analysis

## Prerequisites

- Completed [Tutorial 1: First Analysis](01-first-analysis.md)
- Basic familiarity with YAML syntax
- Understanding of your target domain's vocabulary

---

## Why Domains Matter

LingFrame's base analysis treats all words equally. But domain-specific text has vocabulary with specific connotations:

| Term | General Meaning | Medical Context | Legal Context |
|------|-----------------|-----------------|---------------|
| "terminal" | End station | Life-threatening | Final decision |
| "positive" | Good | Test result (not always good) | Affirmative assertion |
| "discharge" | Release | Patient leaving | Termination of duty |
| "brief" | Short | Legal document | Short |

A domain profile tells LingFrame how to interpret vocabulary in context.

---

## Domain Structure

Each domain lives in `framework/domains/<domain-name>/` with two files:

```
framework/domains/
├── base/              # Default fallback
│   ├── lexicon.yaml   # Generic sentiment terms
│   └── patterns.yaml  # Basic entity patterns
├── military/          # Example specialized domain
│   ├── lexicon.yaml   # Military sentiment terms
│   └── patterns.yaml  # Military entity patterns
└── your-domain/       # Your custom domain
    ├── lexicon.yaml
    └── patterns.yaml
```

---

## Creating a Custom Domain

Let's create a **legal** domain for analyzing court opinions and legal documents.

### Step 1: Create the Directory

```bash
mkdir -p framework/domains/legal
```

### Step 2: Create the Lexicon

The lexicon assigns sentiment scores to domain-specific terms. Scores range from -5.0 (very negative) to +5.0 (very positive).

Create `framework/domains/legal/lexicon.yaml`:

```yaml
# Legal Domain Sentiment Lexicon
# Sentiment scores for legal terminology

name: legal_sentiment_lexicon
description: Custom sentiment scores for legal document analysis

terms:
  # =========================================================================
  # NEGATIVE TERMS (Adverse outcomes, problems)
  # =========================================================================

  # High-intensity negative
  guilty: -3.0
  convicted: -2.8
  negligence: -2.5
  liability: -2.3
  damages: -2.2
  breach: -2.0
  violation: -2.0
  fraud: -3.0
  malpractice: -2.8

  # Medium-intensity negative
  dismissed: -1.5        # Could be positive for defendant
  denied: -1.8
  overruled: -1.2
  objection: -0.8
  alleged: -0.5          # Neutral-leaning negative
  defendant: -0.3        # Slightly negative connotation

  # =========================================================================
  # POSITIVE TERMS (Favorable outcomes, protections)
  # =========================================================================

  # High-intensity positive
  acquitted: 2.8
  exonerated: 3.0
  vindicated: 2.5
  rights: 2.0
  justice: 2.5
  protection: 1.8

  # Medium-intensity positive
  granted: 1.5
  sustained: 1.2
  affirmed: 1.5
  prevailed: 2.0
  plaintiff: 0.3         # Slightly positive (seeking remedy)

  # Low-intensity positive
  precedent: 0.8
  established: 0.5
  remedy: 1.0

  # =========================================================================
  # NEUTRAL/PROCEDURAL (Context-dependent)
  # =========================================================================
  judgment: 0.0
  ruling: 0.0
  court: 0.0
  motion: 0.0
  hearing: 0.0
  testimony: 0.0
  evidence: 0.0
  statute: 0.0
  appeal: 0.0            # Could go either way

# Categories for grouping and visualization
categories:
  outcomes_positive:
    - acquitted
    - exonerated
    - vindicated
    - granted
    - sustained
    - affirmed
    - prevailed
  outcomes_negative:
    - guilty
    - convicted
    - dismissed
    - denied
    - overruled
  wrongdoing:
    - negligence
    - fraud
    - malpractice
    - breach
    - violation
  procedural:
    - judgment
    - ruling
    - motion
    - hearing
    - testimony
    - evidence
    - appeal
  parties:
    - plaintiff
    - defendant
```

### Step 3: Create Entity Patterns

Patterns use Python regex syntax to identify domain-specific entities.

Create `framework/domains/legal/patterns.yaml`:

```yaml
# Legal Domain Entity Patterns
# Regex patterns for legal entity recognition

name: legal_entity_patterns
description: Pattern-based entity extraction for legal documents

patterns:
  # Court names and levels
  COURT: "\\b(Supreme Court|Court of Appeals|District Court|Circuit Court|Superior Court|Municipal Court|Federal Court|State Court|Appellate Court|Trial Court|High Court)\\b"

  # Legal roles
  ROLE: "\\b(Judge|Justice|Attorney|Counsel|Prosecutor|Defendant|Plaintiff|Witness|Jury|Juror|Magistrate|Clerk|Bailiff|Respondent|Petitioner|Appellant|Appellee)\\b"

  # Legal documents
  DOCUMENT: "\\b(Brief|Motion|Complaint|Answer|Petition|Writ|Subpoena|Summons|Affidavit|Deposition|Contract|Agreement|Statute|Regulation|Ordinance|Order|Decree|Judgment|Opinion|Ruling)\\b"

  # Case citations (simplified)
  CITATION: "\\b(\\d+\\s+U\\.S\\.\\s+\\d+|\\d+\\s+F\\.\\d+d\\s+\\d+|\\d+\\s+S\\.Ct\\.\\s+\\d+)\\b"

  # Legal concepts
  CONCEPT: "\\b(Due Process|Equal Protection|First Amendment|Fourth Amendment|Fifth Amendment|Probable Cause|Reasonable Doubt|Preponderance|Clear and Convincing|Strict Scrutiny|Rational Basis|Standing|Jurisdiction|Venue|Precedent|Stare Decisis)\\b"

  # Outcomes
  OUTCOME: "\\b(Affirmed|Reversed|Remanded|Dismissed|Granted|Denied|Sustained|Overruled|Vacated|Modified)\\b"

  # Legal actions
  ACTION: "\\b(filed|appealed|moved|objected|argued|testified|alleged|claimed|asserted|contended|stipulated|admitted|denied)\\b"

  # Temporal markers (legal-specific)
  TEMPORAL: "\\b(hearing date|trial date|filing deadline|statute of limitations|effective date|sentencing date)\\b"

# Colors for visualization
colors:
  COURT: "#1f77b4"       # Blue
  ROLE: "#d62728"        # Red
  DOCUMENT: "#9467bd"    # Purple
  CITATION: "#8c564b"    # Brown
  CONCEPT: "#2ca02c"     # Green
  OUTCOME: "#ff7f0e"     # Orange
  ACTION: "#17becf"      # Cyan
  TEMPORAL: "#bcbd22"    # Yellow-green

# Descriptions for UI
descriptions:
  COURT: "Court names and judicial bodies"
  ROLE: "Legal roles and parties"
  DOCUMENT: "Legal documents and filings"
  CITATION: "Case citations and references"
  CONCEPT: "Legal concepts and doctrines"
  OUTCOME: "Case outcomes and rulings"
  ACTION: "Legal actions and procedures"
  TEMPORAL: "Legal time references"
```

---

## Using Your Domain

### In Project Configuration

Specify your domain in `project.yaml`:

```yaml
project:
  name: "court-opinions"
  version: "1.0.0"

domain:
  profile: legal    # Uses framework/domains/legal/

corpus:
  documents:
    - source: "docs/brown-v-board.txt"
      title: "Brown v. Board of Education"
```

### Via Command Line

```bash
# Currently domains are project-level
# Create a project with your domain, then:
./new_venv/bin/python lingframe.py run -p your-project --visualize
```

---

## Lexicon Design Guidelines

### Score Ranges

| Range | Interpretation | Example Terms |
|-------|---------------|---------------|
| +3 to +5 | Strongly positive | "vindicated", "exonerated" |
| +1 to +3 | Moderately positive | "granted", "affirmed" |
| +0.1 to +1 | Slightly positive | "remedy", "protection" |
| 0 | Neutral | "court", "motion", "hearing" |
| -0.1 to -1 | Slightly negative | "alleged", "defendant" |
| -1 to -3 | Moderately negative | "denied", "dismissed" |
| -3 to -5 | Strongly negative | "guilty", "fraud" |

### Common Mistakes

1. **Over-scoring**: Not every domain term needs a strong score. Most should be close to neutral.

2. **Context blindness**: "Dismissed" is bad for a plaintiff but good for a defendant. When in doubt, use neutral.

3. **Forgetting variations**: Include plurals and verb forms if important ("verdict/verdicts", "convict/convicted/conviction").

4. **Over-specificity**: Focus on terms that genuinely carry sentiment, not every technical term.

---

## Pattern Design Guidelines

### Regex Tips

```yaml
# Word boundaries prevent partial matches
TERM: "\\b(word)\\b"           # Matches "word" not "sword"

# Case-insensitive matching (automatic)
TERM: "\\b(Court|court)\\b"    # Both work, but be explicit

# Multiple words
TERM: "\\b(Supreme Court|District Court)\\b"

# Optional components
TERM: "\\b(First|Second|Third)\\s+Amendment\\b"

# Numbers
CITATION: "\\d+\\s+U\\.S\\.\\s+\\d+"   # "123 U.S. 456"
```

### Entity Type Categories

Choose types that make sense for visualization and filtering:

- **Actors**: People, organizations, roles
- **Objects**: Documents, equipment, artifacts
- **Places**: Locations, jurisdictions
- **Concepts**: Abstract ideas, doctrines
- **Actions**: Verbs, procedures
- **Temporal**: Time references

---

## Testing Your Domain

### Quick Validation

```bash
# Run analysis on a test document
./new_venv/bin/python -c "
from framework.core import registry
from framework.domains import DOMAINS_DIR

# Discover domains
registry.discover_domains(DOMAINS_DIR)

# Check your domain loaded
domain = registry.get_domain('legal')
print(f'Domain: {domain.name}')
print(f'Lexicon terms: {len(domain.lexicon.terms)}')
print(f'Pattern types: {list(domain.patterns.patterns.keys())}')
"
```

### Full Test

1. Find a representative document from your domain
2. Run analysis with and without your domain
3. Compare entity detection and sentiment scores
4. Iterate on lexicon and patterns

---

## Example: Comparing Domains

The same text analyzed with different domains:

**Text**: "The defendant was found guilty of negligence."

**Base domain analysis**:
- Sentiment: Slightly negative (generic "guilty" = -1.5)
- Entities: None detected

**Legal domain analysis**:
- Sentiment: More negative ("guilty" = -3.0, "negligence" = -2.5, "defendant" = -0.3)
- Entities: ROLE: "defendant", OUTCOME: implied

**Military domain analysis**:
- Sentiment: Neutral (no military terms)
- Entities: None detected

---

## Domain Ideas

| Domain | Key Vocabulary | Use Cases |
|--------|---------------|-----------|
| Medical | Diagnoses, treatments, outcomes | Clinical notes, research |
| Academic | Citations, methodology, findings | Papers, dissertations |
| Financial | Transactions, metrics, risk | Reports, filings |
| Technical | APIs, errors, systems | Documentation, logs |
| Literary | Devices, themes, style | Literary criticism |
| Political | Policies, positions, rhetoric | Speeches, platforms |
| Sports | Stats, plays, outcomes | Commentary, analysis |

---

## Exercises

### Exercise 1: Medical Domain

Create a medical domain with:
- Lexicon: positive outcomes (recovery, remission) vs. negative (diagnosis, complication)
- Patterns: medications, conditions, procedures, anatomical terms

### Exercise 2: Improve Existing Domain

Enhance the military domain by adding:
- More vehicle types
- Communication terminology (radio, comms, frequencies)
- Weather/terrain terms relevant to operations

### Exercise 3: Domain for Your Field

Create a domain for text you actually work with:
- Identify 20-30 key sentiment terms
- Define 5-8 entity pattern categories
- Test on real documents

---

## Next Steps

- **[Tutorial 4: Building Modules](04-building-modules.md)** - Create custom analysis modules

---

## File Reference

### lexicon.yaml Structure

```yaml
name: domain_name_lexicon
description: Brief description

terms:
  word: 2.5          # Positive score
  another: -1.5      # Negative score
  neutral: 0.0       # Neutral

categories:
  category_name:
    - word
    - another
```

### patterns.yaml Structure

```yaml
name: domain_name_patterns
description: Brief description

patterns:
  ENTITY_TYPE: "\\b(regex|pattern|here)\\b"

colors:
  ENTITY_TYPE: "#hexcode"

descriptions:
  ENTITY_TYPE: "Human-readable description"
```
