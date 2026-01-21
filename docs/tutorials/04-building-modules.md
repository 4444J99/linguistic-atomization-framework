# Tutorial 4: Building Modules

Extend LingFrame with custom analysis modules and visualization adapters. This is developer-focused content.

---

## What You'll Learn

- Framework architecture and extension points
- Creating a custom analysis module
- Creating a custom visualization adapter
- Registering modules with the framework

## Prerequisites

- Completed Tutorials 1-3
- Python development experience
- Basic understanding of NLP concepts

---

## Architecture Overview

LingFrame follows a pipeline architecture:

```
Document → Atomizer → Corpus → Analysis Modules → Visualization Adapters
                                     ↓                      ↓
                            AnalysisOutput            HTML Files
```

**Key concepts:**

| Concept | Description |
|---------|-------------|
| **Corpus** | Container for documents and their atomized structure |
| **Atom** | Unit of text (theme, paragraph, sentence, word) |
| **AnalysisModule** | Processes corpus and produces structured output |
| **VisualizationAdapter** | Transforms analysis output to HTML |
| **Registry** | Central catalog of available components |

---

## Creating an Analysis Module

Let's build a **readability** module that calculates reading difficulty metrics.

### Step 1: Create the Module File

Create `framework/analysis/readability.py`:

```python
"""
Readability Analysis Module - Calculate reading difficulty metrics.

Provides Flesch-Kincaid, Gunning Fog, and other readability scores.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..core.ontology import (
    AnalysisOutput,
    AtomLevel,
    Corpus,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule


@registry.register_analysis("readability")
class ReadabilityAnalysis(BaseAnalysisModule):
    """
    Readability analysis using standard formulas.

    Calculates:
    - Flesch-Kincaid Grade Level
    - Flesch Reading Ease
    - Gunning Fog Index
    - Average sentence length
    - Average word length
    """

    name = "readability"
    description = "Reading difficulty metrics using standard formulas"

    def __init__(self):
        super().__init__()
        # Syllable counting patterns
        self._vowel_pattern = re.compile(r'[aeiouy]+', re.IGNORECASE)
        self._silent_e = re.compile(r'e$', re.IGNORECASE)

    def count_syllables(self, word: str) -> int:
        """
        Estimate syllable count for a word.

        Uses vowel group counting with adjustments for silent e.
        """
        word = word.lower().strip()
        if len(word) <= 3:
            return 1

        # Count vowel groups
        vowel_groups = self._vowel_pattern.findall(word)
        count = len(vowel_groups)

        # Adjust for silent e
        if self._silent_e.search(word) and count > 1:
            count -= 1

        return max(1, count)

    def count_complex_words(self, words: List[str]) -> int:
        """Count words with 3+ syllables (for Gunning Fog)."""
        return sum(1 for w in words if self.count_syllables(w) >= 3)

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run readability analysis on the corpus.

        Returns metrics at document, theme, and overall levels.
        """
        config = config or {}
        self._config = config

        # Collect all sentences
        sentences = []
        for _, atom in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            if atom.text.strip():
                sentences.append(atom.text)

        # Calculate metrics
        total_words = 0
        total_syllables = 0
        total_sentences = len(sentences)
        all_words = []

        for sentence in sentences:
            words = re.findall(r'\b[a-zA-Z]+\b', sentence)
            all_words.extend(words)
            total_words += len(words)
            total_syllables += sum(self.count_syllables(w) for w in words)

        # Avoid division by zero
        if total_words == 0 or total_sentences == 0:
            return self.make_output({
                "error": "Insufficient text for analysis",
                "metrics": {},
            })

        # Calculate averages
        avg_sentence_length = total_words / total_sentences
        avg_syllables_per_word = total_syllables / total_words
        avg_word_length = sum(len(w) for w in all_words) / len(all_words)

        # Flesch-Kincaid Grade Level
        fk_grade = (
            0.39 * avg_sentence_length +
            11.8 * avg_syllables_per_word -
            15.59
        )

        # Flesch Reading Ease (0-100, higher = easier)
        flesch_ease = (
            206.835 -
            1.015 * avg_sentence_length -
            84.6 * avg_syllables_per_word
        )

        # Gunning Fog Index
        complex_words = self.count_complex_words(all_words)
        complex_word_ratio = complex_words / total_words if total_words else 0
        fog_index = 0.4 * (avg_sentence_length + 100 * complex_word_ratio)

        # Interpret the scores
        interpretation = self._interpret_scores(fk_grade, flesch_ease, fog_index)

        # Build theme-level breakdown
        theme_metrics = []
        for _, atom in self.iter_atoms(corpus, AtomLevel.THEME):
            theme_words = re.findall(r'\b[a-zA-Z]+\b', atom.text)
            theme_sentences = len(re.findall(r'[.!?]+', atom.text)) or 1

            if theme_words:
                theme_avg_sentence = len(theme_words) / theme_sentences
                theme_syllables = sum(self.count_syllables(w) for w in theme_words)
                theme_avg_syllables = theme_syllables / len(theme_words)

                theme_fk = 0.39 * theme_avg_sentence + 11.8 * theme_avg_syllables - 15.59

                theme_metrics.append({
                    "theme_id": atom.id,
                    "word_count": len(theme_words),
                    "sentence_count": theme_sentences,
                    "fk_grade": round(theme_fk, 1),
                })

        return self.make_output({
            "metrics": {
                "flesch_kincaid_grade": round(fk_grade, 1),
                "flesch_reading_ease": round(flesch_ease, 1),
                "gunning_fog_index": round(fog_index, 1),
                "avg_sentence_length": round(avg_sentence_length, 1),
                "avg_word_length": round(avg_word_length, 1),
                "avg_syllables_per_word": round(avg_syllables_per_word, 2),
                "complex_word_ratio": round(complex_word_ratio, 3),
            },
            "statistics": {
                "total_words": total_words,
                "total_sentences": total_sentences,
                "total_syllables": total_syllables,
                "complex_words": complex_words,
            },
            "interpretation": interpretation,
            "theme_breakdown": theme_metrics,
        })

    def _interpret_scores(
        self,
        fk_grade: float,
        flesch_ease: float,
        fog_index: float,
    ) -> Dict[str, Any]:
        """Generate human-readable interpretation of scores."""

        # Grade level interpretation
        if fk_grade <= 6:
            grade_desc = "Elementary school level"
        elif fk_grade <= 8:
            grade_desc = "Middle school level"
        elif fk_grade <= 12:
            grade_desc = "High school level"
        elif fk_grade <= 16:
            grade_desc = "College level"
        else:
            grade_desc = "Graduate/professional level"

        # Flesch ease interpretation
        if flesch_ease >= 80:
            ease_desc = "Very easy to read"
        elif flesch_ease >= 60:
            ease_desc = "Easy to read"
        elif flesch_ease >= 40:
            ease_desc = "Moderately difficult"
        elif flesch_ease >= 20:
            ease_desc = "Difficult"
        else:
            ease_desc = "Very difficult"

        return {
            "grade_level_description": grade_desc,
            "reading_ease_description": ease_desc,
            "recommended_audience": self._recommend_audience(fk_grade),
        }

    def _recommend_audience(self, fk_grade: float) -> str:
        """Suggest appropriate audience for the text."""
        if fk_grade <= 8:
            return "General public"
        elif fk_grade <= 12:
            return "High school educated readers"
        elif fk_grade <= 16:
            return "College educated readers"
        else:
            return "Specialists or academics"
```

