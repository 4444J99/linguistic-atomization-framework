"""
Evaluation Analysis Module - 9-Step Rhetorical Evaluation Framework.

Implements the "From Evaluation to Growth" framework:

Phase 1: EVALUATION
    1. Critique - Strengths and weaknesses assessment
    2. Logic Check - Internal consistency and argument flow
    3. Logos Review - Rational appeal analysis (evidence, facts)
    4. Pathos Review - Emotional resonance analysis
    5. Ethos Review - Credibility and authority markers

Phase 2: RISK
    6. Blind Spots - Overlooked areas and assumptions
    7. Shatter Points - Vulnerabilities and weak arguments

Phase 3: GROWTH
    8. Bloom - Emergent insights and expansion opportunities
    9. Evolve - Synthesized improvement recommendations

Each step operates across all atomization levels (letter → theme) with
aggregation from micro to macro.
"""

from __future__ import annotations

import re
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from statistics import mean, stdev
from typing import Any, Dict, List, Optional, Set, Tuple

from ..core.ontology import (
    AnalysisOutput,
    Atom,
    AtomLevel,
    Corpus,
    DomainProfile,
)
from ..core.registry import registry
from .base import BaseAnalysisModule

logger = logging.getLogger(__name__)

# Optional LLM support
try:
    from ..llm import (
        get_provider,
        LLMProvider,
        LLM_AVAILABLE,
        PromptChainExecutor,
        RhetoricalPromptLibrary,
        RhetoricalOutputParser,
        prompt_library,
    )
    CHAIN_AVAILABLE = True
except ImportError:
    get_provider = None
    LLMProvider = None
    LLM_AVAILABLE = False
    PromptChainExecutor = None
    RhetoricalPromptLibrary = None
    RhetoricalOutputParser = None
    prompt_library = None
    CHAIN_AVAILABLE = False

# Optional NLP libraries
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    SPACY_AVAILABLE = False

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    SentimentIntensityAnalyzer = None
    VADER_AVAILABLE = False


# =============================================================================
# LINGUISTIC MARKERS AND PATTERNS
# =============================================================================

# Evidence and factual markers (Logos)
EVIDENCE_MARKERS = {
    "statistics": [
        r'\d+(?:\.\d+)?%', r'\d+(?:\.\d+)?\s*(?:percent|percentage)',
        r'(?:one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:out\s+of|in)',
        r'(?:majority|minority|half|third|quarter)\s+of',
    ],
    "citations": [
        r'\(\d{4}\)', r'\([A-Z][a-z]+,?\s+\d{4}\)',
        r'(?:according\s+to|cited\s+by|reported\s+by)',
        r'(?:study|research|survey|report|analysis)\s+(?:shows?|finds?|suggests?)',
    ],
    "logical_connectors": [
        r'\b(?:therefore|thus|hence|consequently|as\s+a\s+result)\b',
        r'\b(?:because|since|due\s+to|owing\s+to|given\s+that)\b',
        r'\b(?:if.*then|provided\s+that|assuming\s+that)\b',
        r'\b(?:for\s+example|for\s+instance|such\s+as|namely)\b',
    ],
    "quantifiers": [
        r'\b(?:all|every|each|most|many|some|few|none)\b',
        r'\b(?:always|never|often|sometimes|rarely)\b',
        r'\b(?:significant|substantial|considerable|notable)\b',
    ],
}

# Emotional markers (Pathos)
EMOTIONAL_MARKERS = {
    "appeals": [
        r'\b(?:imagine|consider|think\s+about|picture)\b',
        r'\b(?:feel|felt|feeling|emotion|emotional)\b',
        r'\b(?:heart|soul|spirit|passion)\b',
    ],
    "urgency": [
        r'\b(?:must|need\s+to|have\s+to|urgent|critical|vital)\b',
        r'\b(?:now|immediately|right\s+now|today)\b',
        r'\b(?:before\s+it\'s\s+too\s+late|time\s+is\s+running\s+out)\b',
    ],
    "inclusive": [
        r'\b(?:we|us|our|together|united)\b',
        r'\b(?:everyone|everybody|all\s+of\s+us)\b',
    ],
    "intensifiers": [
        r'\b(?:very|extremely|incredibly|absolutely|truly)\b',
        r'\b(?:amazing|wonderful|terrible|horrible|devastating)\b',
        r'!+',
    ],
}

# Authority markers (Ethos)
AUTHORITY_MARKERS = {
    "credentials": [
        r'\b(?:Dr\.|Professor|PhD|MD|expert|specialist)\b',
        r'\b(?:years?\s+of\s+experience|veteran|renowned)\b',
        r'\b(?:award-winning|acclaimed|recognized)\b',
    ],
    "sources": [
        r'\b(?:Harvard|Stanford|MIT|Oxford|Cambridge)\b',
        r'\b(?:New\s+York\s+Times|Washington\s+Post|BBC|Reuters)\b',
        r'\b(?:scientific|peer-reviewed|published)\b',
    ],
    "trust_builders": [
        r'\b(?:honestly|frankly|truthfully|in\s+fact)\b',
        r'\b(?:proven|established|well-known|widely\s+accepted)\b',
        r'\b(?:trust|reliable|credible|authentic)\b',
    ],
    "hedging": [
        r'\b(?:perhaps|maybe|possibly|might|could)\b',
        r'\b(?:it\s+seems|appears\s+to|tends\s+to)\b',
        r'\b(?:in\s+my\s+opinion|I\s+believe|I\s+think)\b',
    ],
}

# Weak argument markers (Shatter Points)
WEAKNESS_MARKERS = {
    "unsupported": [
        r'\b(?:obviously|clearly|everyone\s+knows)\b',  # Assumes agreement
        r'\b(?:of\s+course|naturally|needless\s+to\s+say)\b',
    ],
    "vague": [
        r'\b(?:things?|stuff|somehow|something|somewhere)\b',
        r'\b(?:people\s+say|they\s+say|it\s+is\s+said)\b',
        r'\b(?:etc\.|and\s+so\s+on|and\s+so\s+forth)\b',
    ],
    "logical_fallacies": [
        r'\b(?:always|never)\b.*\b(?:always|never)\b',  # Absolute statements
        r'\b(?:if\s+we\s+allow|slippery\s+slope)\b',
        r'\b(?:either.*or|black\s+and\s+white)\b',  # False dichotomy
    ],
    "emotional_manipulation": [
        r'\b(?:real\s+(?:men|women|Americans))\b',
        r'\b(?:common\s+sense|any\s+(?:reasonable|rational)\s+person)\b',
    ],
}

# Transition markers for coherence analysis
TRANSITION_MARKERS = {
    "addition": [r'\b(?:also|furthermore|moreover|additionally|in\s+addition)\b'],
    "contrast": [r'\b(?:however|but|although|despite|nevertheless|on\s+the\s+other\s+hand)\b'],
    "cause_effect": [r'\b(?:therefore|thus|consequently|as\s+a\s+result|because)\b'],
    "sequence": [r'\b(?:first|second|third|then|next|finally|lastly)\b'],
    "example": [r'\b(?:for\s+example|for\s+instance|such\s+as|specifically)\b'],
    "conclusion": [r'\b(?:in\s+conclusion|to\s+summarize|overall|in\s+summary)\b'],
}


