#!/usr/bin/env python3
"""
Temporal Flow Analysis - JULES WORK PACKAGE
Analyzes narrative timeline, tense shifts, and chronological structure

Author: AI Agent (Jules)
Date: 2025-11-20
Todo: #2 - Temporal Flow Visualization
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List

from project_paths import PROCESSED_DIR, RAW_DATA_PATH

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

class TemporalAnalyzer:
    """Analyze temporal structure of narrative"""
    
    # Temporal marker patterns
    TEMPORAL_ADVERBS = [
        'then', 'now', 'later', 'before', 'after', 'once', 'when',
        'while', 'during', 'until', 'since', 'ago', 'soon', 'already',
        'eventually', 'finally', 'previously', 'formerly', 'currently'
    ]
    
    PAST_INDICATORS = ['was', 'were', 'had', 'did', 'went', 'saw', 'told', 'asked']
    PRESENT_INDICATORS = ['is', 'are', 'am', 'do', 'does', 'see', 'tell', 'ask']
    FUTURE_INDICATORS = ['will', 'shall', 'going to', 'would', 'could', 'might']
    
    FLASHBACK_SIGNALS = [
        'remember', 'recalled', 'looking back', 'once upon', 'used to',
        'in the past', 'back then', 'years ago', 'deployment'
    ]
    
    FLASHFORWARD_SIGNALS = [
        'will be asked', 'years later', 'in the future', 'someday',
        'when I return', 'back home', 'after the war'
    ]
    
    def __init__(self, atomized_json_path: Path = RAW_DATA_PATH):
        with open(atomized_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.temporal_data = []
        self.tense_distribution = defaultdict(lambda: Counter())

        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                # Small model keeps load time reasonable; upgrade when fine-tuned model is available
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                self.nlp = None
        
    def detect_tense(self, sentence: str) -> str:
        """Detect primary tense; prefer spaCy POS/morph when available."""
        # spaCy-based detection for higher fidelity
        if self.nlp:
            doc = self.nlp(sentence)
            counts = {'past': 0, 'present': 0, 'future': 0}
            for token in doc:
                if token.pos_ in {"VERB", "AUX"}:
                    # Morphological tense information (e.g., Past, Pres, Fut)
                    tenses = token.morph.get('Tense')
                    for tense in tenses:
                        t = tense.lower()
                        if t.startswith('past'):
                            counts['past'] += 1
                        elif t.startswith('pres'):
                            counts['present'] += 1
                        elif t.startswith('fut'):
                            counts['future'] += 1
            if max(counts.values()) > 0:
                return max(counts, key=counts.get)

        # Fallback keyword scan when spaCy is unavailable or inconclusive
        sentence_lower = sentence.lower()
        past_count = sum(1 for word in self.PAST_INDICATORS if word in sentence_lower)
        present_count = sum(1 for word in self.PRESENT_INDICATORS if word in sentence_lower)
        future_count = sum(1 for word in self.FUTURE_INDICATORS if word in sentence_lower)

        counts = {
            'past': past_count,
            'present': present_count,
            'future': future_count
        }

        if max(counts.values()) == 0:
            return 'ambiguous'

        return max(counts, key=counts.get)
    
    def extract_temporal_markers(self, text: str) -> List[str]:
        """Find temporal adverbs and phrases in text"""
        markers = []
        text_lower = text.lower()
        
        for adverb in self.TEMPORAL_ADVERBS:
            if adverb in text_lower:
                markers.append(adverb)
        
        return markers
    
    def detect_narrative_shifts(self, sentence: str) -> Dict[str, bool]:
        """Identify flashbacks and flashforwards"""
        sentence_lower = sentence.lower()
        
        has_flashback = any(signal in sentence_lower for signal in self.FLASHBACK_SIGNALS)
        has_flashforward = any(signal in sentence_lower for signal in self.FLASHFORWARD_SIGNALS)
        
        return {
            'is_flashback': has_flashback,
            'is_flashforward': has_flashforward,
            'is_linear': not (has_flashback or has_flashforward)
        }
    
    def analyze_themes(self):
        """Analyze temporal structure of each theme"""
        for theme in self.data.get('themes', []):
            theme_id = theme['id']
            theme_title = theme.get('title', theme_id)
            
            # Analyze paragraphs
            for paragraph in theme.get('paragraphs', []):
                # Analyze sentences
                for sentence in paragraph.get('sentences', []):
                    sentence_id = sentence['id']
                    sentence_text = sentence['text']
                    
                    # Detect tense
                    tense = self.detect_tense(sentence_text)
                    self.tense_distribution[theme_id][tense] += 1
                    
                    # Extract temporal markers
                    markers = self.extract_temporal_markers(sentence_text)
                    
                    # Detect narrative shifts
                    shifts = self.detect_narrative_shifts(sentence_text)
                    
                    # Store analysis
                    self.temporal_data.append({
                        'sentence_id': sentence_id,
                        'theme_id': theme_id,
                        'theme_title': theme_title,
                        'text': sentence_text[:100] + '...' if len(sentence_text) > 100 else sentence_text,
                        'tense': tense,
                        'temporal_markers': markers,
                        'is_flashback': shifts['is_flashback'],
                        'is_flashforward': shifts['is_flashforward'],
                        'narrative_type': 'flashback' if shifts['is_flashback'] else 
                                         'flashforward' if shifts['is_flashforward'] else 'linear'
                    })
    
    def generate_sankey_data(self) -> Dict:
        """
        Generate Sankey diagram data for narrative flow
        Shows movement between narrative sections and chronological periods
        """
        nodes: List[Dict] = []
        links: List[Dict] = []

        # Theme nodes keep manuscript order
        node_index = {}
        for theme in self.data.get('themes', []):
            node_index[theme['id']] = len(nodes)
            nodes.append({
                'id': theme['id'],
                'name': theme.get('title', theme['id']),
                'group': 'theme'
            })

        # Chronological buckets derived from tense distribution
        chrono_labels = ['past', 'present', 'future', 'ambiguous']
        for label in chrono_labels:
            node_id = f"CHRONO:{label}"
            node_index[node_id] = len(nodes)
            nodes.append({
                'id': node_id,
                'name': f"Chronology – {label}",
                'group': 'chronology'
            })

        # Links: theme → chronological bucket weighted by detected tense counts
        for theme_id, tense_counts in self.tense_distribution.items():
            for label in chrono_labels:
                count = tense_counts.get(label, 0) if isinstance(tense_counts, dict) else tense_counts[label]
                if count > 0:
                    links.append({
                        'source': node_index.get(theme_id, 0),
                        'target': node_index[f"CHRONO:{label}"],
                        'value': int(count),
                        'type': 'tense_flow'
                    })

        return {
            'nodes': nodes,
            'links': links
        }
    
    def export_temporal_data(self, output_path: Path = PROCESSED_DIR / 'temporal_data.json'):
        """Export temporal analysis results"""
        # Compile results
        results = {
            'sentence_analysis': self.temporal_data,
            'theme_tense_distribution': dict(self.tense_distribution),
            'overall_statistics': {
                'total_sentences': len(self.temporal_data),
                'tense_counts': Counter([s['tense'] for s in self.temporal_data]),
                'flashback_count': sum(1 for s in self.temporal_data if s['is_flashback']),
                'flashforward_count': sum(1 for s in self.temporal_data if s['is_flashforward']),
                'linear_count': sum(1 for s in self.temporal_data if s['narrative_type'] == 'linear')
            },
            'sankey_data': self.generate_sankey_data()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Temporal data exported: {len(self.temporal_data)} sentences analyzed")
        return output_path


def main():
    """Main execution"""
    print("🚀 Temporal Flow Analysis - Starting...")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = TemporalAnalyzer(RAW_DATA_PATH)
    
    # Analyze temporal structure
    print("\n⏰ Analyzing tenses and temporal markers...")
    analyzer.analyze_themes()
    
    # Display summary statistics
    print("\n📊 Summary Statistics:")
    total = len(analyzer.temporal_data)
    tense_counts = Counter([s['tense'] for s in analyzer.temporal_data])
    
    print(f"   Total sentences analyzed: {total}")
    print(f"   Past tense: {tense_counts['past']} ({tense_counts['past']/total*100:.1f}%)")
    print(f"   Present tense: {tense_counts['present']} ({tense_counts['present']/total*100:.1f}%)")
    print(f"   Future tense: {tense_counts['future']} ({tense_counts['future']/total*100:.1f}%)")
    
    flashbacks = sum(1 for s in analyzer.temporal_data if s['is_flashback'])
    flashforwards = sum(1 for s in analyzer.temporal_data if s['is_flashforward'])
    print(f"   Flashbacks detected: {flashbacks}")
    print(f"   Flashforwards detected: {flashforwards}")
    
    # Export data
    print("\n💾 Exporting temporal data...")
    analyzer.export_temporal_data()
    
    print("\n" + "=" * 60)
    print("✨ Complete! Next steps:")
    print("   1. Review temporal_data.json")
    print("   2. Create temporal_flow.html with Plotly.js")
    print("   3. Implement timeline + Sankey diagram")
    print("   4. Add tense distribution heatmap")


if __name__ == '__main__':
    main()
