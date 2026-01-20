#!/usr/bin/env python3
"""
Atomize Manuscript - Core Atomization Engine
Parses "Tomb of the Unknowns" into hierarchical structure with unique IDs

Hierarchy:
- Theme (T###): Sections marked with ##
- Paragraph (P####): Separated by blank lines
- Sentence (S#####): Split on punctuation
- Word (W######): Whitespace separated
- Letter (L########): Individual characters

Output: Tomb_of_the_Unknowns_atomized.json
"""

import json
import re
from collections import Counter
from pathlib import Path

from project_paths import RAW_DATA_PATH, SOURCE_MARKDOWN

def atomize_manuscript(markdown_path):
    """Parse markdown manuscript into atomized structure"""
    
    with open(markdown_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split into themes by ## headers
    theme_pattern = r'^## (.+)$'
    parts = re.split(theme_pattern, content, flags=re.MULTILINE)
    
    # First part might be title/preamble
    themes = []
    theme_counter = 1
    paragraph_counter = 1
    sentence_counter = 1
    word_counter = 1
    letter_counter = 1
    
    for i in range(1, len(parts), 2):
        if i+1 >= len(parts):
            break
        
        theme_title = parts[i].strip()
        theme_text = parts[i+1].strip()
        
        theme_id = f"T{theme_counter:03d}"
        
        # Split into paragraphs (double newline)
        paragraphs_text = re.split(r'\n\n+', theme_text)
        paragraphs = []
        
        for para_text in paragraphs_text:
            if not para_text.strip():
                continue
            
            para_id = f"P{paragraph_counter:04d}"
            
            # Split into sentences
            sentences_text = re.split(r'(?<=[.!?])\s+', para_text)
            sentences = []
            
            for sent_text in sentences_text:
                if not sent_text.strip():
                    continue
                
                sent_id = f"S{sentence_counter:05d}"
                
                # Split into words
                words_text = re.findall(r'\S+', sent_text)
                words = []
                
                for word_text in words_text:
                    word_id = f"W{word_counter:06d}"
                    
                    # Split into letters
                    letters = []
                    for char in word_text:
                        letter_id = f"L{letter_counter:08d}"
                        letters.append({
                            'id': letter_id,
                            'char': char,
                            'word_id': word_id,
                            'sentence_id': sent_id,
                            'paragraph_id': para_id,
                            'theme_id': theme_id
                        })
                        letter_counter += 1
                    
                    words.append({
                        'id': word_id,
                        'text': word_text,
                        'letter_count': len(letters),
                        'letters': letters,
                        'sentence_id': sent_id,
                        'paragraph_id': para_id,
                        'theme_id': theme_id
                    })
                    word_counter += 1
                
                sentences.append({
                    'id': sent_id,
                    'text': sent_text,
                    'word_count': len(words),
                    'words': words,
                    'paragraph_id': para_id,
                    'theme_id': theme_id
                })
                sentence_counter += 1
            
            paragraphs.append({
                'id': para_id,
                'text': para_text,
                'sentence_count': len(sentences),
                'sentences': sentences,
                'theme_id': theme_id
            })
            paragraph_counter += 1
        
        themes.append({
            'id': theme_id,
            'title': theme_title,
            'text': theme_text,
            'paragraph_count': len(paragraphs),
            'paragraphs': paragraphs
        })
        theme_counter += 1
    
    # Compile statistics
    total_themes = len(themes)
    total_paragraphs = paragraph_counter - 1
    total_sentences = sentence_counter - 1
    total_words = word_counter - 1
    total_letters = letter_counter - 1
    
    result = {
        'metadata': {
            'title': 'Tomb of the Unknowns',
            'author': 'Christopher Notarnicola',
            'atomized_date': '2025-11-20',
            'hierarchy': 'theme → paragraph → sentence → word → letter',
            'total_themes': total_themes,
            'total_paragraphs': total_paragraphs,
            'total_sentences': total_sentences,
            'total_words': total_words,
            'total_letters': total_letters
        },
        'themes': themes
    }
    
    return result


def main():
    """Main execution"""
    print("🚀 Atomizing Manuscript...")
    print("=" * 60)
    
    # Find markdown file
    markdown_path = SOURCE_MARKDOWN
    output_path = RAW_DATA_PATH
    
    print(f"\n📖 Reading: {markdown_path}")
    
    # Atomize
    result = atomize_manuscript(markdown_path)
    
    # Display statistics
    meta = result['metadata']
    print("\n📊 Atomization Complete:")
    print(f"   Themes: {meta['total_themes']:,}")
    print(f"   Paragraphs: {meta['total_paragraphs']:,}")
    print(f"   Sentences: {meta['total_sentences']:,}")
    print(f"   Words: {meta['total_words']:,}")
    print(f"   Letters: {meta['total_letters']:,}")
    
    # Export
    print(f"\n💾 Exporting to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    # Check file size
    import os
    file_size = os.path.getsize(output_path) / (1024 * 1024)
    print(f"   File size: {file_size:.1f} MB")
    
    print("\n" + "=" * 60)
    print("✨ Done! Ready for analysis.")


if __name__ == '__main__':
    main()
