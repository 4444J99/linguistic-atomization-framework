#!/usr/bin/env python3
"""
Semantic Network Analysis - GEMINI WORK PACKAGE
Creates graph-based visualization of thematic and entity relationships

Author: AI Agent (Gemini)
Date: 2025-11-20
Todo: #1 - Semantic Network Analysis Implementation
"""

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from project_paths import PROCESSED_DIR, RAW_DATA_PATH

class SemanticNetworkBuilder:
    """Build semantic network from atomized manuscript data"""
    
    def __init__(self, atomized_json_path: Path = RAW_DATA_PATH):
        with open(atomized_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        self.nodes = []
        self.edges = []
        self.entity_mentions = defaultdict(set)
        self.theme_texts = {}

        # Precompile simple patterns we fall back to until spaCy NER is available
        self.military_patterns = {
            'MILITARY_TERM': r'\b(Marine|Corpsman|Staff Sergeant|Lieutenant|platoon|convoy|deployment|patrol)\b',
            'LOCATION': r'\b(Iraq|Al Asad|Sal Sinjar|Manhattan|New York)\b',
            'EQUIPMENT': r'\b(M40|M16|rifle|truck|Thunderbird|mask)\b',
        }
        self.compiled_patterns = {
            label: re.compile(pattern, re.IGNORECASE)
            for label, pattern in self.military_patterns.items()
        }

        # Cache entities per theme for node/edge creation
        self.entities_by_theme = self.extract_entities()
        
    def _entity_key(self, text: str, label: str) -> str:
        """Stable ID for an entity node."""
        return f"{label}:{text.lower()}"

    def _extract_entities_from_text(self, text: str) -> List[Dict]:
        """Extract entities using pattern matching fallback."""
        found = []
        for label, pattern in self.compiled_patterns.items():
            for match in pattern.finditer(text):
                found.append({
                    'text': match.group(),
                    'label': label,
                    'start': match.start(),
                    'end': match.end(),
                })
        return found

    def extract_entities(self) -> Dict[str, Dict[str, List[Dict]]]:
        """Extract entities per theme and track mentions for graph nodes/edges."""
        entities = defaultdict(lambda: defaultdict(list))

        for theme in self.data.get('themes', []):
            theme_id = theme['id']
            theme_text = theme.get('text', '')

            for ent in self._extract_entities_from_text(theme_text):
                key = self._entity_key(ent['text'], ent['label'])
                self.entity_mentions[key].add(theme_id)
                entities[theme_id][ent['label']].append(ent)
        
        return entities
    
    def _bump_pairs(self, entities: List[Dict], cooccurrence: Dict[str, Dict[str, int]]):
        """Increment co-occurrence counts for a list of entities within one window."""
        # Use unique keys within window to avoid overweighting repeated matches
        unique_keys = list({self._entity_key(ent['text'], ent['label']) for ent in entities})
        for i, key_a in enumerate(unique_keys):
            for key_b in unique_keys[i + 1:]:
                cooccurrence[key_a][key_b] += 1
                cooccurrence[key_b][key_a] += 1

    def build_cooccurrence_matrix(self, window: str = 'paragraph') -> Dict[str, Dict[str, int]]:
        """
        Calculate entity co-occurrence within specified window
        
        Args:
            window: 'paragraph', 'theme', or 'sentence'
        """
        cooccurrence = defaultdict(lambda: defaultdict(int))

        if window not in {'paragraph', 'theme', 'sentence'}:
            raise ValueError("window must be 'paragraph', 'theme', or 'sentence'")

        for theme in self.data.get('themes', []):
            if window == 'theme':
                entities = self._extract_entities_from_text(theme.get('text', ''))
                self._bump_pairs(entities, cooccurrence)
                continue

            for paragraph in theme.get('paragraphs', []):
                if window == 'paragraph':
                    entities = self._extract_entities_from_text(paragraph.get('text', ''))
                    self._bump_pairs(entities, cooccurrence)
                elif window == 'sentence':
                    for sentence in paragraph.get('sentences', []):
                        entities = self._extract_entities_from_text(sentence.get('text', ''))
                        self._bump_pairs(entities, cooccurrence)

        return cooccurrence
    
    def calculate_theme_similarity(self) -> np.ndarray:
        """
        Calculate semantic similarity between themes using TF-IDF + cosine similarity
        """
        # Extract theme texts
        theme_ids = []
        theme_texts = []
        
        for theme in self.data.get('themes', []):
            theme_ids.append(theme['id'])
            theme_texts.append(theme.get('text', ''))
            self.theme_texts[theme['id']] = theme.get('text', '')
        
        # Calculate TF-IDF vectors
        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        tfidf_matrix = vectorizer.fit_transform(theme_texts)
        
        # Calculate cosine similarity
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        return theme_ids, similarity_matrix
    
    def create_nodes(self):
        """Create node list for D3.js force graph"""
        # Theme nodes
        for theme in self.data.get('themes', []):
            self.nodes.append({
                'id': theme['id'],
                'label': theme.get('title', theme['id']),
                'type': 'theme',
                'word_count': theme.get('word_count', 0),
                'size': 20,  # Large nodes for themes
                'color': '#1f77b4'
            })
        
        # Entity nodes (pattern-based fallback until spaCy NER is integrated)
        for key, themes in self.entity_mentions.items():
            label, text = key.split(':', 1)
            self.nodes.append({
                'id': key,
                'label': text,
                'type': 'entity',
                'entity_type': label,
                'size': 8,
                'mention_count': len(themes),
                'color': {
                    'MILITARY_TERM': '#d62728',
                    'LOCATION': '#2ca02c',
                    'EQUIPMENT': '#9467bd'
                }.get(label, '#7f7f7f')
            })
        
    def create_edges(self, similarity_threshold: float = 0.3):
        """
        Create edge list for D3.js force graph
        
        Args:
            similarity_threshold: Minimum similarity to create edge
        """
        theme_ids, similarity_matrix = self.calculate_theme_similarity()
        
        # Create edges between similar themes
        for i, theme_id_1 in enumerate(theme_ids):
            for j, theme_id_2 in enumerate(theme_ids):
                if i < j:  # Avoid duplicates
                    similarity = similarity_matrix[i][j]
                    if similarity > similarity_threshold:
                        self.edges.append({
                            'source': theme_id_1,
                            'target': theme_id_2,
                            'weight': float(similarity),
                            'type': 'semantic_similarity'
                        })

        # Sequential adjacency (narrative order between themes)
        for idx in range(len(theme_ids) - 1):
            self.edges.append({
                'source': theme_ids[idx],
                'target': theme_ids[idx + 1],
                'weight': 1.0,
                'type': 'sequential_adjacency'
            })

        # Co-occurrence edges between entities
        cooccurrence = self.build_cooccurrence_matrix(window='paragraph')
        for ent_a, neighbors in cooccurrence.items():
            for ent_b, count in neighbors.items():
                if ent_a < ent_b:  # enforce one direction
                    self.edges.append({
                        'source': ent_a,
                        'target': ent_b,
                        'weight': int(count),
                        'type': 'cooccurrence'
                    })

        # Theme → entity mention edges
        seen_mentions = set()
        for theme_id, entity_map in self.entities_by_theme.items():
            for entity_type, ent_list in entity_map.items():
                for ent in ent_list:
                    key = self._entity_key(ent['text'], ent['label'])
                    if (theme_id, key) in seen_mentions:
                        continue
                    seen_mentions.add((theme_id, key))
                    self.edges.append({
                        'source': theme_id,
                        'target': key,
                        'weight': 1.0,
                        'type': 'mention'
                    })
    
    def export_network_data(self, output_path: Path = PROCESSED_DIR / 'semantic_data.json'):
        """Export nodes and edges for D3.js visualization"""
        self.create_nodes()
        self.create_edges()
        
        network_data = {
            'nodes': self.nodes,
            'edges': self.edges,
            'metadata': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'similarity_threshold': 0.3,
                'created': '2025-11-20'
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(network_data, f, indent=2)
        
        print(f"✅ Network data exported: {len(self.nodes)} nodes, {len(self.edges)} edges")
        return output_path


def main():
    """Main execution"""
    print("🚀 Semantic Network Analysis - Starting...")
    print("=" * 60)
    
    # Build network
    builder = SemanticNetworkBuilder(RAW_DATA_PATH)
    
    # Extract entities
    print("\n📊 Extracting entities...")
    entities = builder.extract_entities()
    print(f"   Found entities in {len(entities)} themes")
    
    # Calculate similarities
    print("\n🔗 Calculating theme similarities...")
    theme_ids, similarity_matrix = builder.calculate_theme_similarity()
    print(f"   Computed {len(theme_ids)}x{len(theme_ids)} similarity matrix")
    
    # Export network data
    print("\n💾 Exporting network data...")
    output_file = builder.export_network_data()
    
    print("\n" + "=" * 60)
    print("✨ Complete! Next steps:")
    print("   1. Review semantic_data.json")
    print("   2. Create semantic_network.html with D3.js visualization")
    print("   3. Implement force-directed graph with zoom/filter controls")
    print("   4. Add entity nodes after entity recognition package complete")


if __name__ == '__main__':
    main()