### Step 2: Register the Module

Add to `framework/analysis/__init__.py`:

```python
from .readability import ReadabilityAnalysis
```

The `@registry.register_analysis("readability")` decorator handles registration automatically when the module is imported.

### Step 3: Test the Module

```python
# Quick test
from framework.core import registry, Atomizer, AtomizationSchema, Corpus
from framework.core.ontology import Document

# Setup
registry.discover_domains(...)

# Create test corpus
text = "This is a simple sentence. Here is another one."
schema = AtomizationSchema.default()
atomizer = Atomizer(schema)
doc = Document(id="test", source_path="inline", format="plain", title="Test")
doc.root_atoms = atomizer.atomize_text(text, schema.levels[0])
corpus = Corpus(name="test", documents=[doc], schema=schema)

# Run analysis
readability = registry.create_analysis("readability")
output = readability.analyze(corpus)
print(output.data)
```

---

## Creating a Visualization Adapter

Let's create a **gauge chart** adapter to visualize readability scores.

### Step 1: Create the Adapter File

Create `framework/visualization/adapters/readability_gauge.py`:

```python
"""
Readability Gauge Adapter - Visual gauge charts for readability metrics.

Displays Flesch-Kincaid grade level and reading ease as interactive gauges.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("readability_gauge")
class ReadabilityGaugeAdapter(BaseVisualizationAdapter):
    """
    Gauge visualization for readability metrics.

    Uses Chart.js doughnut charts styled as gauges.
    """

    name = "readability_gauge"
    description = "Interactive gauge charts for readability scores"
    supported_analysis = ["readability"]

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Generate the gauge visualization."""
        config = config or {}

        data = analysis.data
        metrics = data.get("metrics", {})
        interpretation = data.get("interpretation", {})

        # Prepare gauge data
        fk_grade = metrics.get("flesch_kincaid_grade", 0)
        flesch_ease = metrics.get("flesch_reading_ease", 0)
        fog_index = metrics.get("gunning_fog_index", 0)

        # Build the HTML
        title = config.get("title", "Readability Analysis")

        content = self._build_content(
            fk_grade=fk_grade,
            flesch_ease=flesch_ease,
            fog_index=fog_index,
            interpretation=interpretation,
            metrics=metrics,
        )

        scripts = self._build_scripts(fk_grade, flesch_ease, fog_index)

        styles = self._build_styles()

        head_extras = """
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        """

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            styles=styles,
            head_extras=head_extras,
        )

        output_path.write_text(html, encoding="utf-8")
        return output_path

    def _build_content(
        self,
        fk_grade: float,
        flesch_ease: float,
        fog_index: float,
        interpretation: Dict,
        metrics: Dict,
    ) -> str:
        """Build the main content HTML."""
        return f"""
        <div class="glass">
            <h1>📖 Readability Analysis</h1>
            <p class="subtitle">{interpretation.get('grade_level_description', '')}</p>
        </div>

        <div class="gauge-grid">
            <div class="glass gauge-box">
                <h3>Grade Level</h3>
                <canvas id="gradeGauge"></canvas>
                <div class="gauge-value">{fk_grade:.1f}</div>
                <div class="gauge-label">Flesch-Kincaid Grade</div>
            </div>

            <div class="glass gauge-box">
                <h3>Reading Ease</h3>
                <canvas id="easeGauge"></canvas>
                <div class="gauge-value">{flesch_ease:.0f}</div>
                <div class="gauge-label">{interpretation.get('reading_ease_description', '')}</div>
            </div>

            <div class="glass gauge-box">
                <h3>Fog Index</h3>
                <canvas id="fogGauge"></canvas>
                <div class="gauge-value">{fog_index:.1f}</div>
                <div class="gauge-label">Gunning Fog</div>
            </div>
        </div>

        <div class="glass">
            <h3>📊 Details</h3>
            <div class="stats">
                <div class="stat-box">
                    <div class="stat-value">{metrics.get('avg_sentence_length', 0):.1f}</div>
                    <div class="stat-label">Words per Sentence</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{metrics.get('avg_syllables_per_word', 0):.2f}</div>
                    <div class="stat-label">Syllables per Word</div>
                </div>
                <div class="stat-box">
                    <div class="stat-value">{metrics.get('complex_word_ratio', 0):.1%}</div>
                    <div class="stat-label">Complex Words</div>
                </div>
            </div>
            <p style="margin-top: 20px; opacity: 0.8;">
                <strong>Recommended audience:</strong> {interpretation.get('recommended_audience', 'General')}
            </p>
        </div>
        """

    def _build_scripts(
        self,
        fk_grade: float,
        flesch_ease: float,
        fog_index: float,
    ) -> str:
        """Build the JavaScript for gauge charts."""
        return f"""
        function createGauge(canvasId, value, max, colors) {{
            const ctx = document.getElementById(canvasId).getContext('2d');
            const percentage = Math.min(value / max, 1);

            new Chart(ctx, {{
                type: 'doughnut',
                data: {{
                    datasets: [{{
                        data: [percentage * 100, (1 - percentage) * 100],
                        backgroundColor: [colors.fill, 'rgba(255,255,255,0.1)'],
                        borderWidth: 0,
                    }}]
                }},
                options: {{
                    cutout: '75%',
                    rotation: -90,
                    circumference: 180,
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{ legend: {{ display: false }} }}
                }}
            }});
        }}

        // Grade level gauge (0-20 scale, lower is easier)
        createGauge('gradeGauge', {fk_grade}, 20, {{
            fill: {fk_grade} <= 8 ? '#4ECDC4' : {fk_grade} <= 12 ? '#FFE66D' : '#FF6B6B'
        }});

        // Reading ease gauge (0-100, higher is easier)
        createGauge('easeGauge', {flesch_ease}, 100, {{
            fill: {flesch_ease} >= 60 ? '#4ECDC4' : {flesch_ease} >= 30 ? '#FFE66D' : '#FF6B6B'
        }});

        // Fog index gauge (0-20, lower is easier)
        createGauge('fogGauge', {fog_index}, 20, {{
            fill: {fog_index} <= 10 ? '#4ECDC4' : {fog_index} <= 14 ? '#FFE66D' : '#FF6B6B'
        }});
        """

    def _build_styles(self) -> str:
        """Build additional CSS."""
        return """
        .gauge-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .gauge-box {
            text-align: center;
            padding: 30px;
        }
        .gauge-box h3 {
            margin-bottom: 20px;
            font-size: 1.2em;
        }
        .gauge-box canvas {
            max-width: 200px;
            margin: 0 auto;
        }
        .gauge-value {
            font-size: 2.5em;
            font-weight: bold;
            margin-top: -30px;
        }
        .gauge-label {
            opacity: 0.8;
            margin-top: 10px;
        }
        """
```

