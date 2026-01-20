#!/usr/bin/env python3
"""
Entity Recognition & Tagging - CODE ASSISTANT WORK PACKAGE
Named Entity Recognition with military domain customization

Author: AI Agent (Code)
Date: 2025-11-20
Todo: #4 - Entity Recognition and Tagging
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Set

from project_paths import PROCESSED_DIR, RAW_DATA_PATH

# Note: Install spaCy and transformer model
# pip install spacy
# python -m spacy download en_core_web_trf

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    print("⚠️  Warning: spaCy not installed")
    print("   Run: pip install spacy")
    print("   Then: python -m spacy download en_core_web_trf")

class EntityRecognizer:
    """Extract and tag named entities with military domain knowledge"""
    
    # Custom entity patterns for military domain
    MILITARY_PATTERNS = [
        # Ranks
        {"label": "RANK", "pattern": "Staff Sergeant"},
        {"label": "RANK", "pattern": "Gunnery Sergeant"},
        {"label": "RANK", "pattern": "Lieutenant"},
        {"label": "RANK", "pattern": "Captain"},
        {"label": "RANK", "pattern": "Corpsman"},
        {"label": "RANK", "pattern": "Doc"},
        
        # Equipment
        {"label": "EQUIPMENT", "pattern": "M40"},
        {"label": "EQUIPMENT", "pattern": "M16"},
        {"label": "EQUIPMENT", "pattern": "field protective mask"},
        {"label": "EQUIPMENT", "pattern": "rifle"},
        {"label": "EQUIPMENT", "pattern": "Thunderbird"},
        
        # Military units
        {"label": "UNIT", "pattern": "Marine Corps"},
        {"label": "UNIT", "pattern": "platoon"},
        {"label": "UNIT", "pattern": "convoy"},
        {"label": "UNIT", "pattern": "company"},
        
        # Locations
        {"label": "LOCATION_MILITARY", "pattern": "Al Asad"},
        {"label": "LOCATION_MILITARY", "pattern": "Sal Sinjar"},
        {"label": "LOCATION_MILITARY", "pattern": "Camp"},
        
        # Military concepts
        {"label": "MILITARY_CONCEPT", "pattern": "deployment"},
        {"label": "MILITARY_CONCEPT", "pattern": "Semper Fidelis"},
        {"label": "MILITARY_CONCEPT", "pattern": "Operation Iraqi Freedom"},
    ]
    
    def __init__(self, atomized_json_path: Path = RAW_DATA_PATH):
        with open(atomized_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_trf")
                print("✅ Loaded transformer model: en_core_web_trf")
            except OSError:
                try:
                    self.nlp = spacy.load("en_core_web_sm")
                    print("✅ Loaded small model: en_core_web_sm")
                except OSError:
                    print("❌ No spaCy model found. Run: python -m spacy download en_core_web_sm")
                    self.nlp = None
            
            if self.nlp:
                # Add custom entity ruler
                if "entity_ruler" not in self.nlp.pipe_names:
                    ruler = self.nlp.add_pipe("entity_ruler", before="ner")
                    ruler.add_patterns(self.MILITARY_PATTERNS)
                    print(f"✅ Added {len(self.MILITARY_PATTERNS)} custom patterns")
        else:
            self.nlp = None
        
        self.entity_index = defaultdict(list)
        self.entity_counts = Counter()
        
    def extract_entities_from_text(self, text: str, context_id: str) -> List[Dict]:
        """Extract entities from text using spaCy NER"""
        if not self.nlp:
            return []
        
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity_data = {
                'text': ent.text,
                'label': ent.label_,
                'start_char': ent.start_char,
                'end_char': ent.end_char,
                'context_id': context_id
            }
            entities.append(entity_data)
            
            # Update index
            self.entity_index[ent.text].append(context_id)
            self.entity_counts[(ent.text, ent.label_)] += 1
        
        return entities
    
    def enhance_atomized_structure(self):
        """Add entity tags to all levels of atomized structure"""
        enhanced_data = self.data.copy()
        
        for theme in enhanced_data.get('themes', []):
            theme_id = theme['id']
            
            # Extract entities from full theme text
            theme_text = theme.get('text', '')
            theme['entities'] = self.extract_entities_from_text(theme_text, theme_id)
            
            # Process paragraphs
            for paragraph in theme.get('paragraphs', []):
                para_id = paragraph['id']
                para_text = paragraph.get('text', '')
                paragraph['entities'] = self.extract_entities_from_text(para_text, para_id)
                
                # Process sentences
                for sentence in paragraph.get('sentences', []):
                    sent_id = sentence['id']
                    sent_text = sentence['text']
                    sentence['entities'] = self.extract_entities_from_text(sent_text, sent_id)
        
        return enhanced_data
    
    def generate_entity_statistics(self) -> Dict:
        """Calculate entity frequency and co-occurrence statistics"""
        # Entity frequency
        entity_freq = {}
        for (text, label), count in self.entity_counts.most_common():
            if label not in entity_freq:
                entity_freq[label] = []
            entity_freq[label].append({
                'text': text,
                'count': count,
                'contexts': len(self.entity_index[text])
            })
        
        # Entity co-occurrence matrix
        cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for theme in self.data.get('themes', []):
            for paragraph in theme.get('paragraphs', []):
                # Get all entities in paragraph
                para_entities = set()
                for sentence in paragraph.get('sentences', []):
                    sent_text = sentence['text']
                    if self.nlp:
                        doc = self.nlp(sent_text)
                        para_entities.update([ent.text for ent in doc.ents])
                
                # Count co-occurrences
                entity_list = list(para_entities)
                for i, ent1 in enumerate(entity_list):
                    for ent2 in entity_list[i+1:]:
                        cooccurrence[ent1][ent2] += 1
                        cooccurrence[ent2][ent1] += 1
        
        return {
            'frequency_by_type': entity_freq,
            'cooccurrence_matrix': dict(cooccurrence),
            'total_unique_entities': len(self.entity_counts),
            'total_entity_mentions': sum(self.entity_counts.values())
        }
    
    def export_entity_data(self, enhanced_output: Path = PROCESSED_DIR / 'enhanced_atomized.json',
                          stats_output: Path = PROCESSED_DIR / 'entity_statistics.json'):
        """Export enhanced atomized data with entities"""
        
        # Enhance structure
        print("\n🔍 Extracting entities from all text levels...")
        enhanced_data = self.enhance_atomized_structure()
        
        # Generate statistics
        print("\n📊 Generating entity statistics...")
        stats = self.generate_entity_statistics()
        
        # Export enhanced data
        print(f"\n💾 Exporting enhanced atomized data...")
        with open(enhanced_output, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, indent=2)
        print(f"   Saved: {enhanced_output}")
        
        # Export statistics
        with open(stats_output, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        print(f"   Saved: {stats_output}")
        
        return enhanced_output, stats_output


def main():
    """Main execution"""
    print("🚀 Entity Recognition & Tagging - Starting...")
    print("=" * 60)
    
    if not SPACY_AVAILABLE:
        print("\n❌ spaCy not installed. Exiting.")
        return
    
    # Initialize recognizer
    recognizer = EntityRecognizer(RAW_DATA_PATH)
    
    if not recognizer.nlp:
        print("\n❌ No spaCy model available. Exiting.")
        return
    
    # Process and export
    enhanced_file, stats_file = recognizer.export_entity_data()
    
    # Display summary
    print("\n📊 Summary Statistics:")
    print(f"   Unique entities found: {len(recognizer.entity_counts)}")
    print(f"   Total mentions: {sum(recognizer.entity_counts.values())}")
    
    print("\n🏆 Top 10 Most Frequent Entities:")
    for (text, label), count in recognizer.entity_counts.most_common(10):
        print(f"   {count:4d}x [{label:20s}] {text}")
    
    print("\n" + "=" * 60)
    print("✨ Complete! Next steps:")
    print("   1. Review enhanced_atomized.json (with entity tags)")
    print("   2. Review entity_statistics.json")
    print("   3. Create entity_browser.html for interactive exploration")
    print("   4. Implement entity search and filtering interface")


if __name__ == '__main__':
    main()
