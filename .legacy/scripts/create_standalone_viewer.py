#!/usr/bin/env python3
"""
Create a self-contained HTML file with embedded atomized data (first 3 themes as sample)
"""

import json
from pathlib import Path

from project_paths import RAW_DATA_PATH, VISUALIZATIONS_DIR

def create_standalone_viewer(json_file, output_file):
    # Load the full data
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Create a sample with first 3 themes for demonstration
    sample_data = {
        'title': data['title'],
        'author': data['author'],
        'themes': data['themes'][:3]  # Just first 3 themes for manageable size
    }
    
    # Embed the data in the HTML
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tomb of the Unknowns - Atomized View</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Georgia', serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .controls {
            position: sticky;
            top: 0;
            background: #2c3e50;
            color: white;
            padding: 15px;
            margin: -40px -40px 30px -40px;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        
        .controls h2 {
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .toggle-group {
            display: flex;
            flex-wrap: wrap;
            gap: 15px;
            align-items: center;
        }
        
        .toggle-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .toggle-item input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }
        
        .toggle-item label {
            cursor: pointer;
            font-size: 0.95em;
            user-select: none;
        }
        
        .stats {
            margin-top: 10px;
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .notice {
            background: #f39c12;
            color: white;
            padding: 10px;
            margin-top: 10px;
            border-radius: 3px;
            font-size: 0.85em;
        }
        
        .title {
            text-align: center;
            margin-bottom: 10px;
        }
        
        .title h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .title .author {
            font-style: italic;
            font-size: 1.2em;
            color: #666;
        }
        
        .theme {
            margin: 40px 0;
            position: relative;
        }
        
        .theme-title {
            font-size: 1.8em;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }
        
        .paragraph {
            margin: 20px 0;
            position: relative;
        }
        
        .sentence {
            display: inline;
            position: relative;
        }
        
        .word {
            display: inline;
            position: relative;
        }
        
        .letter {
            display: inline;
            position: relative;
        }
        
        /* ID Display Styles */
        .id-badge {
            font-family: 'Courier New', monospace;
            font-size: 0.7em;
            padding: 2px 6px;
            border-radius: 3px;
            margin: 0 4px;
            font-weight: bold;
            white-space: nowrap;
            cursor: help;
            vertical-align: middle;
        }
        
        .theme-id {
            background: #e74c3c;
            color: white;
            display: inline-block;
            margin-right: 10px;
        }
        
        .paragraph-id {
            background: #9b59b6;
            color: white;
        }
        
        .sentence-id {
            background: #3498db;
            color: white;
        }
        
        .word-id {
            background: #f39c12;
            color: white;
        }
        
        .letter-id {
            background: #2ecc71;
            color: white;
            font-size: 0.6em;
        }
        
        /* Hidden by default */
        .theme .theme-id,
        .paragraph .paragraph-id,
        .sentence .sentence-id,
        .word .word-id,
        .letter .letter-id {
            display: none;
        }
        
        /* Show when toggled */
        body.show-theme-ids .theme .theme-id,
        body.show-paragraph-ids .paragraph .paragraph-id,
        body.show-sentence-ids .sentence .sentence-id,
        body.show-word-ids .word .word-id,
        body.show-letter-ids .letter .letter-id {
            display: inline-block;
        }
        
        /* Highlight on hover */
        body.show-theme-ids .theme:hover {
            background: rgba(231, 76, 60, 0.05);
        }
        
        body.show-paragraph-ids .paragraph:hover {
            background: rgba(155, 89, 182, 0.05);
        }
        
        body.show-sentence-ids .sentence:hover {
            background: rgba(52, 152, 219, 0.1);
        }
        
        body.show-word-ids .word:hover {
            background: rgba(243, 156, 18, 0.15);
        }
        
        body.show-letter-ids .letter:hover {
            background: rgba(46, 204, 113, 0.2);
        }
        
        .legend {
            margin-top: 30px;
            padding: 20px;
            background: #ecf0f1;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .legend h3 {
            margin-bottom: 10px;
        }
        
        .legend-item {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="controls">
            <h2>Atomized View Controls</h2>
            <div class="toggle-group">
                <div class="toggle-item">
                    <input type="checkbox" id="toggle-themes" checked>
                    <label for="toggle-themes">Theme IDs</label>
                </div>
                <div class="toggle-item">
                    <input type="checkbox" id="toggle-paragraphs">
                    <label for="toggle-paragraphs">Paragraph IDs</label>
                </div>
                <div class="toggle-item">
                    <input type="checkbox" id="toggle-sentences">
                    <label for="toggle-sentences">Sentence IDs</label>
                </div>
                <div class="toggle-item">
                    <input type="checkbox" id="toggle-words">
                    <label for="toggle-words">Word IDs</label>
                </div>
                <div class="toggle-item">
                    <input type="checkbox" id="toggle-letters">
                    <label for="toggle-letters">Letter IDs</label>
                </div>
            </div>
            <div class="stats" id="stats"></div>
            <div class="notice">
                📌 Sample view: First 3 themes only (for performance). Full manuscript has 49 themes.
            </div>
        </div>
        
        <div class="title">
            <h1 id="manuscript-title">Loading...</h1>
            <div class="author" id="manuscript-author"></div>
        </div>
        
        <div id="content"></div>
        
        <div class="legend">
            <h3>ID Legend</h3>
            <div class="legend-item"><span class="id-badge theme-id" style="display: inline-block;">T###</span> Theme (Section)</div>
            <div class="legend-item"><span class="id-badge paragraph-id" style="display: inline-block;">P####</span> Paragraph</div>
            <div class="legend-item"><span class="id-badge sentence-id" style="display: inline-block;">S#####</span> Sentence</div>
            <div class="legend-item"><span class="id-badge word-id" style="display: inline-block;">W######</span> Word</div>
            <div class="legend-item"><span class="id-badge letter-id" style="display: inline-block;">L########</span> Letter</div>
        </div>
    </div>
    
    <script>
        // Embedded data
        const manuscriptData = ''' + json.dumps(sample_data) + ''';
        
        function renderManuscript(data) {
            document.getElementById('manuscript-title').textContent = data.title;
            document.getElementById('manuscript-author').textContent = 'by ' + data.author;
            
            const content = document.getElementById('content');
            content.innerHTML = '';
            
            // Render each theme
            data.themes.forEach(theme => {
                const themeDiv = document.createElement('div');
                themeDiv.className = 'theme';
                
                const themeTitle = document.createElement('div');
                themeTitle.className = 'theme-title';
                themeTitle.innerHTML = `<span class="id-badge theme-id">${theme.theme_id}</span>${theme.theme_title}`;
                themeDiv.appendChild(themeTitle);
                
                // Render paragraphs
                theme.paragraphs.forEach(para => {
                    const paraDiv = document.createElement('div');
                    paraDiv.className = 'paragraph';
                    
                    const paraId = document.createElement('span');
                    paraId.className = 'id-badge paragraph-id';
                    paraId.textContent = para.paragraph_id;
                    paraId.title = `Paragraph ${para.paragraph_id} in ${para.theme_id}`;
                    paraDiv.appendChild(paraId);
                    
                    // Render sentences
                    para.sentences.forEach((sent, sentIdx) => {
                        const sentSpan = document.createElement('span');
                        sentSpan.className = 'sentence';
                        
                        const sentId = document.createElement('span');
                        sentId.className = 'id-badge sentence-id';
                        sentId.textContent = sent.sentence_id;
                        sentId.title = `Sentence ${sent.sentence_id} in ${sent.paragraph_id}`;
                        sentSpan.appendChild(sentId);
                        
                        // Render words
                        sent.words.forEach((word, wordIdx) => {
                            const wordSpan = document.createElement('span');
                            wordSpan.className = 'word';
                            
                            const wordId = document.createElement('span');
                            wordId.className = 'id-badge word-id';
                            wordId.textContent = word.word_id;
                            wordId.title = `Word ${word.word_id}: "${word.text}" in ${word.sentence_id}`;
                            wordSpan.appendChild(wordId);
                            
                            // Render letters
                            word.letters.forEach(letter => {
                                const letterSpan = document.createElement('span');
                                letterSpan.className = 'letter';
                                
                                const letterId = document.createElement('span');
                                letterId.className = 'id-badge letter-id';
                                letterId.textContent = letter.letter_id;
                                letterId.title = `Letter ${letter.letter_id}: "${letter.char}" in ${letter.word_id}`;
                                letterSpan.appendChild(letterId);
                                
                                const letterText = document.createTextNode(letter.char);
                                letterSpan.appendChild(letterText);
                                
                                wordSpan.appendChild(letterSpan);
                            });
                            
                            sentSpan.appendChild(wordSpan);
                            
                            // Add space after word (except last word)
                            if (wordIdx < sent.words.length - 1) {
                                sentSpan.appendChild(document.createTextNode(' '));
                            }
                        });
                        
                        paraDiv.appendChild(sentSpan);
                        
                        // Add space after sentence (except last sentence)
                        if (sentIdx < para.sentences.length - 1) {
                            paraDiv.appendChild(document.createTextNode(' '));
                        }
                    });
                    
                    themeDiv.appendChild(paraDiv);
                });
                
                content.appendChild(themeDiv);
            });
        }
        
        function updateStats(data) {
            const themeCount = data.themes.length;
            let paraCount = 0, sentCount = 0, wordCount = 0, letterCount = 0;
            
            data.themes.forEach(theme => {
                paraCount += theme.paragraphs.length;
                theme.paragraphs.forEach(para => {
                    sentCount += para.sentences.length;
                    para.sentences.forEach(sent => {
                        wordCount += sent.words.length;
                        sent.words.forEach(word => {
                            letterCount += word.letters.length;
                        });
                    });
                });
            });
            
            document.getElementById('stats').innerHTML = 
                `Themes: ${themeCount}/49 | Paragraphs: ${paraCount} | Sentences: ${sentCount} | Words: ${wordCount} | Letters: ${letterCount}`;
        }
        
        // Toggle controls
        document.getElementById('toggle-themes').addEventListener('change', (e) => {
            document.body.classList.toggle('show-theme-ids', e.target.checked);
        });
        
        document.getElementById('toggle-paragraphs').addEventListener('change', (e) => {
            document.body.classList.toggle('show-paragraph-ids', e.target.checked);
        });
        
        document.getElementById('toggle-sentences').addEventListener('change', (e) => {
            document.body.classList.toggle('show-sentence-ids', e.target.checked);
        });
        
        document.getElementById('toggle-words').addEventListener('change', (e) => {
            document.body.classList.toggle('show-word-ids', e.target.checked);
        });
        
        document.getElementById('toggle-letters').addEventListener('change', (e) => {
            document.body.classList.toggle('show-letter-ids', e.target.checked);
        });
        
        // Initialize with theme IDs showing
        document.body.classList.add('show-theme-ids');
        
        // Render on load
        renderManuscript(manuscriptData);
        updateStats(manuscriptData);
    </script>
</body>
</html>'''
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Standalone viewer created: {output_file}")
    print("This version embeds the first 3 themes as a sample.")
    print("Open it in any browser - no server required!")

if __name__ == "__main__":
    create_standalone_viewer(
        RAW_DATA_PATH,
        VISUALIZATIONS_DIR / "atomized_viewer_standalone.html"
    )