### Step 2: Register the Adapter

Add to `framework/visualization/adapters/__init__.py`:

```python
from .readability_gauge import ReadabilityGaugeAdapter
```

### Step 3: Use in Projects

Add to your `project.yaml`:

```yaml
analysis:
  pipelines:
    - module: readability

visualization:
  adapters:
    - type: readability_gauge
      analysis: readability
```

---

## Module Interface Reference

### BaseAnalysisModule

```python
class BaseAnalysisModule(AnalysisModule):
    """Required interface for analysis modules."""

    name: str = "module_name"
    description: str = "What this module does"

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Required: Implement your analysis logic.

        Args:
            corpus: Atomized document structure
            domain: Optional domain profile for customization
            config: Optional configuration dict

        Returns:
            AnalysisOutput with your results
        """
        pass

    # Helpful utilities inherited:
    def iter_atoms(self, corpus, level) -> Generator[Tuple[Document, Atom]]:
        """Iterate over atoms at a specific level."""

    def get_all_text_at_level(self, corpus, level) -> List[Tuple[str, str]]:
        """Get all (id, text) pairs at a level."""

    def get_theme_texts(self, corpus) -> Dict[str, str]:
        """Get theme_id -> text mapping."""

    def get_sentence_data(self, corpus) -> List[Dict]:
        """Get sentence data with parent references."""

    def make_output(self, data, metadata=None) -> AnalysisOutput:
        """Create properly formatted output."""
```

