#!/usr/bin/env python3
"""
Emotional Sentiment Mapping - COPILOT WORK PACKAGE
Sentence-level sentiment analysis with military lexicon

Author: AI Agent (Copilot)
Date: 2025-11-20
Todo: #3 - Emotional Sentiment Mapping
"""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from project_paths import PROCESSED_DIR, RAW_DATA_PATH

# Note: Install these packages first
# pip install vaderSentiment textblob

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    from textblob import TextBlob
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("⚠️  Warning: vaderSentiment or textblob not installed")
    print("   Run: pip install vaderSentiment textblob")

class SentimentMapper:
    """Analyze emotional sentiment across manuscript"""
    
    # Custom military lexicon for VADER
    MILITARY_LEXICON = {
        # Negative terms
        'gunfire': -2.5,
        'explosion': -3.0,
        'blood': -2.8,
        'death': -3.2,
        'fear': -2.0,
        'enemy': -1.5,
        'attack': -2.3,
        'wounded': -2.5,
        'killed': -3.0,
        'infection': -2.0,
        'pain': -2.2,
        'trauma': -2.4,
        'war': -1.8,
        'combat': -1.5,
        'firefight': -2.1,
        'IED': -3.0,
        'casualty': -2.8,
        
        # Positive terms
        'safe': 2.0,
        'home': 1.8,
        'laughter': 2.3,
        'friend': 1.5,
        'smile': 1.8,
        'Semper Fidelis': 2.5,
        'Marine': 1.2,
        'victory': 2.5,
        'survived': 2.0,
        'reunite': 2.2,
        'celebration': 2.0,
        'love': 2.5,
        
        # Neutral/ambiguous (adjust defaults)
        'deployment': -0.5,
        'convoy': -0.3,
        'patrol': -0.4,
        'mission': 0.2,
        'orders': 0.0,
        'duty': 0.5,
        'service': 0.8,
        'rifle': -0.2,
        'uniform': 0.3,
    }
    
    def __init__(self, atomized_json_path: Path = RAW_DATA_PATH):
        with open(atomized_json_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        if SENTIMENT_AVAILABLE:
            self.vader = SentimentIntensityAnalyzer()
            # Add custom military lexicon
            self.vader.lexicon.update(self.MILITARY_LEXICON)
        else:
            self.vader = None
        
        self.sentiment_data = []
        
    def analyze_sentence(self, text: str) -> Dict:
        """
        Analyze sentiment of single sentence using VADER + TextBlob
        """
        if not SENTIMENT_AVAILABLE:
            return {
                'vader_compound': 0.0,
                'vader_pos': 0.0,
                'vader_neg': 0.0,
                'vader_neu': 1.0,
                'textblob_polarity': 0.0,
                'textblob_subjectivity': 0.0,
                'composite_score': 0.0,
                'classification': 'neutral'
            }
        
        # VADER analysis (good for social media, military slang)
        vader_scores = self.vader.polarity_scores(text)
        
        # TextBlob analysis (good for literary sentiment)
        blob = TextBlob(text)
        
        # Composite score: average of VADER compound and TextBlob polarity
        composite = (vader_scores['compound'] + blob.sentiment.polarity) / 2
        
        # Classify sentiment
        if composite >= 0.05:
            classification = 'positive'
        elif composite <= -0.05:
            classification = 'negative'
        else:
            classification = 'neutral'
        
        return {
            'vader_compound': vader_scores['compound'],
            'vader_pos': vader_scores['pos'],
            'vader_neg': vader_scores['neg'],
            'vader_neu': vader_scores['neu'],
            'textblob_polarity': blob.sentiment.polarity,
            'textblob_subjectivity': blob.sentiment.subjectivity,
            'composite_score': composite,
            'classification': classification
        }
    
    def analyze_all_sentences(self):
        """Analyze sentiment for every sentence in manuscript"""
        sentence_number = 0
        
        for theme in self.data.get('themes', []):
            theme_id = theme['id']
            theme_title = theme.get('title', theme_id)
            
            for paragraph in theme.get('paragraphs', []):
                for sentence in paragraph.get('sentences', []):
                    sentence_number += 1
                    sentence_id = sentence['id']
                    sentence_text = sentence['text']
                    
                    # Analyze sentiment
                    sentiment = self.analyze_sentence(sentence_text)
                    
                    # Store results
                    self.sentiment_data.append({
                        'sentence_id': sentence_id,
                        'sentence_number': sentence_number,
                        'theme_id': theme_id,
                        'theme_title': theme_title,
                        'text': sentence_text,
                        **sentiment
                    })
    
    def find_emotional_peaks(self, n: int = 10) -> Dict[str, List]:
        """Find most positive and negative sentences"""
        sorted_by_score = sorted(
            self.sentiment_data,
            key=lambda x: x['composite_score']
        )
        
        return {
            'most_negative': sorted_by_score[:n],
            'most_positive': sorted_by_score[-n:][::-1]
        }
    
    def calculate_theme_statistics(self) -> Dict:
        """Calculate sentiment statistics per theme"""
        from statistics import mean, stdev
        
        theme_stats = {}
        
        for theme in self.data.get('themes', []):
            theme_id = theme['id']
            
            # Get sentences for this theme
            theme_sentences = [
                s for s in self.sentiment_data 
                if s['theme_id'] == theme_id
            ]
            
            if not theme_sentences:
                continue
            
            scores = [s['composite_score'] for s in theme_sentences]
            
            theme_stats[theme_id] = {
                'title': theme['title'] if 'title' in theme else theme_id,
                'sentence_count': len(theme_sentences),
                'mean_sentiment': mean(scores),
                'stdev_sentiment': stdev(scores) if len(scores) > 1 else 0.0,
                'min_sentiment': min(scores),
                'max_sentiment': max(scores),
                'classification_counts': Counter([s['classification'] for s in theme_sentences])
            }
        
        return theme_stats
    
    def export_sentiment_data(self, output_path: Path = PROCESSED_DIR / 'sentiment_data.json'):
        """Export all sentiment analysis results"""
        peaks = self.find_emotional_peaks()
        theme_stats = self.calculate_theme_statistics()
        
        results = {
            'sentence_sentiments': self.sentiment_data,
            'emotional_peaks': peaks,
            'theme_statistics': theme_stats,
            'overall_statistics': {
                'total_sentences': len(self.sentiment_data),
                'classification_counts': Counter([s['classification'] for s in self.sentiment_data]),
                'mean_composite': sum(s['composite_score'] for s in self.sentiment_data) / len(self.sentiment_data)
            },
            'custom_lexicon': self.MILITARY_LEXICON
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        print(f"✅ Sentiment data exported: {len(self.sentiment_data)} sentences analyzed")
        return output_path


def main():
    """Main execution"""
    print("🚀 Sentiment Analysis - Starting...")
    print("=" * 60)
    
    if not SENTIMENT_AVAILABLE:
        print("\n❌ Required packages not installed. Exiting.")
        return
    
    # Initialize analyzer
    mapper = SentimentMapper(RAW_DATA_PATH)
    
    # Analyze all sentences
    print("\n💭 Analyzing sentiment for all sentences...")
    mapper.analyze_all_sentences()
    
    # Display summary
    print("\n📊 Summary Statistics:")
    print(f"   Total sentences: {len(mapper.sentiment_data)}")
    
    classifications = Counter([s['classification'] for s in mapper.sentiment_data])
    total = len(mapper.sentiment_data)
    print(f"   Positive: {classifications['positive']} ({classifications['positive']/total*100:.1f}%)")
    print(f"   Negative: {classifications['negative']} ({classifications['negative']/total*100:.1f}%)")
    print(f"   Neutral: {classifications['neutral']} ({classifications['neutral']/total*100:.1f}%)")
    
    # Show emotional peaks
    peaks = mapper.find_emotional_peaks(n=3)
    print("\n🔥 Top 3 Most Positive Sentences:")
    for i, sent in enumerate(peaks['most_positive'], 1):
        print(f"   {i}. [{sent['composite_score']:.2f}] {sent['text'][:80]}...")
    
    print("\n💔 Top 3 Most Negative Sentences:")
    for i, sent in enumerate(peaks['most_negative'], 1):
        print(f"   {i}. [{sent['composite_score']:.2f}] {sent['text'][:80]}...")
    
    # Export data
    print("\n💾 Exporting sentiment data...")
    mapper.export_sentiment_data()
    
    print("\n" + "=" * 60)
    print("✨ Complete! Next steps:")
    print("   1. Review sentiment_data.json")
    print("   2. Create sentiment_map.html with Chart.js")
    print("   3. Implement emotional arc line chart")
    print("   4. Add sentiment heatmap by theme")


if __name__ == '__main__':
    main()
