#!/usr/bin/env python3
"""
Create a visual sample and query interface for the atomized manuscript
"""

import json
from pathlib import Path

from project_paths import DERIVED_DIR, RAW_DATA_PATH

def load_atomized_data(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def create_sample_view(data, output_file):
    """Create a human-readable sample showing the ID hierarchy"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"ATOMIZED MANUSCRIPT: {data['title']}\n")
        f.write(f"Author: {data['author']}\n")
        f.write("=" * 80 + "\n\n")
        
        # Show first 2 themes as examples
        for theme in data['themes'][:2]:
            f.write(f"\n[{theme['theme_id']}] THEME: {theme['theme_title']}\n")
            f.write("-" * 80 + "\n")
            
            # Show first paragraph of each theme
            if theme['paragraphs']:
                para = theme['paragraphs'][0]
                f.write(f"\n  [{para['paragraph_id']}] PARAGRAPH:\n")
                
                # Show first 2 sentences
                for sent in para['sentences'][:2]:
                    f.write(f"\n    [{sent['sentence_id']}] SENTENCE: {sent['text'][:80]}...\n")
                    
                    # Show first 3 words
                    for word in sent['words'][:3]:
                        f.write(f"      [{word['word_id']}] WORD: '{word['text']}'\n")
                        
                        # Show all letters of first word
                        if word == sent['words'][0]:
                            f.write("        LETTERS: ")
                            for letter in word['letters']:
                                f.write(f"[{letter['letter_id']}:{letter['char']}] ")
                            f.write("\n")
                    
                    f.write(f"      ... ({len(sent['words'])} total words)\n")
                
                f.write(f"\n  ... ({len(para['sentences'])} total sentences in paragraph)\n")
            
            f.write(f"\n  ... ({len(theme['paragraphs'])} total paragraphs in theme)\n")
        
        f.write(f"\n\n... ({len(data['themes'])} total themes in manuscript)\n")
        
        # Add ID format legend
        f.write("\n" + "=" * 80 + "\n")
        f.write("ID FORMAT LEGEND:\n")
        f.write("  Theme:     T### (3 digits, e.g., T001)\n")
        f.write("  Paragraph: P#### (4 digits, e.g., P0000)\n")
        f.write("  Sentence:  S##### (5 digits, e.g., S00001)\n")
        f.write("  Word:      W###### (6 digits, e.g., W000001)\n")
        f.write("  Letter:    L######## (8 digits, e.g., L00000001)\n")
        f.write("\nEach ID is globally unique across the entire manuscript.\n")
        f.write("Lower-level IDs maintain references to their parent IDs.\n")

def create_index(data, output_file):
    """Create a navigable index of all themes and their IDs"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"INDEX: {data['title']}\n")
        f.write("=" * 80 + "\n\n")
        
        for theme in data['themes']:
            para_count = len(theme['paragraphs'])
            sent_count = sum(len(p['sentences']) for p in theme['paragraphs'])
            word_count = sum(len(s['words']) for p in theme['paragraphs'] 
                           for s in p['sentences'])
            
            f.write(f"{theme['theme_id']}: {theme['theme_title']}\n")
            f.write(f"  Paragraphs: {para_count} | Sentences: {sent_count} | Words: {word_count}\n")
            f.write(f"  First paragraph: {theme['paragraphs'][0]['paragraph_id'] if theme['paragraphs'] else 'N/A'}\n")
            f.write("\n")

def query_by_id(data, id_string):
    """Query the manuscript by any level of ID"""
    
    id_type = id_string[0]
    
    if id_type == 'T':
        # Find theme
        for theme in data['themes']:
            if theme['theme_id'] == id_string:
                return {
                    'type': 'theme',
                    'id': theme['theme_id'],
                    'title': theme['theme_title'],
                    'paragraph_count': len(theme['paragraphs'])
                }
    
    elif id_type == 'P':
        # Find paragraph
        for theme in data['themes']:
            for para in theme['paragraphs']:
                if para['paragraph_id'] == id_string:
                    return {
                        'type': 'paragraph',
                        'id': para['paragraph_id'],
                        'theme_id': para['theme_id'],
                        'text': para['text'][:200] + '...',
                        'sentence_count': len(para['sentences'])
                    }
    
    elif id_type == 'S':
        # Find sentence
        for theme in data['themes']:
            for para in theme['paragraphs']:
                for sent in para['sentences']:
                    if sent['sentence_id'] == id_string:
                        return {
                            'type': 'sentence',
                            'id': sent['sentence_id'],
                            'paragraph_id': sent['paragraph_id'],
                            'text': sent['text'],
                            'word_count': len(sent['words'])
                        }
    
    elif id_type == 'W':
        # Find word
        for theme in data['themes']:
            for para in theme['paragraphs']:
                for sent in para['sentences']:
                    for word in sent['words']:
                        if word['word_id'] == id_string:
                            return {
                                'type': 'word',
                                'id': word['word_id'],
                                'sentence_id': word['sentence_id'],
                                'text': word['text'],
                                'letter_count': len(word['letters'])
                            }
    
    elif id_type == 'L':
        # Find letter
        for theme in data['themes']:
            for para in theme['paragraphs']:
                for sent in para['sentences']:
                    for word in sent['words']:
                        for letter in word['letters']:
                            if letter['letter_id'] == id_string:
                                return {
                                    'type': 'letter',
                                    'id': letter['letter_id'],
                                    'word_id': letter['word_id'],
                                    'char': letter['char']
                                }
    
    return None

if __name__ == "__main__":
    # Load data
    data = load_atomized_data(RAW_DATA_PATH)
    
    # Create sample view
    sample_path = DERIVED_DIR / "atomized_sample.txt"
    create_sample_view(data, sample_path)
    print(f"Sample view created: {sample_path.name}")
    
    # Create index
    index_path = DERIVED_DIR / "atomized_index.txt"
    create_index(data, index_path)
    print(f"Index created: {index_path.name}")
    
    # Example queries
    print("\nExample queries:")
    print("-" * 40)
    
    examples = ['T001', 'P0000', 'S00001', 'W000001', 'L00000001']
    for ex_id in examples:
        result = query_by_id(data, ex_id)
        if result:
            print(f"\n{ex_id} ({result['type']}):")
            for key, val in result.items():
                if key not in ['type']:
                    print(f"  {key}: {val}")
