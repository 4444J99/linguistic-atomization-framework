#!/usr/bin/env python3
"""
Create ultra-modern interactive visual analysis with glassmorphism, animations, and interactivity
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
                    
                    clean_word = ''.join(c for c in word['text'].lower() 
                                        if c.isalnum() or c == "'")
                    if clean_word:
                        analysis['word_frequency'][clean_word] += 1
                    
                    word_length = len(word['letters'])
                    analysis['word_lengths'].append(word_length)
                    
                    for letter in word['letters']:
                        analysis['counts']['letters'] += 1
                        theme_analysis['letters'] += 1
                        
                        if letter['char'].isalpha():
                            analysis['letter_frequency'][letter['char'].lower()] += 1
            
            analysis['paragraph_lengths'].append(para_word_count)
        
        analysis['themes_detail'].append(theme_analysis)
    
    analysis['averages'] = {
        'words_per_sentence': analysis['counts']['words'] / analysis['counts']['sentences'] if analysis['counts']['sentences'] > 0 else 0,
        'sentences_per_paragraph': analysis['counts']['sentences'] / analysis['counts']['paragraphs'] if analysis['counts']['paragraphs'] > 0 else 0,
        'words_per_paragraph': analysis['counts']['words'] / analysis['counts']['paragraphs'] if analysis['counts']['paragraphs'] > 0 else 0,
        'letters_per_word': analysis['counts']['letters'] / analysis['counts']['words'] if analysis['counts']['words'] > 0 else 0
    }
    
    return analysis

def create_modern_visualization(analysis, output_file: Path):
    """Create ultra-modern glassmorphic visualization with animations"""
    
    top_words = analysis['word_frequency'].most_common(50)
    letter_freq = sorted(analysis['letter_frequency'].most_common(), key=lambda x: x[0])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{analysis['metadata']['title']} - Interactive Analysis</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            background-size: 400% 400%;
            animation: gradientShift 15s ease infinite;
            color: #1a1a2e;
            padding: 20px;
            min-height: 100vh;
            overflow-x: hidden;
        }}
        
        @keyframes gradientShift {{
            0% {{ background-position: 0% 50%; }}
            50% {{ background-position: 100% 50%; }}
            100% {{ background-position: 0% 50%; }}
        }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
        }}
        
        /* Glassmorphism styles */
        .glass {{
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.2);
        }}
        
        .glass-dark {{
            background: rgba(0, 0, 0, 0.2);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
        }}
        
        /* Header */
        .header {{
            padding: 40px;
            margin-bottom: 30px;
            text-align: center;
            animation: fadeInDown 1s ease;
        }}
        
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .header h1 {{
            font-size: 3.5em;
            font-weight: 800;
            color: white;
            text-shadow: 2px 2px 20px rgba(0,0,0,0.3);
            margin-bottom: 15px;
            letter-spacing: -1px;
        }}
        
        .header .subtitle {{
            font-size: 1.4em;
            color: rgba(255,255,255,0.9);
            font-weight: 400;
        }}
        
        .header .badge {{
            display: inline-block;
            margin-top: 20px;
            padding: 10px 25px;
            background: rgba(255,255,255,0.25);
            backdrop-filter: blur(10px);
            border-radius: 50px;
            color: white;
            font-weight: 600;
            font-size: 0.9em;
            animation: pulse 2s ease-in-out infinite;
        }}
        
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.05); }}
        }}
        
        /* Stats Grid */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            padding: 30px;
            text-align: center;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            cursor: pointer;
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.8s ease backwards;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(45deg, rgba(255,255,255,0.1), rgba(255,255,255,0));
            opacity: 0;
            transition: opacity 0.3s;
        }}
        
        .stat-card:hover::before {{
            opacity: 1;
        }}
        
        .stat-card:hover {{
            transform: translateY(-10px) scale(1.02);
            box-shadow: 0 15px 45px 0 rgba(31, 38, 135, 0.3);
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .stat-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .stat-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .stat-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .stat-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .stat-card:nth-child(5) {{ animation-delay: 0.5s; }}
        
        .stat-icon {{
            font-size: 2.5em;
            margin-bottom: 15px;
            animation: float 3s ease-in-out infinite;
        }}
        
        @keyframes float {{
            0%, 100% {{ transform: translateY(0px); }}
            50% {{ transform: translateY(-10px); }}
        }}
        
        .stat-number {{
            font-size: 3em;
            font-weight: 800;
            color: white;
            margin-bottom: 10px;
            text-shadow: 2px 2px 10px rgba(0,0,0,0.2);
        }}
        
        .stat-label {{
            color: rgba(255,255,255,0.9);
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 2px;
            font-weight: 600;
        }}
        
        /* Word Cloud */
        .word-cloud {{
            padding: 40px;
            margin-bottom: 30px;
            animation: fadeIn 1s ease;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        .word-cloud h3 {{
            font-size: 1.8em;
            color: white;
            margin-bottom: 25px;
            font-weight: 700;
        }}
        
        .word-cloud-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
        }}
        
        .word-item {{
            padding: 10px 20px;
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            border-radius: 50px;
            transition: all 0.3s ease;
            cursor: pointer;
            font-weight: 600;
            animation: fadeInScale 0.5s ease backwards;
        }}
        
        @keyframes fadeInScale {{
            from {{
                opacity: 0;
                transform: scale(0.8);
            }}
            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}
        
        .word-item:hover {{
            transform: scale(1.15) rotate(2deg);
            background: rgba(255, 255, 255, 0.35);
            box-shadow: 0 8px 25px rgba(0,0,0,0.2);
        }}
        
        /* Charts */
        .chart-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 25px;
            margin-bottom: 30px;
        }}
        
        .chart-container {{
            padding: 35px;
            transition: all 0.4s ease;
            animation: fadeIn 1s ease;
        }}
        
        .chart-container:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 50px 0 rgba(31, 38, 135, 0.3);
        }}
        
        .chart-container h3 {{
            font-size: 1.5em;
            color: white;
            margin-bottom: 25px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .chart-wrapper {{
            position: relative;
            height: 350px;
        }}
        
        /* Themes List */
        .themes-list {{
            padding: 40px;
            animation: fadeIn 1.2s ease;
        }}
        
        .themes-list h3 {{
            font-size: 1.8em;
            color: white;
            margin-bottom: 25px;
            font-weight: 700;
        }}
        
        .theme-item {{
            padding: 20px;
            margin: 15px 0;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-left: 4px solid rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            transition: all 0.3s ease;
            cursor: pointer;
            animation: slideInLeft 0.5s ease backwards;
        }}
        
        @keyframes slideInLeft {{
            from {{
                opacity: 0;
                transform: translateX(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}
        
        .theme-item:hover {{
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(10px);
            border-left-width: 8px;
        }}
        
        .theme-title {{
            font-weight: 700;
            color: white;
            margin-bottom: 12px;
            font-size: 1.1em;
        }}
        
        .theme-stats {{
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            font-size: 0.9em;
            color: rgba(255,255,255,0.85);
        }}
        
        .theme-stat {{
            display: flex;
            align-items: center;
            gap: 6px;
            padding: 5px 12px;
            background: rgba(0,0,0,0.15);
            border-radius: 20px;
        }}
        
        /* Loading animation */
        .loading {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
            animation: fadeOut 0.5s ease 1s forwards;
        }}
        
        @keyframes fadeOut {{
            to {{
                opacity: 0;
                pointer-events: none;
            }}
        }}
        
        .loading-spinner {{
            width: 60px;
            height: 60px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }}
        
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 12px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.1);
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: rgba(255,255,255,0.3);
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: rgba(255,255,255,0.5);
        }}
    </style>
</head>
<body>
    <div class="loading">
        <div class="loading-spinner"></div>
    </div>
    
    <div class="container">
        <div class="header glass">
            <h1>{analysis['metadata']['title']}</h1>
            <div class="subtitle">by {analysis['metadata']['author']}</div>
            <div class="badge">
                🎨 Interactive Atomization Analysis
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card glass">
                <div class="stat-icon">📚</div>
                <div class="stat-number" data-target="{analysis['counts']['themes']}">{analysis['counts']['themes']}</div>
                <div class="stat-label">Themes</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon">📄</div>
                <div class="stat-number" data-target="{analysis['counts']['paragraphs']}">{analysis['counts']['paragraphs']}</div>
                <div class="stat-label">Paragraphs</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon">📝</div>
                <div class="stat-number" data-target="{analysis['counts']['sentences']}">{analysis['counts']['sentences']}</div>
                <div class="stat-label">Sentences</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon">📖</div>
                <div class="stat-number" data-target="{analysis['counts']['words']}">{analysis['counts']['words']}</div>
                <div class="stat-label">Words</div>
            </div>
            <div class="stat-card glass">
                <div class="stat-icon">🔤</div>
                <div class="stat-number" data-target="{analysis['counts']['letters']}">{analysis['counts']['letters']}</div>
                <div class="stat-label">Letters</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card glass-dark">
                <div class="stat-number">{analysis['averages']['words_per_sentence']:.1f}</div>
                <div class="stat-label">Words / Sentence</div>
            </div>
            <div class="stat-card glass-dark">
                <div class="stat-number">{analysis['averages']['sentences_per_paragraph']:.1f}</div>
                <div class="stat-label">Sentences / Paragraph</div>
            </div>
            <div class="stat-card glass-dark">
                <div class="stat-number">{analysis['averages']['words_per_paragraph']:.1f}</div>
                <div class="stat-label">Words / Paragraph</div>
            </div>
            <div class="stat-card glass-dark">
                <div class="stat-number">{analysis['averages']['letters_per_word']:.1f}</div>
                <div class="stat-label">Letters / Word</div>
            </div>
        </div>
        
        <div class="word-cloud glass">
            <h3>✨ Top 50 Most Frequent Words</h3>
            <div class="word-cloud-container">
                {"".join([f'<span class="word-item" style="font-size: {min(0.8 + (count/top_words[0][1]) * 1.5, 2.2)}em; animation-delay: {i*0.02}s;" title="{count} occurrences">{word}</span>' for i, (word, count) in enumerate(top_words)])}
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container glass">
                <h3>📊 Letter Frequency Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="letterChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container glass">
                <h3>📏 Word Length Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="wordLengthChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="chart-grid">
            <div class="chart-container glass">
                <h3>📐 Sentence Length Distribution</h3>
                <div class="chart-wrapper">
                    <canvas id="sentenceLengthChart"></canvas>
                </div>
            </div>
            
            <div class="chart-container glass">
                <h3>📑 Theme Size Comparison</h3>
                <div class="chart-wrapper">
                    <canvas id="themeChart"></canvas>
                </div>
            </div>
        </div>
        
        <div class="themes-list glass">
            <h3>🎯 All Themes Breakdown</h3>
            {"".join([f'''
            <div class="theme-item" style="animation-delay: {i*0.05}s;">
                <div class="theme-title">{theme['id']}: {theme['title']}</div>
                <div class="theme-stats">
                    <div class="theme-stat">📄 {theme['paragraphs']} paragraphs</div>
                    <div class="theme-stat">📝 {theme['sentences']} sentences</div>
                    <div class="theme-stat">📖 {theme['words']} words</div>
                    <div class="theme-stat">🔤 {theme['letters']} letters</div>
                </div>
            </div>
            ''' for i, theme in enumerate(analysis['themes_detail'])])}
        </div>
    </div>
    
    <script>
        // Number counter animation
        function animateValue(element, start, end, duration) {{
            const range = end - start;
            const increment = end > start ? 1 : -1;
            const stepTime = Math.abs(Math.floor(duration / range));
            let current = start;
            const timer = setInterval(() => {{
                current += increment;
                element.textContent = current.toLocaleString();
                if (current === end) {{
                    clearInterval(timer);
                }}
            }}, stepTime);
        }}
        
        // Animate all stat numbers
        setTimeout(() => {{
            document.querySelectorAll('.stat-number[data-target]').forEach(el => {{
                const target = parseInt(el.getAttribute('data-target'));
                animateValue(el, 0, target, 2000);
            }});
        }}, 500);
        
        // Chart.js configuration
        Chart.defaults.color = 'rgba(255, 255, 255, 0.9)';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    display: false
                }},
                tooltip: {{
                    backgroundColor: 'rgba(0, 0, 0, 0.8)',
                    backdropFilter: 'blur(10px)',
                    padding: 12,
                    cornerRadius: 8,
                    titleFont: {{ size: 14, weight: 'bold' }},
                    bodyFont: {{ size: 13 }}
                }}
            }},
            scales: {{
                x: {{
                    grid: {{
                        color: 'rgba(255, 255, 255, 0.1)'
                    }},
                    ticks: {{
                        color: 'rgba(255, 255, 255, 0.9)'
                    }}
                }},
                y: {{
                    grid: {{
                        color: 'rgba(255, 255, 255, 0.1)'
                    }},
                    ticks: {{
                        color: 'rgba(255, 255, 255, 0.9)'
                    }}
                }}
            }},
            animation: {{
                duration: 2000,
                easing: 'easeInOutQuart'
            }}
        }};
        
        // Letter frequency chart
        const letterCtx = document.getElementById('letterChart').getContext('2d');
        new Chart(letterCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([l[0] for l in letter_freq])},
                datasets: [{{
                    label: 'Frequency',
                    data: {json.dumps([l[1] for l in letter_freq])},
                    backgroundColor: 'rgba(255, 255, 255, 0.3)',
                    borderColor: 'rgba(255, 255, 255, 0.8)',
                    borderWidth: 2,
                    borderRadius: 6
                }}]
            }},
            options: chartOptions
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
            type: 'line',
            data: {{
                labels: sortedLengths,
                datasets: [{{
                    label: 'Number of Words',
                    data: sortedLengths.map(len => wordLengthCounts[len]),
                    backgroundColor: 'rgba(255, 200, 87, 0.2)',
                    borderColor: 'rgba(255, 200, 87, 1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(255, 200, 87, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }}]
            }},
            options: chartOptions
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
                    backgroundColor: 'rgba(123, 97, 255, 0.3)',
                    borderColor: 'rgba(123, 97, 255, 1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(123, 97, 255, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 7
                }}]
            }},
            options: chartOptions
        }});
        
        // Theme comparison chart
        const themeCtx = document.getElementById('themeChart').getContext('2d');
        const themeChartOptions = {{...chartOptions}};
        themeChartOptions.indexAxis = 'y';
        
        new Chart(themeCtx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps([t['title'][:30] + '...' if len(t['title']) > 30 else t['title'] for t in analysis['themes_detail']])},
                datasets: [{{
                    label: 'Words',
                    data: {json.dumps([t['words'] for t in analysis['themes_detail']])},
                    backgroundColor: 'rgba(240, 147, 251, 0.4)',
                    borderColor: 'rgba(240, 147, 251, 1)',
                    borderWidth: 2,
                    borderRadius: 6
                }}]
            }},
            options: themeChartOptions
        }});
        
        // Interactive theme item clicks
        document.querySelectorAll('.theme-item').forEach(item => {{
            item.addEventListener('click', () => {{
                item.style.animation = 'pulse 0.5s ease';
                setTimeout(() => {{
                    item.style.animation = '';
                }}, 500);
            }});
        }});
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Modern glassmorphic visualization created: {output_file}")

if __name__ == "__main__":
    json_file = RAW_DATA_PATH
    output_file = VISUALIZATIONS_DIR / "atomized_modern.html"
    
    print("Analyzing manuscript...")
    analysis = analyze_manuscript(json_file)
    
    print("Creating modern visualization...")
    create_modern_visualization(analysis, output_file)
    
    print("Done! Open the file in your browser.")
