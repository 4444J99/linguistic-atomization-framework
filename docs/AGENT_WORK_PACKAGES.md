# AI Agent Work Distribution - Tomb of the Unknowns Expansion

**Project Overview**: Comprehensive expansion of atomized literary text analysis with advanced NLP, ML, and visualization capabilities.

**Base Assets**:
- Source: `Tomb_of_the_Unknowns_atomized.json` (54MB, 312,704 elements)
- Hierarchy: 49 themes → 183 paragraphs → 2,976 sentences → 54,970 words → 256,516 letters
- ID Format: T### (theme), P#### (paragraph), S##### (sentence), W###### (word), L######## (letter)

---

## 🤖 GEMINI WORK PACKAGE

### Primary Assignment: Semantic Network Analysis (Todo #1)
**Status**: IN PROGRESS
**Priority**: HIGH
**Estimated Complexity**: 8/10

#### Objective
Create an interactive graph-based visualization revealing hidden relationships between themes, entities, concepts, and narrative elements throughout the manuscript.

#### Technical Requirements
- **Framework**: D3.js v7+ for force-directed graph
- **Input**: `Tomb_of_the_Unknowns_atomized.json`
- **Output**: `semantic_network.html` (standalone with embedded data sample)

#### Implementation Specifications

**Node Types**:
1. Theme nodes (large circles, color: #1f77b4)
2. Entity nodes (medium circles, color by type):
   - PERSON: #ff7f0e
   - PLACE: #2ca02c
   - MILITARY_TERM: #d62728
   - OBJECT: #9467bd

**Edge Types**:
- Co-occurrence within same paragraph (weight by frequency)
- Semantic similarity (cosine similarity > 0.6)
- Sequential adjacency (narrative flow)

**Features to Implement**:
1. Force-directed layout with collision detection
2. Zoom/pan controls (d3.zoom)
3. Node hover: show connected entities + context excerpt
4. Click node: highlight all paths, show detailed panel
5. Filter controls:
   - By entity type (checkboxes)
   - By theme (dropdown)
   - By edge weight threshold (slider)
6. Search box: find and highlight nodes
7. Export view as SVG/PNG

**Analysis Requirements**:
```python
# Pre-processing needed:
1. Extract co-occurrence matrix (window size: paragraph)
2. Calculate TF-IDF vectors for themes
3. Compute pairwise cosine similarity
4. Identify entity mentions per theme
5. Weight edges: frequency * similarity * proximity
```

**Deliverables**:
- `semantic_network.html` - Interactive visualization
- `semantic_network.py` - Pre-processing script
- `semantic_data.json` - Graph structure (nodes + edges)
- `README_semantic.md` - Usage documentation

**Code Starter Template**:
```javascript
// D3.js force-directed graph skeleton
const width = 1920, height = 1080;
const svg = d3.select("#graph").append("svg")
  .attr("width", width).attr("height", height);

const simulation = d3.forceSimulation(nodes)
  .force("link", d3.forceLink(links).id(d => d.id).distance(100))
  .force("charge", d3.forceManyBody().strength(-300))
  .force("center", d3.forceCenter(width / 2, height / 2))
  .force("collision", d3.forceCollide().radius(30));

// Add drag, zoom, hover, click handlers
```

---

## 🤖 JULES WORK PACKAGE

### Primary Assignment: Temporal Flow Visualization (Todo #2)
**Status**: NOT STARTED
**Priority**: HIGH
**Estimated Complexity**: 7/10

#### Objective
Map the manuscript's complex temporal structure including chronological markers, tense shifts, flashbacks, and narrative non-linearity.

#### Technical Requirements
- **Framework**: Plotly.js for Sankey diagrams + custom timeline
- **Input**: `Tomb_of_the_Unknowns_atomized.json`
- **Output**: `temporal_flow.html`

#### Implementation Specifications

**Temporal Analysis Markers**:
1. Verb tense detection (past, present, future, conditional)
2. Temporal adverbs: "then", "now", "later", "before", "after", "once", "will"
3. Chronological indicators: dates, time of day, seasonal references
4. Flashback/flashforward signals: "looking back", "I remember", "will be asked"

**Visualization Components**:

**Component 1: Narrative Timeline (horizontal)**
- X-axis: manuscript position (theme order)
- Y-axis: inferred chronological time
- Color code by tense: past (blue), present (green), future (orange)
- Vertical lines connect narrative position to chronological position

**Component 2: Sankey Flow Diagram**
- Source nodes: Narrative sections (T001-T049)
- Target nodes: Chronological periods (detected/inferred)
- Flow width: word count
- Show narrative jumping through time

**Component 3: Tense Distribution Heatmap**
- Rows: Themes
- Columns: Tense categories
- Cell color: percentage of sentences in that tense

**Analysis Requirements**:
```python
import spacy
nlp = spacy.load("en_core_web_sm")

def analyze_temporal_markers(text):
    doc = nlp(text)
    tense_counts = {"past": 0, "present": 0, "future": 0}
    temporal_markers = []
    
    for sent in doc.sents:
        # Analyze verb tenses
        # Extract temporal adverbs
        # Identify chronological references
    
    return {
        "tense_distribution": tense_counts,
        "temporal_markers": temporal_markers,
        "chronological_hints": extract_time_refs(doc)
    }
```

**Deliverables**:
- `temporal_flow.html` - Interactive visualization
- `temporal_analysis.py` - Tense/time extraction script
- `temporal_data.json` - Structured temporal analysis
- `README_temporal.md` - Interpretation guide

---

## 🤖 COPILOT WORK PACKAGE

### Primary Assignment: Emotional Sentiment Mapping (Todo #3)
**Status**: NOT STARTED
**Priority**: HIGH
**Estimated Complexity**: 6/10

#### Objective
Perform sentence-level sentiment analysis and create an emotional arc visualization showing the manuscript's affective journey.

#### Technical Requirements
- **Libraries**: VADER (vaderSentiment), TextBlob
- **Framework**: Chart.js + custom canvas rendering
- **Input**: `Tomb_of_the_Unknowns_atomized.json`
- **Output**: `sentiment_map.html` + `sentiment_data.json`

#### Implementation Specifications

**Sentiment Analysis Approach**:
1. VADER for social media-style sentiment (military slang, informal speech)
2. TextBlob for literary sentiment (polarity & subjectivity)
3. Custom military lexicon additions:
   - Positive: "Semper Fidelis", "mission complete", "safe", "home"
   - Negative: "gunfire", "blood", "fear", "infection", "lost"
   - Neutral/ambiguous: "deployment", "convoy", "patrol"

**Visualization Components**:

**Component 1: Emotional Arc Line Chart**
- X-axis: Sentence position (1-2976)
- Y-axis: Sentiment score (-1 to +1)
- Smooth line with rolling average (window=10)
- Color gradient: red (negative) → yellow (neutral) → green (positive)
- Theme boundaries marked with vertical lines

**Component 2: Sentiment Heatmap**
- Grid: Themes (rows) × Sentiment bins (columns)
- Bins: Very Negative, Negative, Neutral, Positive, Very Positive
- Cell intensity: percentage of sentences in bin

**Component 3: Emotional Peaks/Valleys Table**
- Top 10 most positive sentences (with context)
- Top 10 most negative sentences (with context)
- Most emotionally volatile themes (highest std deviation)

**Code Implementation**:
```python
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from textblob import TextBlob
import json

analyzer = SentimentIntensityAnalyzer()

# Add custom military lexicon
military_lexicon = {
    "gunfire": -2.5,
    "explosion": -3.0,
    "safe": 2.0,
    # ... add 50+ terms
}
analyzer.lexicon.update(military_lexicon)

def analyze_sentiment(sentence_text):
    vader_scores = analyzer.polarity_scores(sentence_text)
    blob = TextBlob(sentence_text)
    
    return {
        "vader_compound": vader_scores['compound'],
        "vader_pos": vader_scores['pos'],
        "vader_neg": vader_scores['neg'],
        "vader_neu": vader_scores['neu'],
        "textblob_polarity": blob.sentiment.polarity,
        "textblob_subjectivity": blob.sentiment.subjectivity,
        "composite_score": (vader_scores['compound'] + blob.sentiment.polarity) / 2
    }
```

**Deliverables**:
- `sentiment_map.html` - Interactive visualization
- `sentiment_analysis.py` - Sentiment computation script
- `sentiment_data.json` - All sentence-level scores
- `military_lexicon.json` - Custom sentiment dictionary
- `README_sentiment.md` - Methodology documentation

---

## 🤖 CODE (Additional Assistant) WORK PACKAGE

### Primary Assignment: Entity Recognition & Tagging (Todo #4)
**Status**: NOT STARTED
**Priority**: HIGH
**Estimated Complexity**: 7/10

#### Objective
Implement Named Entity Recognition (NER) using spaCy to identify and tag all entities, creating an enhanced searchable entity index.

#### Technical Requirements
- **Library**: spaCy v3+ with `en_core_web_trf` (transformer model)
- **Custom Training**: Fine-tune on military/war memoir corpus
- **Input**: `Tomb_of_the_Unknowns_atomized.json`
- **Output**: `enhanced_atomized.json` + `entity_browser.html`

#### Implementation Specifications

**Entity Categories**:
1. **Standard NER**: PERSON, GPE (geo-political), LOC, ORG, DATE, TIME
2. **Custom Military Entities**:
   - RANK: "Staff Sergeant", "Lieutenant", "Corpsman"
   - UNIT: "Marine Corps", "platoon", "convoy"
   - EQUIPMENT: "M40", "M16", "Thunderbird", "fuel truck"
   - LOCATION_MILITARY: "Al Asad", "Sal Sinjar", "Iraq"
   - INCIDENT: "firefight", "checkpoint", "patrol", "convoy"

**Entity Enhancement Process**:
```python
import spacy
from spacy.training import Example
from spacy.util import minibatch, compounding

# Load base model
nlp = spacy.load("en_core_web_trf")

# Add custom entity ruler for military terms
ruler = nlp.add_pipe("entity_ruler", before="ner")
patterns = [
    {"label": "RANK", "pattern": "Staff Sergeant"},
    {"label": "EQUIPMENT", "pattern": "M40"},
    {"label": "LOCATION_MILITARY", "pattern": "Al Asad"},
    # ... add 100+ patterns
]
ruler.add_patterns(patterns)

def enhance_atomized_with_entities(atomized_json):
    """Add entity tags to all levels of hierarchy"""
    for theme in atomized_json['themes']:
        theme_text = reconstruct_text(theme)
        doc = nlp(theme_text)
        theme['entities'] = extract_entities(doc)
        
        for para in theme['paragraphs']:
            para_doc = nlp(para['text'])
            para['entities'] = extract_entities(para_doc)
            
            for sent in para['sentences']:
                sent_doc = nlp(sent['text'])
                sent['entities'] = extract_entities(sent_doc)
                
    return atomized_json
```

**Entity Browser Features**:
1. Entity type filter (checkboxes for all types)
2. Search by entity name (autocomplete)
3. View all occurrences with context (5 words before/after)
4. Click entity → jump to location in text
5. Entity frequency chart (bar chart of top 50)
6. Entity co-occurrence matrix (which entities appear together)
7. Export entity index as CSV

**Deliverables**:
- `enhanced_atomized.json` - Atomized text + entity tags
- `entity_extraction.py` - NER processing script
- `entity_browser.html` - Interactive entity explorer
- `custom_military_patterns.json` - Pattern definitions
- `entity_statistics.json` - Frequency, co-occurrence data
- `README_entities.md` - Entity taxonomy documentation

---

## 📊 SHARED RESOURCES & COORDINATION

### Common Data Formats

**Entity JSON Structure**:
```json
{
  "text": "Staff Sergeant",
  "label": "RANK",
  "start_char": 127,
  "end_char": 141,
  "sentence_id": "S00042",
  "context": "...talked to Staff Sergeant about..."
}
```

**Sentiment JSON Structure**:
```json
{
  "sentence_id": "S00042",
  "vader_compound": 0.34,
  "textblob_polarity": 0.2,
  "composite_score": 0.27,
  "classification": "positive"
}
```

**Temporal Marker Structure**:
```json
{
  "sentence_id": "S00042",
  "primary_tense": "past",
  "temporal_adverbs": ["then", "later"],
  "chronological_hint": "deployment",
  "narrative_time": 0.42,
  "inferred_chronological": "2004-2005"
}
```

### Integration Points

1. **Cross-Reference Entities + Sentiment**: Which entities correlate with positive/negative sentiment?
2. **Temporal + Sentiment**: How does emotional tone change over narrative time vs. chronological time?
3. **Network + Entities**: Show entity relationships in semantic network
4. **All → Master Dashboard**: Combine all analyses into unified interface

---

## 🚀 GETTING STARTED

### For Each Agent:

1. **Read Base Data**:
   ```python
   import json
   with open('Tomb_of_the_Unknowns_atomized.json', 'r') as f:
       data = json.load(f)
   ```

2. **Install Dependencies**:
   ```bash
   pip install spacy vaderSentiment textblob plotly scikit-learn
   python -m spacy download en_core_web_trf
   ```

3. **Create Your Working Branch**:
   ```bash
   git checkout -b feature/your-todo-name
   ```

4. **Output Naming Convention**:
   - Scripts: `{feature}_analysis.py`
   - Data: `{feature}_data.json`
   - Viz: `{feature}_visualization.html`
   - Docs: `README_{feature}.md`

5. **Submit Work**:
   - Commit to your branch
   - Include sample outputs in `/samples/`
   - Document in README with usage examples

---

## 📋 SUCCESS CRITERIA

Each work package should deliver:
- ✅ Functional standalone HTML visualization
- ✅ Reusable Python analysis script
- ✅ Structured JSON data output
- ✅ Documentation with examples
- ✅ Performance: Process 54MB JSON in <5 minutes
- ✅ UX: Responsive design, loading indicators, error handling
- ✅ Code: PEP 8 compliant, type hints, docstrings

---

## 🔄 ITERATION PLAN

### Phase 1 (Current): Core Analytics
- Semantic Network (Gemini)
- Temporal Flow (Jules)
- Sentiment Mapping (Copilot)
- Entity Recognition (Code)

### Phase 2 (Next): Comparative & Interactive
- Readability metrics
- Stylometric analysis
- Search interface
- Comparative tools

### Phase 3 (Future): Advanced ML
- Topic modeling (LDA)
- Text generation (GPT-based)
- Thematic clustering
- 3D visualizations

---

**Questions?** Reference the base files in `<repo-root>/`:
- `atomize_manuscript.py` - See original atomization logic
- `atomized_modern.html` - Reference for glassmorphic design patterns
- `atomized_analysis.html` - Example Chart.js implementation

**Let's build something extraordinary.** 🎖️