# =============================================================================
# HELPER CLASSES
# =============================================================================

@dataclass
class StepResult:
    """Result from a single evaluation step."""
    step_number: int
    step_name: str
    phase: str
    score: float  # 0-100
    findings: List[Dict[str, Any]] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    level_breakdown: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    llm_insights: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "step_name": self.step_name,
            "phase": self.phase,
            "score": self.score,
            "findings": self.findings,
            "metrics": self.metrics,
            "level_breakdown": self.level_breakdown,
            "recommendations": self.recommendations,
            "llm_insights": self.llm_insights,
        }


# =============================================================================
# EVALUATION ANALYSIS MODULE
# =============================================================================

@registry.register_analysis("evaluation")
class EvaluationAnalysis(BaseAnalysisModule):
    """
    9-Step Rhetorical Evaluation Analysis Module.

    Analyzes text across three phases:
    1. Evaluation (Critique, Logic, Logos, Pathos, Ethos)
    2. Risk (Blind Spots, Shatter Points)
    3. Growth (Bloom, Evolve)

    Each step operates at multiple atomization levels with aggregation.
    """

    name = "evaluation"
    description = "9-step rhetorical evaluation framework (Evaluation → Reinforcement → Risk → Growth)"

    # Step definitions with 4-phase flow
    # Note: Logic Check moved to Reinforcement phase (after initial evaluation)
    STEPS = {
        1: ("critique", "Evaluation", "Strengths and weaknesses assessment"),
        2: ("logic_check", "Reinforcement", "Internal consistency and argument flow"),
        3: ("logos", "Evaluation", "Rational appeal - evidence and reasoning"),
        4: ("pathos", "Evaluation", "Emotional resonance and engagement"),
        5: ("ethos", "Evaluation", "Credibility and authority markers"),
        6: ("blind_spots", "Risk", "Overlooked areas and assumptions"),
        7: ("shatter_points", "Risk", "Vulnerabilities and weak arguments"),
        8: ("bloom", "Growth", "Emergent insights and connections"),
        9: ("evolve", "Growth", "Synthesized improvement recommendations"),
    }

    # 4-phase execution order (Evaluation → Reinforcement → Risk → Growth)
    STEP_ORDER = [
        1,  # Critique - Evaluation
        3,  # Logos - Evaluation
        4,  # Pathos - Evaluation
        5,  # Ethos - Evaluation
        2,  # Logic Check - Reinforcement (validates findings from Evaluation)
        6,  # Blind Spots - Risk
        7,  # Shatter Points - Risk
        8,  # Bloom - Growth
        9,  # Evolve - Growth
    ]

    # All steps can now use LLM enhancement
    LLM_ENHANCED_STEPS = {1, 2, 3, 4, 5, 6, 7, 8, 9}

    # Phase groupings
    PHASE_STEPS = {
        "Evaluation": [1, 3, 4, 5],
        "Reinforcement": [2],
        "Risk": [6, 7],
        "Growth": [8, 9],
    }

    def __init__(self):
        super().__init__()
        self._llm_provider: Optional[LLMProvider] = None
        self._chain_executor: Optional["PromptChainExecutor"] = None
        self._parser: Optional["RhetoricalOutputParser"] = None
        self._vader = None
        self._nlp = None
        self._compiled_patterns: Dict[str, Dict[str, List[re.Pattern]]] = {}

        # Initialize VADER if available
        if VADER_AVAILABLE:
            self._vader = SentimentIntensityAnalyzer()

        # Initialize parser if available
        if CHAIN_AVAILABLE:
            self._parser = RhetoricalOutputParser()

        # Compile all regex patterns
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile all regex patterns for efficiency."""
        pattern_groups = {
            "evidence": EVIDENCE_MARKERS,
            "emotional": EMOTIONAL_MARKERS,
            "authority": AUTHORITY_MARKERS,
            "weakness": WEAKNESS_MARKERS,
            "transitions": TRANSITION_MARKERS,
        }

        for group_name, categories in pattern_groups.items():
            self._compiled_patterns[group_name] = {}
            for category, patterns in categories.items():
                self._compiled_patterns[group_name][category] = [
                    re.compile(p, re.IGNORECASE) for p in patterns
                ]

    def _setup_llm(self, config: Dict[str, Any]):
        """Initialize LLM provider and chain executor from config."""
        llm_config = config.get("llm")
        if llm_config and get_provider:
            self._llm_provider = get_provider(llm_config)
            if self._llm_provider:
                logger.info(f"LLM provider initialized: {self._llm_provider.name}")

                # Initialize chain executor if available
                chain_config = config.get("chain", {})
                if CHAIN_AVAILABLE and chain_config.get("enabled", True):
                    self._chain_executor = PromptChainExecutor(
                        provider=self._llm_provider,
                        prompts=prompt_library,
                        parser=self._parser,
                        max_retries=chain_config.get("max_retries", 2),
                    )
                    logger.info("Prompt chain executor initialized")

    def _get_llm_step_analysis(
        self,
        step_name: str,
        corpus: Corpus,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Get LLM-enhanced analysis for a step using the chain executor.

        Args:
            step_name: Name of the evaluation step
            corpus: The corpus being analyzed
            additional_context: Extra context variables

        Returns:
            Parsed LLM output or None if LLM not available
        """
        if not self._chain_executor:
            return None

        # Prepare text content for analysis
        sample_text = self._extract_sample_text(corpus, max_chars=3000)
        self._chain_executor.set_text(sample_text)

        try:
            step_result = self._chain_executor.execute_step(
                step_name,
                additional_context=additional_context,
            )

            if step_result.success:
                return step_result.parsed_output
            else:
                logger.warning(f"LLM step {step_name} failed: {step_result.error}")
                return None

        except Exception as e:
            logger.error(f"Error in LLM step {step_name}: {e}")
            return None

    def _extract_sample_text(self, corpus: Corpus, max_chars: int = 3000) -> str:
        """Extract sample text from corpus for LLM analysis."""
        sample_parts = []
        current_len = 0

        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            if current_len + len(theme.text) > max_chars:
                remaining = max_chars - current_len
                if remaining > 100:
                    sample_parts.append(theme.text[:remaining] + "...")
                break
            sample_parts.append(theme.text)
            current_len += len(theme.text) + 2

        return "\n\n".join(sample_parts)

    def _merge_llm_findings(
        self,
        heuristic_findings: List[Dict[str, Any]],
        llm_output: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Merge LLM findings with heuristic findings."""
        if not llm_output or not self._parser:
            return heuristic_findings

        llm_findings = self._parser.extract_findings(llm_output)

        # Combine, avoiding duplicates based on description
        seen_descriptions = {f.get("description", "")[:50] for f in heuristic_findings}
        merged = heuristic_findings.copy()

        for finding in llm_findings:
            desc = finding.get("description", "")[:50]
            if desc not in seen_descriptions:
                finding["source"] = "llm"
                merged.append(finding)
                seen_descriptions.add(desc)

        return merged

    def _merge_llm_recommendations(
        self,
        heuristic_recs: List[str],
        llm_output: Optional[Dict[str, Any]],
    ) -> List[str]:
        """Merge LLM recommendations with heuristic recommendations."""
        if not llm_output or not self._parser:
            return heuristic_recs

        llm_recs = self._parser.extract_recommendations(llm_output)

        # Combine, avoiding duplicates
        seen = set(r.lower()[:30] for r in heuristic_recs)
        merged = heuristic_recs.copy()

        for rec in llm_recs:
            if rec.lower()[:30] not in seen:
                merged.append(rec)
                seen.add(rec.lower()[:30])

        return merged

    # =========================================================================
    # PATTERN MATCHING UTILITIES
    # =========================================================================

    def _count_pattern_matches(
        self,
        text: str,
        group: str,
        category: Optional[str] = None,
    ) -> Dict[str, int]:
        """Count pattern matches in text."""
        if group not in self._compiled_patterns:
            return {}

        counts = {}
        categories = self._compiled_patterns[group]

        if category:
            categories = {category: categories.get(category, [])}

        for cat_name, patterns in categories.items():
            cat_count = 0
            for pattern in patterns:
                matches = pattern.findall(text)
                cat_count += len(matches)
            counts[cat_name] = cat_count

        return counts

    def _find_pattern_instances(
        self,
        text: str,
        group: str,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Find all pattern instances with positions."""
        if group not in self._compiled_patterns:
            return []

        instances = []
        categories = self._compiled_patterns[group]

        if category:
            categories = {category: categories.get(category, [])}

        for cat_name, patterns in categories.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    instances.append({
                        "category": cat_name,
                        "text": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                    })

        return instances

    # =========================================================================
    # LEVEL AGGREGATION
    # =========================================================================

    def _analyze_at_level(
        self,
        corpus: Corpus,
        level: AtomLevel,
        analyzer_func,
    ) -> Dict[str, Any]:
        """Run analysis function at a specific level and aggregate."""
        results = []

        for doc, atom in self.iter_atoms(corpus, level):
            result = analyzer_func(atom.text, atom)
            result["atom_id"] = atom.id
            results.append(result)

        return {
            "level": level.value,
            "count": len(results),
            "items": results,
        }

    def _aggregate_scores(
        self,
        level_results: Dict[str, Dict[str, Any]],
    ) -> float:
        """Aggregate scores from multiple levels (weighted by level depth)."""
        weights = {
            "letter": 0.05,
            "word": 0.15,
            "sentence": 0.35,
            "paragraph": 0.30,
            "theme": 0.15,
        }

        total_weight = 0
        weighted_sum = 0

        for level_name, result in level_results.items():
            if "score" in result:
                weight = weights.get(level_name, 0.1)
                weighted_sum += result["score"] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 50.0

    # =========================================================================
    # STEP 1: CRITIQUE
    # =========================================================================

    def _step_critique(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Assess overall strengths and weaknesses."""
        findings = []
        level_breakdown = {}

        # Sentence-level analysis
        sentence_metrics = {"quality_scores": [], "lengths": [], "complexity": []}

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            text = sentence.text
            words = text.split()
            word_count = len(words)

            # Sentence quality heuristics
            quality = 50.0  # Base score

            # Length appropriateness (ideal: 15-25 words)
            if 15 <= word_count <= 25:
                quality += 10
            elif word_count < 8:
                quality -= 10
            elif word_count > 40:
                quality -= 15

            # Has proper structure (starts with capital, ends with punctuation)
            if text and text[0].isupper():
                quality += 5
            if text and text[-1] in ".!?":
                quality += 5

            # Transition usage
            transitions = self._count_pattern_matches(text, "transitions")
            if sum(transitions.values()) > 0:
                quality += 10

            # Evidence markers
            evidence = self._count_pattern_matches(text, "evidence")
            if sum(evidence.values()) > 0:
                quality += 10

            sentence_metrics["quality_scores"].append(quality)
            sentence_metrics["lengths"].append(word_count)

        # Calculate statistics
        if sentence_metrics["quality_scores"]:
            avg_quality = mean(sentence_metrics["quality_scores"])
            quality_std = stdev(sentence_metrics["quality_scores"]) if len(sentence_metrics["quality_scores"]) > 1 else 0
            avg_length = mean(sentence_metrics["lengths"])
        else:
            avg_quality = 50.0
            quality_std = 0
            avg_length = 0

        level_breakdown["sentence"] = {
            "score": avg_quality,
            "avg_length": avg_length,
            "quality_variation": quality_std,
            "count": len(sentence_metrics["quality_scores"]),
        }

        # Theme-level coherence
        theme_scores = []
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            # Check for clear structure
            paragraphs = [c for c in theme.children if c.level == AtomLevel.PARAGRAPH]
            theme_score = 50.0

            if len(paragraphs) >= 2:
                theme_score += 15
            if theme.metadata.get("title"):
                theme_score += 10

            theme_scores.append(theme_score)

        if theme_scores:
            level_breakdown["theme"] = {
                "score": mean(theme_scores),
                "count": len(theme_scores),
            }

        # Identify strengths and weaknesses
        if avg_quality >= 70:
            findings.append({
                "type": "strength",
                "category": "sentence_quality",
                "description": "Strong sentence construction with good variety and structure",
                "score_impact": "+15",
            })
        elif avg_quality < 50:
            findings.append({
                "type": "weakness",
                "category": "sentence_quality",
                "description": "Sentence quality could be improved with better structure and transitions",
                "score_impact": "-10",
            })

        # Calculate overall score
        overall_score = self._aggregate_scores(level_breakdown)

        # Get LLM insights if available
        llm_insights = None
        if self._llm_provider and 1 in self.LLM_ENHANCED_STEPS:
            llm_insights = self._get_llm_critique(corpus)

        recommendations = []
        if avg_length < 12:
            recommendations.append("Consider expanding sentences with more detail and evidence")
        if avg_length > 30:
            recommendations.append("Some sentences may benefit from being split for clarity")
        if quality_std > 20:
            recommendations.append("Work on maintaining consistent sentence quality throughout")

        return StepResult(
            step_number=1,
            step_name="critique",
            phase="Evaluation",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "avg_sentence_quality": avg_quality,
                "avg_sentence_length": avg_length,
                "quality_consistency": 100 - quality_std,
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    def _get_llm_critique(self, corpus: Corpus) -> Optional[str]:
        """Get LLM-powered critique analysis."""
        if not self._llm_provider:
            return None

        # Sample text for analysis (first 2000 chars)
        sample_text = ""
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            sample_text += theme.text[:1000] + "\n\n"
            if len(sample_text) > 2000:
                break

        prompt = f"""Analyze the following text for rhetorical strengths and weaknesses.
Focus on:
1. Clarity and coherence
2. Argument structure
3. Evidence quality
4. Writing style

Provide 3-5 key observations with specific examples.

TEXT:
{sample_text[:2000]}

ANALYSIS:"""

        response = self._llm_provider.complete(
            prompt=prompt,
            system_prompt="You are a rhetorical analysis expert. Be concise and specific.",
        )

        return response.text if response.success else None

    # =========================================================================
    # STEP 2: LOGIC CHECK
    # =========================================================================

    def _step_logic_check(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Check internal consistency and argument flow."""
        findings = []
        level_breakdown = {}

        # Analyze argument flow via transitions
        transition_counts = defaultdict(int)
        sentences_with_transitions = 0
        total_sentences = 0

        argument_chains = []
        current_chain = []

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            total_sentences += 1
            text = sentence.text

            transitions = self._count_pattern_matches(text, "transitions")
            transition_total = sum(transitions.values())

            if transition_total > 0:
                sentences_with_transitions += 1
                for cat, count in transitions.items():
                    transition_counts[cat] += count

                # Track argument chains
                if transitions.get("cause_effect", 0) > 0:
                    current_chain.append(sentence.id)
                elif current_chain:
                    if len(current_chain) >= 2:
                        argument_chains.append(current_chain.copy())
                    current_chain = []

        # Capture final chain
        if len(current_chain) >= 2:
            argument_chains.append(current_chain)

        # Calculate metrics
        transition_density = sentences_with_transitions / total_sentences if total_sentences > 0 else 0
        transition_variety = len([c for c in transition_counts.values() if c > 0])

        # Score based on logical structure
        logic_score = 50.0

        if transition_density > 0.3:
            logic_score += 20
        elif transition_density > 0.15:
            logic_score += 10

        if transition_variety >= 4:
            logic_score += 15
        elif transition_variety >= 2:
            logic_score += 5

        if len(argument_chains) >= 2:
            logic_score += 15

        level_breakdown["sentence"] = {
            "score": logic_score,
            "transition_density": transition_density,
            "transition_variety": transition_variety,
            "argument_chains": len(argument_chains),
        }

        # Paragraph-level coherence
        para_scores = []
        for _, para in self.iter_atoms(corpus, AtomLevel.PARAGRAPH):
            sentences = [c for c in para.children if c.level == AtomLevel.SENTENCE]
            if len(sentences) < 2:
                continue

            # Check if sentences flow logically
            para_score = 50.0
            for i, sent in enumerate(sentences[1:], 1):
                prev_text = sentences[i-1].text.lower()
                curr_text = sent.text.lower()

                # Check for pronoun references (basic coherence)
                if any(p in curr_text[:50] for p in ["this", "that", "these", "those", "it", "they"]):
                    para_score += 5

                # Check for transition words
                transitions = self._count_pattern_matches(sent.text, "transitions")
                if sum(transitions.values()) > 0:
                    para_score += 5

            para_scores.append(min(100, para_score))

        if para_scores:
            level_breakdown["paragraph"] = {
                "score": mean(para_scores),
                "count": len(para_scores),
            }

        # Identify issues
        if transition_density < 0.1:
            findings.append({
                "type": "weakness",
                "category": "flow",
                "description": "Low use of transition words reduces logical flow between ideas",
                "score_impact": "-15",
            })
        else:
            findings.append({
                "type": "strength",
                "category": "flow",
                "description": f"Good use of transitions ({transition_variety} types used)",
                "score_impact": "+10",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if transition_density < 0.15:
            recommendations.append("Add more transition words to connect ideas (therefore, however, furthermore)")
        if transition_counts.get("cause_effect", 0) < 2:
            recommendations.append("Strengthen cause-effect relationships with explicit connectors")
        if transition_counts.get("example", 0) < 2:
            recommendations.append("Include more examples to support abstract claims")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 2 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("logic_check", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                llm_insights = llm_output.get("_raw") or str(llm_output.get("coherence_assessment", ""))

        return StepResult(
            step_number=2,
            step_name="logic_check",
            phase="Reinforcement",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "transition_density": transition_density * 100,
                "transition_types_used": transition_variety,
                "argument_chains_found": len(argument_chains),
                "transition_breakdown": dict(transition_counts),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 3: LOGOS REVIEW
    # =========================================================================

    def _step_logos(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Analyze rational appeal - evidence and reasoning."""
        findings = []
        level_breakdown = {}

        evidence_counts = defaultdict(int)
        sentences_with_evidence = 0
        total_sentences = 0
        evidence_instances = []

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            total_sentences += 1
            text = sentence.text

            evidence = self._count_pattern_matches(text, "evidence")
            evidence_total = sum(evidence.values())

            if evidence_total > 0:
                sentences_with_evidence += 1
                for cat, count in evidence.items():
                    evidence_counts[cat] += count

                # Track specific instances
                for instance in self._find_pattern_instances(text, "evidence"):
                    evidence_instances.append({
                        "sentence_id": sentence.id,
                        **instance,
                    })

        # Calculate metrics
        evidence_density = sentences_with_evidence / total_sentences if total_sentences > 0 else 0
        evidence_variety = len([c for c in evidence_counts.values() if c > 0])

        # Score
        logos_score = 40.0

        if evidence_density > 0.2:
            logos_score += 25
        elif evidence_density > 0.1:
            logos_score += 15

        if evidence_counts.get("statistics", 0) > 0:
            logos_score += 10
        if evidence_counts.get("citations", 0) > 0:
            logos_score += 15
        if evidence_counts.get("logical_connectors", 0) >= 3:
            logos_score += 10

        level_breakdown["sentence"] = {
            "score": logos_score,
            "evidence_density": evidence_density,
            "evidence_variety": evidence_variety,
            "total_evidence_markers": sum(evidence_counts.values()),
        }

        # Findings
        if evidence_counts.get("citations", 0) > 0:
            findings.append({
                "type": "strength",
                "category": "citations",
                "description": f"Text includes {evidence_counts['citations']} citation references",
                "score_impact": "+15",
            })

        if evidence_counts.get("statistics", 0) > 0:
            findings.append({
                "type": "strength",
                "category": "statistics",
                "description": f"Uses {evidence_counts['statistics']} statistical references",
                "score_impact": "+10",
            })

        if evidence_density < 0.05:
            findings.append({
                "type": "weakness",
                "category": "evidence",
                "description": "Very low evidence density - claims may appear unsupported",
                "score_impact": "-20",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if evidence_counts.get("citations", 0) == 0:
            recommendations.append("Add source citations to strengthen credibility")
        if evidence_counts.get("statistics", 0) == 0:
            recommendations.append("Include statistical data to support key claims")
        if evidence_density < 0.1:
            recommendations.append("Increase use of specific examples and evidence")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 3 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("logos", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                llm_insights = llm_output.get("_raw") or str(llm_output.get("logical_structure", ""))

        return StepResult(
            step_number=3,
            step_name="logos",
            phase="Evaluation",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "evidence_density_percent": evidence_density * 100,
                "evidence_types_used": evidence_variety,
                "statistics_count": evidence_counts.get("statistics", 0),
                "citations_count": evidence_counts.get("citations", 0),
                "logical_connectors_count": evidence_counts.get("logical_connectors", 0),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 4: PATHOS REVIEW
    # =========================================================================

    def _step_pathos(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Analyze emotional resonance and engagement."""
        findings = []
        level_breakdown = {}

        emotional_counts = defaultdict(int)
        sentiment_scores = []
        engagement_markers = 0
        total_sentences = 0

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            total_sentences += 1
            text = sentence.text

            # Emotional markers
            emotional = self._count_pattern_matches(text, "emotional")
            emotional_total = sum(emotional.values())
            engagement_markers += emotional_total

            for cat, count in emotional.items():
                emotional_counts[cat] += count

            # Sentiment analysis
            if self._vader:
                scores = self._vader.polarity_scores(text)
                sentiment_scores.append(scores["compound"])

        # Calculate metrics
        emotional_density = engagement_markers / total_sentences if total_sentences > 0 else 0

        if sentiment_scores:
            sentiment_mean = mean(sentiment_scores)
            sentiment_variation = stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0
        else:
            sentiment_mean = 0
            sentiment_variation = 0

        # Score - balance is important for pathos
        pathos_score = 50.0

        # Some emotional engagement is good
        if 0.1 <= emotional_density <= 0.4:
            pathos_score += 20
        elif emotional_density > 0.4:
            pathos_score += 5  # Too much can be overwhelming
        elif emotional_density > 0:
            pathos_score += 10

        # Sentiment variation shows emotional arc
        if 0.2 <= sentiment_variation <= 0.5:
            pathos_score += 15
        elif sentiment_variation > 0.1:
            pathos_score += 5

        # Inclusive language builds connection
        if emotional_counts.get("inclusive", 0) > 0:
            pathos_score += 10

        level_breakdown["sentence"] = {
            "score": pathos_score,
            "emotional_density": emotional_density,
            "sentiment_mean": sentiment_mean,
            "sentiment_variation": sentiment_variation,
        }

        # Findings
        if emotional_counts.get("inclusive", 0) > 2:
            findings.append({
                "type": "strength",
                "category": "connection",
                "description": "Good use of inclusive language to connect with audience",
                "score_impact": "+10",
            })

        if emotional_counts.get("urgency", 0) > 3:
            findings.append({
                "type": "observation",
                "category": "urgency",
                "description": f"High urgency language ({emotional_counts['urgency']} instances) may feel pressuring",
                "score_impact": "0",
            })

        if emotional_density < 0.05:
            findings.append({
                "type": "weakness",
                "category": "engagement",
                "description": "Very low emotional engagement - may feel dry or disconnected",
                "score_impact": "-10",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if emotional_density < 0.1:
            recommendations.append("Consider adding more engaging language to connect with readers")
        if emotional_counts.get("inclusive", 0) == 0:
            recommendations.append("Use inclusive language (we, us, together) to build reader connection")
        if sentiment_variation < 0.1:
            recommendations.append("Vary emotional tone to create a more engaging narrative arc")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 4 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("pathos", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                llm_insights = llm_output.get("_raw") or str(llm_output.get("emotional_tone", ""))

        return StepResult(
            step_number=4,
            step_name="pathos",
            phase="Evaluation",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "emotional_density_percent": emotional_density * 100,
                "sentiment_mean": sentiment_mean,
                "sentiment_variation": sentiment_variation,
                "appeals_count": emotional_counts.get("appeals", 0),
                "inclusive_count": emotional_counts.get("inclusive", 0),
                "urgency_count": emotional_counts.get("urgency", 0),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 5: ETHOS REVIEW
    # =========================================================================

    def _step_ethos(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Analyze credibility and authority markers."""
        findings = []
        level_breakdown = {}

        authority_counts = defaultdict(int)
        total_sentences = 0

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            total_sentences += 1
            text = sentence.text

            authority = self._count_pattern_matches(text, "authority")
            for cat, count in authority.items():
                authority_counts[cat] += count

        # Calculate metrics
        authority_total = sum(authority_counts.values())
        authority_density = authority_total / total_sentences if total_sentences > 0 else 0

        # Score
        ethos_score = 50.0

        if authority_counts.get("credentials", 0) > 0:
            ethos_score += 15
        if authority_counts.get("sources", 0) > 0:
            ethos_score += 15
        if authority_counts.get("trust_builders", 0) > 0:
            ethos_score += 10

        # Hedging can be good (shows intellectual honesty) or bad (shows uncertainty)
        hedging = authority_counts.get("hedging", 0)
        if 1 <= hedging <= 5:
            ethos_score += 5  # Some hedging is honest
        elif hedging > 10:
            ethos_score -= 10  # Too much hedging undermines authority

        level_breakdown["sentence"] = {
            "score": ethos_score,
            "authority_density": authority_density,
            "authority_total": authority_total,
        }

        # Findings
        if authority_counts.get("sources", 0) > 0:
            findings.append({
                "type": "strength",
                "category": "sources",
                "description": "References reputable sources to establish credibility",
                "score_impact": "+15",
            })

        if authority_counts.get("credentials", 0) > 0:
            findings.append({
                "type": "strength",
                "category": "credentials",
                "description": "Includes expert credentials or qualifications",
                "score_impact": "+15",
            })

        if hedging > 10:
            findings.append({
                "type": "weakness",
                "category": "hedging",
                "description": f"Excessive hedging ({hedging} instances) may undermine authority",
                "score_impact": "-10",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if authority_counts.get("sources", 0) == 0:
            recommendations.append("Reference reputable sources to strengthen credibility")
        if authority_counts.get("credentials", 0) == 0:
            recommendations.append("Establish expertise through credentials or experience")
        if authority_counts.get("trust_builders", 0) == 0:
            recommendations.append("Add trust-building language to connect with audience")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 5 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("ethos", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                llm_insights = llm_output.get("_raw") or str(llm_output.get("credibility_markers", ""))

        return StepResult(
            step_number=5,
            step_name="ethos",
            phase="Evaluation",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "authority_density_percent": authority_density * 100,
                "credentials_count": authority_counts.get("credentials", 0),
                "sources_count": authority_counts.get("sources", 0),
                "trust_builders_count": authority_counts.get("trust_builders", 0),
                "hedging_count": hedging,
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 6: BLIND SPOTS
    # =========================================================================

    def _step_blind_spots(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Identify overlooked areas and assumptions."""
        findings = []
        level_breakdown = {}

        # Collect all unique topics/concepts (simple word frequency analysis)
        word_freq = Counter()
        theme_topics = defaultdict(set)

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            words = sentence.text.lower().split()
            # Filter to meaningful words (length > 4, not common)
            meaningful = [w.strip(".,!?;:\"'") for w in words if len(w) > 4]
            word_freq.update(meaningful)

            if sentence.theme_id:
                theme_topics[sentence.theme_id].update(meaningful[:5])

        # Find potential blind spots
        potential_gaps = []

        # Check for assumption markers
        assumption_patterns = [
            r'\b(?:obviously|clearly|of\s+course|everyone\s+knows)\b',
            r'\b(?:naturally|needless\s+to\s+say|it\s+goes\s+without\s+saying)\b',
        ]

        assumption_count = 0
        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            for pattern in assumption_patterns:
                if re.search(pattern, sentence.text, re.IGNORECASE):
                    assumption_count += 1
                    potential_gaps.append({
                        "type": "assumption",
                        "sentence_id": sentence.id,
                        "text": sentence.text[:100],
                    })

        # Check for counterargument consideration
        counterargument_patterns = [
            r'\b(?:critics|opponents|some\s+argue|on\s+the\s+other\s+hand)\b',
            r'\b(?:however|although|despite|nevertheless)\b',
            r'\b(?:counterargument|objection|concern)\b',
        ]

        counterarguments_addressed = 0
        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            for pattern in counterargument_patterns:
                if re.search(pattern, sentence.text, re.IGNORECASE):
                    counterarguments_addressed += 1
                    break

        # Score based on awareness
        blind_spots_score = 70.0  # Start high, subtract for issues

        if assumption_count > 5:
            blind_spots_score -= 20
        elif assumption_count > 2:
            blind_spots_score -= 10

        if counterarguments_addressed == 0:
            blind_spots_score -= 15
        elif counterarguments_addressed < 2:
            blind_spots_score -= 5

        level_breakdown["document"] = {
            "score": blind_spots_score,
            "assumptions_detected": assumption_count,
            "counterarguments_addressed": counterarguments_addressed,
        }

        # Findings
        if assumption_count > 0:
            findings.append({
                "type": "blind_spot",
                "category": "assumptions",
                "description": f"Found {assumption_count} potential unstated assumptions",
                "examples": [g["text"][:80] for g in potential_gaps[:3]],
                "score_impact": f"-{min(20, assumption_count * 5)}",
            })

        if counterarguments_addressed == 0:
            findings.append({
                "type": "blind_spot",
                "category": "counterarguments",
                "description": "No counterarguments or opposing views addressed",
                "score_impact": "-15",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if assumption_count > 0:
            recommendations.append("Review and explicitly state or support assumed premises")
        if counterarguments_addressed == 0:
            recommendations.append("Address potential counterarguments to strengthen the argument")
        recommendations.append("Consider perspectives from different stakeholders")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 6 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("blind_spots", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                # Extract meaningful insight summary
                hidden = llm_output.get("hidden_assumptions", [])
                if hidden:
                    llm_insights = f"Found {len(hidden)} hidden assumptions. "
                    if isinstance(hidden[0], dict):
                        llm_insights += hidden[0].get("assumption", "")

        return StepResult(
            step_number=6,
            step_name="blind_spots",
            phase="Risk",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "assumptions_detected": assumption_count,
                "counterarguments_addressed": counterarguments_addressed,
                "unique_concepts_count": len(word_freq),
                "themes_analyzed": len(theme_topics),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 7: SHATTER POINTS
    # =========================================================================

    def _step_shatter_points(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Identify vulnerabilities and weak arguments."""
        findings = []
        level_breakdown = {}

        weakness_counts = defaultdict(int)
        vulnerable_sentences = []

        for _, sentence in self.iter_atoms(corpus, AtomLevel.SENTENCE):
            text = sentence.text

            weaknesses = self._count_pattern_matches(text, "weakness")
            weakness_total = sum(weaknesses.values())

            if weakness_total > 0:
                for cat, count in weaknesses.items():
                    weakness_counts[cat] += count

                vulnerable_sentences.append({
                    "sentence_id": sentence.id,
                    "text": text[:100],
                    "weakness_types": [k for k, v in weaknesses.items() if v > 0],
                })

        # Score - lower weaknesses = higher score
        vulnerability_score = 100.0
        total_weaknesses = sum(weakness_counts.values())

        if total_weaknesses > 10:
            vulnerability_score -= 40
        elif total_weaknesses > 5:
            vulnerability_score -= 25
        elif total_weaknesses > 0:
            vulnerability_score -= 10

        # Specific penalties
        if weakness_counts.get("logical_fallacies", 0) > 0:
            vulnerability_score -= 15
        if weakness_counts.get("unsupported", 0) > 3:
            vulnerability_score -= 10

        level_breakdown["sentence"] = {
            "score": vulnerability_score,
            "total_weaknesses": total_weaknesses,
            "vulnerable_sentence_count": len(vulnerable_sentences),
        }

        # Findings
        if weakness_counts.get("unsupported", 0) > 0:
            findings.append({
                "type": "shatter_point",
                "category": "unsupported_claims",
                "description": f"Found {weakness_counts['unsupported']} instances of assumed agreement without evidence",
                "severity": "medium",
                "score_impact": "-10",
            })

        if weakness_counts.get("vague", 0) > 2:
            findings.append({
                "type": "shatter_point",
                "category": "vagueness",
                "description": f"Found {weakness_counts['vague']} vague or imprecise references",
                "severity": "low",
                "score_impact": "-5",
            })

        if weakness_counts.get("logical_fallacies", 0) > 0:
            findings.append({
                "type": "shatter_point",
                "category": "logical_fallacy",
                "description": f"Potential logical fallacies detected ({weakness_counts['logical_fallacies']} instances)",
                "severity": "high",
                "score_impact": "-15",
            })

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if weakness_counts.get("unsupported", 0) > 0:
            recommendations.append("Replace assumed agreements with explicit evidence")
        if weakness_counts.get("vague", 0) > 0:
            recommendations.append("Replace vague terms with specific details")
        if weakness_counts.get("logical_fallacies", 0) > 0:
            recommendations.append("Review and correct potential logical fallacies")

        # Get LLM insights if available
        llm_output = None
        llm_insights = None
        if self._llm_provider and 7 in self.LLM_ENHANCED_STEPS:
            llm_output = self._get_llm_step_analysis("shatter_points", corpus)
            if llm_output:
                findings = self._merge_llm_findings(findings, llm_output)
                recommendations = self._merge_llm_recommendations(recommendations, llm_output)
                # Extract vulnerability summary
                vulns = llm_output.get("critical_vulnerabilities", [])
                resilience = llm_output.get("overall_resilience", {})
                if vulns:
                    llm_insights = f"Identified {len(vulns)} critical vulnerabilities. "
                if isinstance(resilience, dict):
                    llm_insights = (llm_insights or "") + resilience.get("assessment", "")

        return StepResult(
            step_number=7,
            step_name="shatter_points",
            phase="Risk",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "total_vulnerabilities": total_weaknesses,
                "unsupported_claims": weakness_counts.get("unsupported", 0),
                "vague_references": weakness_counts.get("vague", 0),
                "potential_fallacies": weakness_counts.get("logical_fallacies", 0),
                "vulnerable_sentences": len(vulnerable_sentences),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    # =========================================================================
    # STEP 8: BLOOM
    # =========================================================================

    def _step_bloom(self, corpus: Corpus, domain: Optional[DomainProfile]) -> StepResult:
        """Identify emergent insights and expansion opportunities."""
        findings = []
        level_breakdown = {}

        # Find theme connections via shared vocabulary
        theme_words = defaultdict(set)
        for _, theme in self.iter_atoms(corpus, AtomLevel.THEME):
            words = set(theme.text.lower().split())
            # Filter to meaningful words
            meaningful = {w.strip(".,!?;:\"'") for w in words if len(w) > 4}
            theme_words[theme.id] = meaningful

        # Find cross-theme connections
        theme_connections = []
        theme_ids = list(theme_words.keys())
        for i, tid1 in enumerate(theme_ids):
            for tid2 in theme_ids[i+1:]:
                shared = theme_words[tid1] & theme_words[tid2]
                if len(shared) >= 3:
                    theme_connections.append({
                        "theme_1": tid1,
                        "theme_2": tid2,
                        "shared_concepts": list(shared)[:5],
                        "connection_strength": len(shared),
                    })

        # Identify recurring concepts (potential expansion points)
        all_words = []
        for words in theme_words.values():
            all_words.extend(words)

        word_freq = Counter(all_words)
        recurring_concepts = [
            {"concept": word, "frequency": count}
            for word, count in word_freq.most_common(10)
            if count >= 2
        ]

        # Score based on insight potential
        bloom_score = 50.0

        if len(theme_connections) >= 3:
            bloom_score += 25
        elif len(theme_connections) >= 1:
            bloom_score += 15

        if len(recurring_concepts) >= 5:
            bloom_score += 15
        elif len(recurring_concepts) >= 2:
            bloom_score += 10

        level_breakdown["theme"] = {
            "score": bloom_score,
            "connections_found": len(theme_connections),
            "recurring_concepts": len(recurring_concepts),
        }

        # Findings
        if theme_connections:
            findings.append({
                "type": "insight",
                "category": "theme_connections",
                "description": f"Found {len(theme_connections)} meaningful connections between themes",
                "examples": [f"{c['theme_1']} ↔ {c['theme_2']}" for c in theme_connections[:3]],
                "score_impact": "+15",
            })

        if recurring_concepts:
            findings.append({
                "type": "insight",
                "category": "recurring_concepts",
                "description": "Key concepts that could be developed further",
                "examples": [c["concept"] for c in recurring_concepts[:5]],
                "score_impact": "+10",
            })

        # Get LLM insights if available
        llm_insights = None
        if self._llm_provider and 8 in self.LLM_ENHANCED_STEPS:
            # Set theme data on chain executor if available
            if self._chain_executor:
                self._chain_executor.set_theme_data(
                    connections=theme_connections,
                    concepts=recurring_concepts,
                )
            llm_insights = self._get_llm_bloom_insights(corpus, theme_connections, recurring_concepts)

        overall_score = self._aggregate_scores(level_breakdown)

        recommendations = []
        if theme_connections:
            recommendations.append(f"Explore connection between themes: {theme_connections[0]['theme_1']} and {theme_connections[0]['theme_2']}")
        if recurring_concepts:
            top_concept = recurring_concepts[0]["concept"]
            recommendations.append(f"Consider developing the concept of '{top_concept}' more deeply")
        recommendations.append("Look for unexpected parallels between different sections")

        return StepResult(
            step_number=8,
            step_name="bloom",
            phase="Growth",
            score=min(100, max(0, overall_score)),
            findings=findings,
            metrics={
                "theme_connections": len(theme_connections),
                "recurring_concepts": len(recurring_concepts),
                "total_themes": len(theme_ids),
            },
            level_breakdown=level_breakdown,
            recommendations=recommendations,
            llm_insights=llm_insights,
        )

    def _get_llm_bloom_insights(
        self,
        corpus: Corpus,
        connections: List[Dict],
        concepts: List[Dict],
    ) -> Optional[str]:
        """Get LLM-powered insight generation."""
        if not self._llm_provider:
            return None

        concepts_str = ", ".join(c["concept"] for c in concepts[:5])
        connections_str = "\n".join(
            f"- {c['theme_1']} and {c['theme_2']} share: {', '.join(c['shared_concepts'][:3])}"
            for c in connections[:3]
        )

        prompt = f"""Based on this analysis of a text:

RECURRING CONCEPTS: {concepts_str}

THEME CONNECTIONS:
{connections_str}

Generate 3-5 creative insights about:
1. Hidden patterns or themes
2. Unexplored connections
3. Opportunities for expansion or development

Be specific and actionable.

INSIGHTS:"""

        response = self._llm_provider.complete(
            prompt=prompt,
            system_prompt="You are a creative analyst finding novel insights in text structure.",
        )

        return response.text if response.success else None

    # =========================================================================
    # STEP 9: EVOLVE
    # =========================================================================

    def _step_evolve(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile],
        previous_results: Dict[str, StepResult],
    ) -> StepResult:
        """Synthesize improvement recommendations."""
        findings = []
        level_breakdown = {}

        # Aggregate all recommendations from previous steps
        all_recommendations = []
        for step_num in range(1, 9):
            step_name, _, _ = self.STEPS[step_num]
            if step_name in previous_results:
                for rec in previous_results[step_name].recommendations:
                    all_recommendations.append({
                        "source_step": step_name,
                        "recommendation": rec,
                        "priority": self._calculate_priority(
                            previous_results[step_name].score,
                            step_name,
                        ),
                    })

        # Sort by priority
        all_recommendations.sort(key=lambda x: x["priority"], reverse=True)

        # Identify quick wins (high impact, likely easy)
        quick_wins = [
            r for r in all_recommendations
            if "add" in r["recommendation"].lower() or "include" in r["recommendation"].lower()
        ][:3]

        # Identify structural improvements
        structural = [
            r for r in all_recommendations
            if "structure" in r["recommendation"].lower()
            or "flow" in r["recommendation"].lower()
            or "transition" in r["recommendation"].lower()
        ][:3]

        # Calculate overall improvement potential
        scores = [
            previous_results[name].score
            for name, _ in [(self.STEPS[i][0], i) for i in range(1, 9)]
            if name in previous_results
        ]

        if scores:
            avg_score = mean(scores)
            improvement_potential = 100 - avg_score
        else:
            avg_score = 50
            improvement_potential = 50

        # Score based on actionability of recommendations
        evolve_score = 50.0 + (len(quick_wins) * 10) + (len(structural) * 5)
        evolve_score = min(100, evolve_score)

        level_breakdown["synthesis"] = {
            "score": evolve_score,
            "total_recommendations": len(all_recommendations),
            "quick_wins": len(quick_wins),
            "structural_improvements": len(structural),
        }

        # Findings
        findings.append({
            "type": "summary",
            "category": "improvement_potential",
            "description": f"Overall improvement potential: {improvement_potential:.0f}%",
            "current_avg_score": avg_score,
        })

        if quick_wins:
            findings.append({
                "type": "quick_wins",
                "category": "easy_improvements",
                "description": "High-impact improvements that can be made quickly",
                "items": [q["recommendation"] for q in quick_wins],
            })

        if structural:
            findings.append({
                "type": "structural",
                "category": "deeper_improvements",
                "description": "Structural improvements for long-term quality",
                "items": [s["recommendation"] for s in structural],
            })

        # Get LLM synthesis if available
        llm_insights = None
        if self._llm_provider and 9 in self.LLM_ENHANCED_STEPS:
            llm_insights = self._get_llm_evolution_synthesis(previous_results, all_recommendations)

        # Top prioritized recommendations
        top_recommendations = [r["recommendation"] for r in all_recommendations[:5]]

        return StepResult(
            step_number=9,
            step_name="evolve",
            phase="Growth",
            score=evolve_score,
            findings=findings,
            metrics={
                "current_avg_score": avg_score,
                "improvement_potential": improvement_potential,
                "total_recommendations": len(all_recommendations),
                "quick_wins_count": len(quick_wins),
                "structural_count": len(structural),
            },
            level_breakdown=level_breakdown,
            recommendations=top_recommendations,
            llm_insights=llm_insights,
        )

    def _calculate_priority(self, step_score: float, step_name: str) -> float:
        """Calculate priority for a recommendation based on step score and importance."""
        # Lower scores = higher priority for improvement
        base_priority = 100 - step_score

        # Weight by step importance
        importance_weights = {
            "critique": 1.2,
            "logic_check": 1.3,
            "logos": 1.1,
            "pathos": 0.9,
            "ethos": 1.0,
            "blind_spots": 1.2,
            "shatter_points": 1.4,
            "bloom": 0.8,
        }

        return base_priority * importance_weights.get(step_name, 1.0)

    def _get_llm_evolution_synthesis(
        self,
        results: Dict[str, StepResult],
        recommendations: List[Dict],
    ) -> Optional[str]:
        """Get LLM-powered improvement synthesis."""
        if not self._llm_provider:
            return None

        # Build summary of scores
        scores_summary = "\n".join(
            f"- {name}: {results[name].score:.0f}/100"
            for name in ["critique", "logic_check", "logos", "pathos", "ethos", "blind_spots", "shatter_points"]
            if name in results
        )

        top_recs = "\n".join(f"- {r['recommendation']}" for r in recommendations[:7])

        prompt = f"""Based on this rhetorical analysis:

SCORES:
{scores_summary}

TOP RECOMMENDATIONS:
{top_recs}

Synthesize a strategic improvement plan that:
1. Identifies the most critical areas to address first
2. Suggests a logical sequence of improvements
3. Explains how improvements connect and reinforce each other

Be specific and actionable. Limit to 4-5 strategic recommendations.

IMPROVEMENT PLAN:"""

        response = self._llm_provider.complete(
            prompt=prompt,
            system_prompt="You are a strategic writing coach synthesizing feedback into an actionable plan.",
        )

        return response.text if response.success else None

    # =========================================================================
    # MAIN ANALYZE METHOD
    # =========================================================================

    def analyze(
        self,
        corpus: Corpus,
        domain: Optional[DomainProfile] = None,
        config: Optional[Dict[str, Any]] = None,
    ) -> AnalysisOutput:
        """
        Run 9-step evaluation analysis with 4-phase flow.

        Phases: Evaluation → Reinforcement → Risk → Growth

        Config options:
            steps (list): Which steps to run (default: all in STEP_ORDER)
            levels (list): Which levels to analyze (default: all)
            llm (dict): LLM provider configuration
            chain (dict): Chain executor configuration
                - enabled (bool): Enable chain execution (default: True)
                - show_reasoning (bool): Include prompt/response pairs
                - max_retries (int): Retry count for parsing failures
        """
        self._config = config or {}

        # Setup LLM and chain executor if configured
        self._setup_llm(self._config)

        # Initialize chain executor with corpus text if available
        if self._chain_executor:
            sample_text = self._extract_sample_text(corpus)
            self._chain_executor.set_text(sample_text)

        # Determine which steps to run (use 4-phase order)
        steps_to_run = self._config.get("steps", self.STEP_ORDER.copy())
        if isinstance(steps_to_run, str):
            steps_to_run = [int(s.strip()) for s in steps_to_run.split(",")]

        # Reorder steps according to 4-phase flow if all steps requested
        if set(steps_to_run) == set(range(1, 10)):
            steps_to_run = self.STEP_ORDER.copy()

        # Run each step
        results: Dict[str, StepResult] = {}

        step_methods = {
            1: self._step_critique,
            2: self._step_logic_check,
            3: self._step_logos,
            4: self._step_pathos,
            5: self._step_ethos,
            6: self._step_blind_spots,
            7: self._step_shatter_points,
            8: self._step_bloom,
        }

        for step_num in steps_to_run:
            if step_num not in self.STEPS:
                continue

            step_name, phase, description = self.STEPS[step_num]
            logger.info(f"Running step {step_num}: {step_name} ({phase} phase)")

            if step_num == 9:
                # Evolve needs previous results
                result = self._step_evolve(corpus, domain, results)
            elif step_num in step_methods:
                result = step_methods[step_num](corpus, domain)
            else:
                continue

            results[step_name] = result

        # Build phase summaries (now includes 4 phases)
        phases = {
            "evaluation": {},
            "reinforcement": {},
            "risk": {},
            "growth": {},
        }

        for step_num, (step_name, phase, _) in self.STEPS.items():
            if step_name in results:
                phase_key = phase.lower()
                if phase_key not in phases:
                    phases[phase_key] = {}
                phases[phase_key][step_name] = results[step_name].to_dict()

        # Calculate summary scores by phase
        phase_scores = {}
        for phase_name, phase_data in phases.items():
            if phase_data:
                scores = [s["score"] for s in phase_data.values()]
                phase_scores[phase_name] = mean(scores) if scores else 0

        all_scores = [r.score for r in results.values()]
        overall_score = mean(all_scores) if all_scores else 0

        # Collect top recommendations
        all_recs = []
        for result in results.values():
            all_recs.extend(result.recommendations)

        # Deduplicate recommendations
        seen_recs = set()
        unique_recs = []
        for rec in all_recs:
            rec_key = rec.lower()[:40]
            if rec_key not in seen_recs:
                seen_recs.add(rec_key)
                unique_recs.append(rec)

        # Build flow data for visualization (in 4-phase order)
        flow = []
        for step_num in steps_to_run:
            if step_num not in self.STEPS:
                continue
            step_name, phase, description = self.STEPS[step_num]
            if step_name in results:
                flow.append({
                    "step": step_num,
                    "name": step_name,
                    "phase": phase,
                    "description": description,
                    "score": results[step_name].score,
                    "llm_enhanced": results[step_name].llm_insights is not None,
                })

        # Get chain history if available
        chain_data = []
        chain_usage = {}
        if self._chain_executor:
            chain_data = self._chain_executor.get_chain_for_visualization()
            chain_usage = self._chain_executor.get_usage_summary()

        return self.make_output(
            data={
                "phases": phases,
                "summary": {
                    "overall_score": overall_score,
                    "phase_scores": phase_scores,
                    "top_recommendations": unique_recs[:10],
                },
                "flow": flow,
                "prompt_chain": chain_data,
            },
            metadata={
                "steps_run": steps_to_run,
                "step_order": "4-phase",
                "llm_enabled": self._llm_provider is not None,
                "chain_enabled": self._chain_executor is not None,
                "chain_usage": chain_usage,
                "vader_available": VADER_AVAILABLE,
                "spacy_available": SPACY_AVAILABLE,
            },
        )