### BaseVisualizationAdapter

```python
class BaseVisualizationAdapter(VisualizationAdapter):
    """Required interface for visualization adapters."""

    name: str = "adapter_name"
    description: str = "What this adapter visualizes"
    supported_analysis: List[str] = ["module_name"]

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Required: Generate the visualization.

        Args:
            analysis: Output from an analysis module
            output_path: Where to save the visualization
            config: Optional configuration

        Returns:
            Path to generated file
        """
        pass

    # Helpful utilities inherited:
    def wrap_html(self, title, content, scripts="", styles="", head_extras=""):
        """Wrap content in a complete HTML document with base styling."""

    def get_base_css(self) -> str:
        """Get the base glassmorphic CSS."""

    # Template engine available:
    self.engine.render(template, context)
```

---

## Best Practices

### Analysis Modules

1. **Return structured data** - Use nested dicts with clear keys
2. **Include metadata** - Add counts, timestamps, config used
3. **Handle edge cases** - Empty text, missing data, malformed input
4. **Make dependencies optional** - Use try/except for external libraries
5. **Document output schema** - Explain what your output contains

### Visualization Adapters

1. **Be self-contained** - Include all CSS/JS in the output
2. **Use CDNs for libraries** - Chart.js, D3.js, etc.
3. **Responsive design** - Work on mobile and desktop
4. **Include fallbacks** - Show something if visualization fails
5. **Match existing style** - Use the glassmorphic theme

