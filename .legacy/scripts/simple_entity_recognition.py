#!/usr/bin/env python3
"""
Simple Entity Recognition - Pattern-based extraction without spaCy
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

from project_paths import PROCESSED_DIR, RAW_DATA_PATH

def extract_entities(text):
    """Extract entities using pattern matching"""
    entities = {
        'PERSON': [],
        'RANK': [],
        'LOCATION': [],
        'EQUIPMENT': [],
        'UNIT': [],
        'TEMPORAL': []
    }
    
    # Military ranks
    ranks = ['Staff Sergeant', 'Gunnery Sergeant', 'Lieutenant', 'Captain', 
             'Corpsman', 'Sergeant', 'Private', 'Colonel', 'General']
    for rank in ranks:
        if rank in text:
            entities['RANK'].append(rank)
    
    # Names (capitalized words followed by capitalized words)
    name_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b'
    names = re.findall(name_pattern, text)
    for name in names:
        if name not in ranks and not any(r in name for r in ranks):
            entities['PERSON'].append(name)
    
    # Equipment
    equipment = ['M40', 'M16', 'rifle', 'mask', 'Thunderbird', 'weapon']
    for equip in equipment:
        if equip in text.lower():
            entities['EQUIPMENT'].append(equip)
    
    # Locations
    location_keywords = ['Arlington', 'Vietnam', 'Iraq', 'Afghanistan', 'Tomb']
    for loc in location_keywords:
        if loc in text:
            entities['LOCATION'].append(loc)
    
    # Units
    unit_keywords = ['Marine Corps', 'platoon', 'squad', 'battalion', 'regiment']
    for unit in unit_keywords:
        if unit in text:
            entities['UNIT'].append(unit)
    
    # Temporal markers
    temporal_keywords = ['morning', 'evening', 'night', 'day', 'hour', 'minute', 
                        'dawn', 'dusk', 'midnight', 'noon']
    for temp in temporal_keywords:
        if temp in text.lower():
            entities['TEMPORAL'].append(temp)
    
    return entities

def process_atomized_data():
    """Process atomized JSON and extract entities"""
    
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    enhanced_data = data.copy()
    entity_stats = defaultdict(Counter)
    
    # Process each sentence
    for theme in enhanced_data['themes']:
        for para in theme['paragraphs']:
            for sent in para['sentences']:
                text = sent['text']
                entities = extract_entities(text)
                sent['entities'] = entities
                
                # Update statistics
                for entity_type, values in entities.items():
                    for value in values:
                        entity_stats[entity_type][value] += 1
    
    # Save enhanced data
    enhanced_path = PROCESSED_DIR / 'enhanced_atomized.json'
    with open(enhanced_path, 'w', encoding='utf-8') as f:
        json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
    
    # Save statistics
    stats = {
        'total_entities': sum(sum(counter.values()) for counter in entity_stats.values()),
        'by_type': {
            entity_type: {
                'total': sum(counter.values()),
                'unique': len(counter),
                'top_10': dict(counter.most_common(10))
            }
            for entity_type, counter in entity_stats.items()
        }
    }
    
    stats_path = PROCESSED_DIR / 'entity_statistics.json'
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    
    print("✅ Entity recognition complete!")
    print(f"   Total entities: {stats['total_entities']}")
    for entity_type, info in stats['by_type'].items():
        print(f"   {entity_type}: {info['total']} ({info['unique']} unique)")

if __name__ == '__main__':
    process_atomized_data()
