from __future__ import annotations

import re
from collections import Counter


ETHOS_MARKERS = {"according", "study", "evidence", "expert", "source", "citation"}
PATHOS_MARKERS = {
    "fear",
    "love",
    "grief",
    "rage",
    "hope",
    "joy",
    "pain",
    "sacred",
    "mythic",
}
LOGOS_MARKERS = {"therefore", "because", "hence", "thus", "if", "then", "proof", "logic"}
FALLACY_PATTERNS = {
    "bandwagon": re.compile(r"\beveryone knows\b", flags=re.IGNORECASE),
    "false dilemma": re.compile(r"\beither\b.+\bor\b", flags=re.IGNORECASE),
    "ad hominem": re.compile(r"\byou are (stupid|ignorant|worthless)\b", flags=re.IGNORECASE),
}


class RhetoricalAnalyzer:
    def analyze(self, text: str) -> dict:
        tokens = re.findall(r"[\w'-]+", text.lower())
        if not tokens:
            return {
                "ethos_score": 0.0,
                "pathos_score": 0.0,
                "logos_score": 0.0,
                "strategies": [],
                "fallacies": [],
                "explainability": {"token_count": 0, "marker_counts": {}},
            }

        counts = Counter(tokens)
        denom = max(len(tokens), 1)

        ethos = sum(counts[m] for m in ETHOS_MARKERS) / denom
        pathos = sum(counts[m] for m in PATHOS_MARKERS) / denom
        logos = sum(counts[m] for m in LOGOS_MARKERS) / denom

        strategy_ranking = sorted(
            [("ethos", ethos), ("pathos", pathos), ("logos", logos)],
            key=lambda item: item[1],
            reverse=True,
        )
        strategies = [name for name, value in strategy_ranking if value > 0]

        fallacies = [name for name, pattern in FALLACY_PATTERNS.items() if pattern.search(text)]

        return {
            "ethos_score": round(min(1.0, ethos * 10), 4),
            "pathos_score": round(min(1.0, pathos * 10), 4),
            "logos_score": round(min(1.0, logos * 10), 4),
            "strategies": strategies,
            "fallacies": fallacies,
            "explainability": {
                "token_count": len(tokens),
                "marker_counts": {
                    "ethos": sum(counts[m] for m in ETHOS_MARKERS),
                    "pathos": sum(counts[m] for m in PATHOS_MARKERS),
                    "logos": sum(counts[m] for m in LOGOS_MARKERS),
                },
            },
        }