### Testing

```python
# Create minimal test corpus
def make_test_corpus(text: str) -> Corpus:
    from framework.core import Atomizer, AtomizationSchema
    from framework.core.ontology import Document, Corpus

    schema = AtomizationSchema.default()
    atomizer = Atomizer(schema)
    doc = Document(id="test", source_path="inline", format="plain", title="Test")
    doc.root_atoms = atomizer.atomize_text(text, schema.levels[0])
    return Corpus(name="test", documents=[doc], schema=schema)

# Test your module
corpus = make_test_corpus("Your test text here.")
module = YourModule()
output = module.analyze(corpus)
assert "expected_key" in output.data
```

---

## Exercises

### Exercise 1: Word Frequency Module

Create a module that:
- Counts word frequencies
- Identifies top N words per theme
- Excludes stopwords
- Outputs data for a word cloud visualization

### Exercise 2: Sentence Complexity Analyzer

Create a module that:
- Parses sentence structure (if NLTK available)
- Counts clause depth
- Identifies complex vs. simple sentences
- Flags potentially confusing sentences

### Exercise 3: Custom Visualization

Create an adapter that:
- Takes any analysis output
- Generates a summary card
- Uses the glassmorphic style
- Shows key metrics and recommendations

---

## Resources

- **Framework source**: `framework/` directory
- **Existing modules**: `framework/analysis/` (semantic, temporal, sentiment, entity, evaluation)
- **Existing adapters**: `framework/visualization/adapters/`
- **Architecture docs**: `docs/architecture.md`

---

## Troubleshooting

### Module not found

```python
# Ensure module is imported in __init__.py
from .your_module import YourModule

# Check registration
from framework.core import registry
print(registry.list_analysis_modules())
```

### Visualization not generating

```python
# Check adapter is registered
print(registry.list_adapters())

# Test adapter directly
adapter = YourAdapter()
output = AnalysisOutput(module_name="test", data={"key": "value"})
adapter.generate(output, Path("test.html"))
```

### Data structure issues

```python
# Validate output structure
output = your_module.analyze(corpus)
print(json.dumps(output.to_dict(), indent=2))
```
