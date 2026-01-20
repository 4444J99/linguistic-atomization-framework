#!/usr/bin/env python3
"""
Create comprehensive visual analysis of the atomized manuscript
"""

import json
from collections import Counter
from pathlib import Path

from project_paths import RAW_DATA_PATH, VISUALIZATIONS_DIR

def analyze_manuscript(json_file: Path):
    """Analyze the manuscript at all levels"""
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    analysis = {
        'metadata': {
            'title': data['title'],
            'author': data['author'],
            'total_themes': len(data['themes'])
        },
        'counts': {
            'themes': 0,
            'paragraphs': 0,
            'sentences': 0,
            'words': 0,
            'letters': 0
        },
        'themes_detail': [],
        'word_frequency': Counter(),
        'letter_frequency': Counter(),
        'sentence_lengths': [],
        'word_lengths': [],
        'paragraph_lengths': []
    }
    
    for theme in data['themes']:
        theme_analysis = {
            'id': theme['theme_id'],
            'title': theme['theme_title'],
            'paragraphs': len(theme['paragraphs']),
            'sentences': 0,
            'words': 0,
            'letters': 0
        }
        
        analysis['counts']['themes'] += 1
        
        for para in theme['paragraphs']:
            analysis['counts']['paragraphs'] += 1
            para_word_count = 0
            
            for sent in para['sentences']:
                analysis['counts']['sentences'] += 1
                theme_analysis['sentences'] += 1
                
                sent_word_count = len(sent['words'])
                analysis['sentence_lengths'].append(sent_word_count)
                
                for word in sent['words']:
                    analysis['counts']['words'] += 1
                    theme_analysis['words'] += 1
                    para_word_count += 1
                    
                    # Clean word for frequency analysis (remove punctuation)
                    clean_word = ''.join(c for c in word['text'].lower() 
                                        if c.isalnum() or c == "'")
                    if clean_word:
                        analysis['word_frequency'][clean_word] += 1
                    
                    word_length = len(word['letters'])
                    analysis['word_lengths'].append(word_length)
                    
                    for letter in word['letters']:
                        analysis['counts']['letters'] += 1
                        theme_analysis['letters'] += 1
                        
                        # Only count actual letters
                        if letter['char'].isalpha():
                            analysis['letter_frequency'][letter['char'].lower()] += 1
            
            analysis['paragraph_lengths'].append(para_word_count)
        
        analysis['themes_detail'].append(theme_analysis)
    
    # Calculate averages
    analysis['averages'] = {
        'words_per_sentence': analysis['counts']['words'] / analysis['counts']['sentences'] if analysis['counts']['sentences'] > 0 else 0,
        'sentences_per_paragraph': analysis['counts']['sentences'] / analysis['counts']['paragraphs'] if analysis['counts']['paragraphs'] > 0 else 0,
        'words_per_paragraph': analysis['counts']['words'] / analysis['counts']['paragraphs'] if analysis['counts']['paragraphs'] > 0 else 0,
        'letters_per_word': analysis['counts']['letters'] / analysis['counts']['words'] if analysis['counts']['words'] > 0 else 0
    }
    
    return analysis

