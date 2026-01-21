"""
Sentiment Chart Adapter - Chart.js sentiment visualization.

Generates emotional arc and sentiment distribution charts from sentiment analysis output.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...core.ontology import AnalysisOutput
from ...core.registry import registry
from ..base import BaseVisualizationAdapter


@registry.register_adapter("sentiment_chart")
class SentimentChartAdapter(BaseVisualizationAdapter):
    """
    Chart.js adapter for sentiment analysis visualization.

    Features:
    - Emotional arc line chart
    - Theme comparison bar chart
    - Classification distribution pie chart
    - Top positive/negative sentences
    """

    name = "sentiment_chart"
    description = "Chart.js sentiment analysis visualizations"
    supported_analysis = ["sentiment"]

    def get_chartjs_script(
        self,
        sentence_data: List[Dict],
        theme_stats: Dict[str, Dict],
        overall_stats: Dict[str, Any],
        peaks: Dict[str, List],
    ) -> str:
        """Generate Chart.js visualization script."""
        return f"""
        const sentenceData = {json.dumps(sentence_data, indent=2)};
        const themeStats = {json.dumps(theme_stats, indent=2)};
        const overallStats = {json.dumps(overall_stats, indent=2)};
        const peaks = {json.dumps(peaks, indent=2)};

        // Emotional Arc Line Chart
        new Chart(document.getElementById('emotional-arc'), {{
            type: 'line',
            data: {{
                labels: sentenceData.map((_, i) => i + 1),
                datasets: [{{
                    label: 'Composite Sentiment',
                    data: sentenceData.map(s => s.composite_score),
                    borderColor: 'rgba(78, 205, 196, 1)',
                    backgroundColor: 'rgba(78, 205, 196, 0.1)',
                    fill: true,
                    tension: 0.4
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ labels: {{ color: 'white' }} }},
                    tooltip: {{
                        callbacks: {{
                            afterLabel: function(context) {{
                                const sent = sentenceData[context.dataIndex];
                                return sent.text.substring(0, 60) + '...';
                            }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        title: {{ display: true, text: 'Sentence Number', color: 'white' }},
                        ticks: {{ color: 'white' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }}
                    }},
                    y: {{
                        title: {{ display: true, text: 'Sentiment Score', color: 'white' }},
                        ticks: {{ color: 'white' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        min: -1, max: 1
                    }}
                }}
            }}
        }});

        // Theme Comparison Bar Chart
        const themeLabels = Object.values(themeStats).map(t => t.title);
        const themeMeans = Object.values(themeStats).map(t => t.mean_sentiment);

        new Chart(document.getElementById('theme-comparison'), {{
            type: 'bar',
            data: {{
                labels: themeLabels,
                datasets: [{{
                    label: 'Mean Sentiment',
                    data: themeMeans,
                    backgroundColor: themeMeans.map(v =>
                        v >= 0 ? 'rgba(44, 160, 44, 0.8)' : 'rgba(214, 39, 40, 0.8)'
                    )
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ labels: {{ color: 'white' }} }} }},
                scales: {{
                    x: {{ ticks: {{ color: 'white' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
                    y: {{
                        ticks: {{ color: 'white' }},
                        grid: {{ color: 'rgba(255,255,255,0.1)' }},
                        min: -1, max: 1
                    }}
                }}
            }}
        }});

        // Classification Distribution Pie Chart
        const classLabels = Object.keys(overallStats.classification_counts);
        const classCounts = Object.values(overallStats.classification_counts);

        new Chart(document.getElementById('classification-dist'), {{
            type: 'doughnut',
            data: {{
                labels: classLabels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
                datasets: [{{
                    data: classCounts,
                    backgroundColor: [
                        'rgba(44, 160, 44, 0.8)',
                        'rgba(214, 39, 40, 0.8)',
                        'rgba(127, 127, 127, 0.8)'
                    ]
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{ position: 'bottom', labels: {{ color: 'white' }} }}
                }}
            }}
        }});

        // Populate peak sentences using safe DOM methods
        function createPeakItem(sentence, isPositive) {{
            const li = document.createElement('li');

            const scoreSpan = document.createElement('span');
            scoreSpan.style.color = isPositive ? '#4ECDC4' : '#FF6B6B';
            scoreSpan.textContent = isPositive
                ? '[+' + sentence.composite_score.toFixed(2) + ']'
                : '[' + sentence.composite_score.toFixed(2) + ']';
            li.appendChild(scoreSpan);

            const textNode = document.createTextNode(' ' + sentence.text.substring(0, 80) + '...');
            li.appendChild(textNode);

            return li;
        }}

        const positiveList = document.getElementById('positive-peaks');
        const negativeList = document.getElementById('negative-peaks');

        peaks.most_positive.slice(0, 5).forEach(s => {{
            positiveList.appendChild(createPeakItem(s, true));
        }});

        peaks.most_negative.slice(0, 5).forEach(s => {{
            negativeList.appendChild(createPeakItem(s, false));
        }});
        """

    def generate(
        self,
        analysis: AnalysisOutput,
        output_path: Path,
        config: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Generate sentiment chart visualization.

        Args:
            analysis: Sentiment analysis output
            output_path: Output file path
            config: Optional configuration
        """
        self._config = config or {}

        sentence_data = analysis.data.get("sentence_sentiments", [])
        theme_stats = analysis.data.get("theme_statistics", {})
        overall_stats = analysis.data.get("overall_statistics", {})
        peaks = analysis.data.get("emotional_peaks", {"most_positive": [], "most_negative": []})

        title = self._config.get("title", "Sentiment Analysis")

        content = f"""
        <div class="glass">
            <h1>💭 {title}</h1>
            <p class="subtitle">Emotional landscape with customized sentiment scoring</p>
        </div>

        <div class="glass stats">
            <div class="stat-box">
                <div class="stat-value">{overall_stats.get('total_sentences', 0)}</div>
                <div class="stat-label">Total Sentences</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #4ECDC4">{overall_stats.get('classification_counts', {}).get('positive', 0)}</div>
                <div class="stat-label">Positive</div>
            </div>
            <div class="stat-box">
                <div class="stat-value" style="color: #FF6B6B">{overall_stats.get('classification_counts', {}).get('negative', 0)}</div>
                <div class="stat-label">Negative</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">{overall_stats.get('classification_counts', {}).get('neutral', 0)}</div>
                <div class="stat-label">Neutral</div>
            </div>
        </div>

        <div class="glass">
            <h2 style="margin-bottom: 15px;">📈 Emotional Arc</h2>
            <div style="height: 300px;"><canvas id="emotional-arc"></canvas></div>
        </div>

        <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
            <div class="glass">
                <h2 style="margin-bottom: 15px;">📊 Theme Comparison</h2>
                <div style="height: 250px;"><canvas id="theme-comparison"></canvas></div>
            </div>
            <div class="glass">
                <h2 style="margin-bottom: 15px;">🎯 Classification</h2>
                <div style="height: 250px;"><canvas id="classification-dist"></canvas></div>
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
            <div class="glass">
                <h2 style="margin-bottom: 15px; color: #4ECDC4;">🌟 Most Positive</h2>
                <ul id="positive-peaks" style="list-style: none; padding: 0;">
                </ul>
            </div>
            <div class="glass">
                <h2 style="margin-bottom: 15px; color: #FF6B6B;">💔 Most Negative</h2>
                <ul id="negative-peaks" style="list-style: none; padding: 0;">
                </ul>
            </div>
        </div>
        """

        styles = """
        #positive-peaks li, #negative-peaks li {
            padding: 10px;
            margin-bottom: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 8px;
            font-size: 0.9em;
            line-height: 1.4;
        }
        """

        head_extras = '<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>'
        scripts = self.get_chartjs_script(sentence_data, theme_stats, overall_stats, peaks)

        html = self.wrap_html(
            title=title,
            content=content,
            scripts=scripts,
            styles=styles,
            head_extras=head_extras,
        viz_type="sentiment",
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        return output_path