def create_visualization_html(analysis, output_file: Path):
    """Create an interactive HTML visualization"""
    
    # Get top words and letters
    top_words = analysis['word_frequency'].most_common(50)
    letter_freq = analysis['letter_frequency'].most_common()
    
    # Sort letters alphabetically for chart
    letter_freq_sorted = sorted(letter_freq, key=lambda x: x[0])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis['metadata']['title']} - Visual Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 2.5em;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.2em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            text-transform: uppercase;
            font-size: 0.9em;
            letter-spacing: 1px;
        }}
        
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        
        .chart-container {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-container h3 {{
            margin-bottom: 20px;
            color: #2c3e50;
            font-size: 1.3em;
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 350px;
        }}
        
        .themes-list {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .themes-list h3 {{
            margin-bottom: 20px;
            color: #2c3e50;
            font-size: 1.3em;
        }}
        
        .theme-item {{
            padding: 15px;
            margin: 10px 0;
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            border-radius: 5px;
        }}
        
        .theme-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 8px;
        }}
        
        .theme-stats {{
            display: flex;
            gap: 20px;
            font-size: 0.9em;
            color: #7f8c8d;
        }}
        
        .theme-stat {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .word-cloud {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        
        .word-cloud h3 {{
            margin-bottom: 20px;
            color: #2c3e50;
        }}
        
        .word-cloud-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
        }}
        
        .word-item {{
            padding: 8px 15px;
            background: #667eea;
            color: white;
            border-radius: 20px;
            transition: all 0.3s;
            cursor: default;
        }}
        
        .word-item:hover {{
            transform: scale(1.1);
            background: #764ba2;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{analysis['metadata']['title']}</h1>
            <div class="subtitle">by {analysis['metadata']['author']}</div>
            <div class="subtitle" style="margin-top: 10px; font-size: 1em;">
                📊 Comprehensive Atomization Analysis
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{analysis['counts']['themes']}</div>
                <div class="stat-label">Themes</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['counts']['paragraphs']:,}</div>
                <div class="stat-label">Paragraphs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['counts']['sentences']:,}</div>
                <div class="stat-label">Sentences</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['counts']['words']:,}</div>
                <div class="stat-label">Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['counts']['letters']:,}</div>
                <div class="stat-label">Letters</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{analysis['averages']['words_per_sentence']:.1f}</div>
                <div class="stat-label">Words/Sentence</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['averages']['sentences_per_paragraph']:.1f}</div>
                <div class="stat-label">Sentences/Paragraph</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['averages']['words_per_paragraph']:.1f}</div>
                <div class="stat-label">Words/Paragraph</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{analysis['averages']['letters_per_word']:.1f}</div>
                <div class="stat-label">Letters/Word</div>
            </div>
        </div>
        
        <div class="word-cloud">
            <h3>Top 50 Most Frequent Words</h3>
            <div class="word-cloud-container">
                {"".join([f'<span class="word-item" style="font-size: {min(0.8 + (count/top_words[0][1]) * 1.2, 2)}em;" title="{count} occurrences">{word}</span>' for word, count in top_words])}
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container">
                <h3>Letter Frequency Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="letterChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Word Length Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="wordLengthChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container">
                <h3>Sentence Length Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="sentenceLengthChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container">
                <h3>Theme Size Comparison (by word count)</h3>
                <div class="chart-wrapper">
                    <canvas id="themeChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="themes-list">
            <h3>All Themes Breakdown</h3>
            {"".join([f'''
            <div class="theme-item">
                <div class="theme-title">{theme['id']}: {theme['title']}</div>
                <div class="theme-stats">
                    <div class="theme-stat">📄 {theme['paragraphs']} paragraphs</div>
                    <div class="theme-stat">📝 {theme['sentences']} sentences</div>
                    <div class="theme-stat">📖 {theme['words']} words</div>
                    <div class="theme-stat">🔤 {theme['letters']} letters</div>
                </div>
            </div>
            ''' for theme in analysis['themes_detail']])}
        </div>
    </div>
    
    <script>
        // Letter frequency chart
        const letterCtx = document.getElementById('letterChart').getContext('2d');
        new Chart(letterCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([l[0] for l in letter_freq_sorted])},
                datasets: [{{
                    label: 'Frequency',
                    data: {json.dumps([l[1] for l in letter_freq_sorted])},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Occurrences'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Letter'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Word length distribution
        const wordLengths = {json.dumps(analysis['word_lengths'])};
        const wordLengthCounts = {{}};
        wordLengths.forEach(len => {{
            wordLengthCounts[len] = (wordLengthCounts[len] || 0) + 1;
        }});
        const sortedLengths = Object.keys(wordLengthCounts).sort((a, b) => a - b).slice(0, 20);
        
        const wordLengthCtx = document.getElementById('wordLengthChart').getContext('2d');
        new Chart(wordLengthCtx, {{
            type: 'bar',
            data: {{
                labels: sortedLengths,
                datasets: [{{
                    label: 'Number of Words',
                    data: sortedLengths.map(len => wordLengthCounts[len]),
                    backgroundColor: 'rgba(243, 156, 18, 0.8)',
                    borderColor: 'rgba(243, 156, 18, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Count'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Word Length (letters)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Sentence length distribution
        const sentLengths = {json.dumps(analysis['sentence_lengths'])};
        const sentLengthCounts = {{}};
        sentLengths.forEach(len => {{
            const bucket = Math.floor(len / 5) * 5;
            sentLengthCounts[bucket] = (sentLengthCounts[bucket] || 0) + 1;
        }});
        const sortedSentLengths = Object.keys(sentLengthCounts).sort((a, b) => a - b).slice(0, 20);
        
        const sentLengthCtx = document.getElementById('sentenceLengthChart').getContext('2d');
        new Chart(sentLengthCtx, {{
            type: 'line',
            data: {{
                labels: sortedSentLengths.map(l => l + '-' + (parseInt(l) + 4)),
                datasets: [{{
                    label: 'Number of Sentences',
                    data: sortedSentLengths.map(len => sentLengthCounts[len]),
                    backgroundColor: 'rgba(52, 152, 219, 0.2)',
                    borderColor: 'rgba(52, 152, 219, 1)',
                    borderWidth: 2,
                    fill: true
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Count'
                        }}
                    }},
                    x: {{
                        title: {{
                            display: true,
                            text: 'Sentence Length (words)'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
        
        // Theme comparison chart
        const themeCtx = document.getElementById('themeChart').getContext('2d');
        new Chart(themeCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([t['title'][:30] + '...' if len(t['title']) > 30 else t['title'] for t in analysis['themes_detail']])},
                datasets: [{{
                    label: 'Words',
                    data: {json.dumps([t['words'] for t in analysis['themes_detail']])},
                    backgroundColor: 'rgba(155, 89, 182, 0.8)',
                    borderColor: 'rgba(155, 89, 182, 1)',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                scales: {{
                    x: {{
                        beginAtZero: true,
                        title: {{
                            display: true,
                            text: 'Word Count'
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Visual analysis created: {output_file}")

if __name__ == "__main__":
    json_file = RAW_DATA_PATH
    output_file = VISUALIZATIONS_DIR / "atomized_analysis.html"
    
    print("Analyzing manuscript...")
    analysis = analyze_manuscript(json_file)
    
    print("Creating visualization...")
    create_visualization_html(analysis, output_file)
    
    print(f"\nAnalysis Summary:")
    print(f"  Total themes: {analysis['counts']['themes']}")
    print(f"  Total words: {analysis['counts']['words']:,}")
    print(f"  Top 5 words: {', '.join([f'{w}({c})' for w, c in analysis['word_frequency'].most_common(5)])}")
    print(f"  Avg sentence length: {analysis['averages']['words_per_sentence']:.1f} words")
