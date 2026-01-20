"""
Prompt Templates for Rhetorical Evaluation - AI Prompt Chain System.

Provides structured prompts for all 9 evaluation steps with:
- Clear purpose and desired outcomes
- Example outputs for consistent formatting
- Output schemas for parsing
- Chain-of-thought reasoning support
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """
    Structured prompt template for a single evaluation step.

    Contains all information needed to execute and parse an LLM analysis step,
    including the prompt text, expected output format, and example outputs.
    """
    step_id: str
    step_name: str
    phase: str
    purpose: str
    desired_outcome: str
    prompt: str
    system_role: str
    example_output: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    chain_context_keys: List[str] = field(default_factory=list)

    def format(self, **kwargs) -> str:
        """Format the prompt with provided context variables."""
        try:
            return self.prompt.format(**kwargs)
        except KeyError as e:
            # Return partially formatted prompt if some keys missing
            result = self.prompt
            for key, value in kwargs.items():
                result = result.replace(f"{{{key}}}", str(value))
            return result


# =============================================================================
# RHETORICAL PROMPT LIBRARY
# =============================================================================

RHETORICAL_PROMPTS: Dict[str, PromptTemplate] = {

    # =========================================================================
    # EVALUATION PHASE
    # =========================================================================

    "critique": PromptTemplate(
        step_id="1",
        step_name="Critique",
        phase="Evaluation",
        purpose="Provide comprehensive evaluation of strengths and weaknesses",
        desired_outcome="Clear understanding of what works well and what needs improvement",
        prompt='''Evaluate this content thoroughly. Identify its key strengths and weaknesses.
Highlight which parts are effective and which need improvement, providing specific reasons.

CONTENT:
{text}

Provide your analysis in this JSON format:
```json
{{
    "strengths": [
        {{"point": "description", "example": "specific text example", "impact": "why this works"}}
    ],
    "weaknesses": [
        {{"point": "description", "example": "specific text example", "fix": "how to improve"}}
    ],
    "key_observations": ["observation 1", "observation 2", "observation 3"],
    "overall_assessment": "brief overall evaluation",
    "confidence": 0.85
}}
```''',
        system_role="You are an expert rhetorical analyst specializing in written communication evaluation. Be specific and cite examples from the text.",
        example_output={
            "strengths": [
                {"point": "Clear main argument", "example": "The thesis in paragraph 1...", "impact": "Sets clear expectations"}
            ],
            "weaknesses": [
                {"point": "Weak conclusion", "example": "The final paragraph...", "fix": "Add call to action"}
            ],
            "key_observations": ["Well-structured introduction", "Evidence needs strengthening", "Tone is consistent"],
            "overall_assessment": "Solid foundation with room for improvement in evidence quality",
            "confidence": 0.85
        },
        output_schema={
            "type": "object",
            "required": ["strengths", "weaknesses", "key_observations"],
            "properties": {
                "strengths": {"type": "array"},
                "weaknesses": {"type": "array"},
                "key_observations": {"type": "array"},
                "overall_assessment": {"type": "string"},
                "confidence": {"type": "number"}
            }
        },
    ),

    "logos": PromptTemplate(
        step_id="3",
        step_name="Logos Review",
        phase="Evaluation",
        purpose="Assess clarity and persuasiveness of rational arguments",
        desired_outcome="Strengthen the argument's intellectual and factual appeal",
        prompt='''Assess the rational and factual appeal (logos) of this content.
Analyze whether arguments are clear, well-supported, and logically persuasive.

CONTENT:
{text}

Provide your analysis in this JSON format:
```json
{{
    "logical_structure": {{
        "assessment": "description of argument structure",
        "score": 75,
        "issues": ["issue 1", "issue 2"]
    }},
    "evidence_quality": {{
        "assessment": "description of evidence used",
        "score": 70,
        "gaps": ["gap 1", "gap 2"]
    }},
    "reasoning_chains": [
        {{"claim": "the claim", "support": "supporting evidence", "strength": "strong/moderate/weak"}}
    ],
    "recommendations": ["recommendation 1", "recommendation 2"],
    "confidence": 0.80
}}
```''',
        system_role="You are an expert in logic, argumentation, and evidence-based reasoning. Focus on the rational persuasiveness of the content.",
        example_output={
            "logical_structure": {
                "assessment": "Arguments are clearly stated but some leaps in logic",
                "score": 75,
                "issues": ["Jump from premise to conclusion in paragraph 3"]
            },
            "evidence_quality": {
                "assessment": "Good use of statistics but lacks primary sources",
                "score": 70,
                "gaps": ["No expert citations", "Statistics not sourced"]
            },
            "reasoning_chains": [
                {"claim": "Market share increased", "support": "Sales data from Q3", "strength": "strong"}
            ],
            "recommendations": ["Add source citations", "Strengthen conclusion logic"],
            "confidence": 0.80
        },
        output_schema={
            "type": "object",
            "required": ["logical_structure", "evidence_quality", "recommendations"],
            "properties": {
                "logical_structure": {"type": "object"},
                "evidence_quality": {"type": "object"},
                "reasoning_chains": {"type": "array"},
                "recommendations": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
    ),

    "pathos": PromptTemplate(
        step_id="4",
        step_name="Pathos Review",
        phase="Evaluation",
        purpose="Evaluate emotional resonance and appeal to audience",
        desired_outcome="Create strong emotional connection with the audience",
        prompt='''Analyze the emotional tone and resonance (pathos) of this content.
Evaluate whether it creates emotional connection with its intended audience.

CONTENT:
{text}

Provide your analysis in this JSON format:
```json
{{
    "emotional_tone": {{
        "primary": "dominant emotion",
        "secondary": ["other emotions"],
        "consistency": "assessment of tone consistency"
    }},
    "audience_connection": {{
        "assessment": "how well it connects",
        "score": 70,
        "techniques_used": ["technique 1", "technique 2"]
    }},
    "emotional_arc": {{
        "opening": "emotion at start",
        "middle": "emotion in body",
        "closing": "emotion at end",
        "effectiveness": "assessment of arc"
    }},
    "recommendations": ["recommendation 1", "recommendation 2"],
    "confidence": 0.75
}}
```''',
        system_role="You are an expert in emotional intelligence, audience engagement, and persuasive communication. Focus on emotional impact and connection.",
        example_output={
            "emotional_tone": {
                "primary": "hopeful",
                "secondary": ["urgent", "empathetic"],
                "consistency": "Generally consistent with minor tonal shifts"
            },
            "audience_connection": {
                "assessment": "Good use of relatable examples but could be more personal",
                "score": 70,
                "techniques_used": ["Inclusive language (we/us)", "Vivid imagery"]
            },
            "emotional_arc": {
                "opening": "Concern/problem statement",
                "middle": "Building hope through solutions",
                "closing": "Optimistic call to action",
                "effectiveness": "Well-crafted progression"
            },
            "recommendations": ["Add personal anecdote", "Strengthen emotional close"],
            "confidence": 0.75
        },
        output_schema={
            "type": "object",
            "required": ["emotional_tone", "audience_connection", "recommendations"],
            "properties": {
                "emotional_tone": {"type": "object"},
                "audience_connection": {"type": "object"},
                "emotional_arc": {"type": "object"},
                "recommendations": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
    ),

    "ethos": PromptTemplate(
        step_id="5",
        step_name="Ethos Review",
        phase="Evaluation",
        purpose="Examine credibility, authority, and trustworthiness",
        desired_outcome="Enhance the speaker's or writer's reliability and authority",
        prompt='''Evaluate the credibility and authority (ethos) of this content.
Assess whether it reflects expertise and trustworthiness.

CONTENT:
{text}

Provide your analysis in this JSON format:
```json
{{
    "credibility_markers": {{
        "present": ["marker 1", "marker 2"],
        "missing": ["expected marker 1", "expected marker 2"],
        "score": 70
    }},
    "authority_signals": {{
        "expertise_demonstrated": "assessment",
        "sources_quality": "assessment",
        "professional_tone": "assessment"
    }},
    "trust_factors": {{
        "transparency": "assessment",
        "balanced_perspective": "assessment",
        "acknowledgment_of_limits": "assessment"
    }},
    "hedging_analysis": {{
        "count": 5,
        "appropriateness": "assessment of hedging usage"
    }},
    "recommendations": ["recommendation 1", "recommendation 2"],
    "confidence": 0.80
}}
```''',
        system_role="You are an expert in credibility assessment, professional communication, and trust-building in written content. Focus on authority and reliability.",
        example_output={
            "credibility_markers": {
                "present": ["Expert terminology", "Reference to established research"],
                "missing": ["Author credentials", "Institutional backing"],
                "score": 70
            },
            "authority_signals": {
                "expertise_demonstrated": "Good command of subject matter",
                "sources_quality": "Mix of quality sources, some unverified",
                "professional_tone": "Appropriate and consistent"
            },
            "trust_factors": {
                "transparency": "Clear about methodology",
                "balanced_perspective": "Acknowledges some counterpoints",
                "acknowledgment_of_limits": "Could better address limitations"
            },
            "hedging_analysis": {
                "count": 5,
                "appropriateness": "Appropriate level of epistemic humility"
            },
            "recommendations": ["Add author bio/credentials", "Cite more primary sources"],
            "confidence": 0.80
        },
        output_schema={
            "type": "object",
            "required": ["credibility_markers", "authority_signals", "recommendations"],
            "properties": {
                "credibility_markers": {"type": "object"},
                "authority_signals": {"type": "object"},
                "trust_factors": {"type": "object"},
                "hedging_analysis": {"type": "object"},
                "recommendations": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
    ),

    # =========================================================================
    # REINFORCEMENT PHASE
    # =========================================================================

    "logic_check": PromptTemplate(
        step_id="2",
        step_name="Logic Check",
        phase="Reinforcement",
        purpose="Ensure internal consistency and sound reasoning",
        desired_outcome="Eliminate contradictions and reinforce logical coherence",
        prompt='''Examine the content for logical consistency, building on previous evaluation findings.
Identify contradictions, gaps in reasoning, or unsupported claims.

CONTENT:
{text}

PREVIOUS EVALUATION FINDINGS:
{previous_findings}

Provide your analysis in this JSON format:
```json
{{
    "contradictions": [
        {{"location": "where found", "statement_1": "first claim", "statement_2": "conflicting claim", "severity": "high/medium/low"}}
    ],
    "logical_gaps": [
        {{"location": "where found", "description": "the gap", "impact": "how it affects argument"}}
    ],
    "unsupported_claims": [
        {{"claim": "the claim", "location": "where found", "evidence_needed": "what would strengthen it"}}
    ],
    "coherence_assessment": {{
        "overall": "assessment",
        "score": 75,
        "strongest_sections": ["section 1"],
        "weakest_sections": ["section 2"]
    }},
    "fixes": ["fix 1", "fix 2", "fix 3"],
    "confidence": 0.85
}}
```''',
        system_role="You are an expert in logic, critical thinking, and argument analysis. Your role is to identify inconsistencies and strengthen coherence.",
        example_output={
            "contradictions": [
                {"location": "Paragraphs 2 and 5", "statement_1": "Market is growing", "statement_2": "Declining revenues", "severity": "high"}
            ],
            "logical_gaps": [
                {"location": "Paragraph 3", "description": "Jump from data to conclusion", "impact": "Weakens central argument"}
            ],
            "unsupported_claims": [
                {"claim": "Industry standard practice", "location": "Paragraph 4", "evidence_needed": "Citation or data"}
            ],
            "coherence_assessment": {
                "overall": "Generally coherent with some gaps",
                "score": 75,
                "strongest_sections": ["Introduction", "Methodology"],
                "weakest_sections": ["Results interpretation"]
            },
            "fixes": ["Reconcile growth vs revenue claims", "Add transitional logic in P3", "Support claim with citation"],
            "confidence": 0.85
        },
        output_schema={
            "type": "object",
            "required": ["contradictions", "logical_gaps", "coherence_assessment", "fixes"],
            "properties": {
                "contradictions": {"type": "array"},
                "logical_gaps": {"type": "array"},
                "unsupported_claims": {"type": "array"},
                "coherence_assessment": {"type": "object"},
                "fixes": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
        chain_context_keys=["previous_findings"],
    ),

    # =========================================================================
    # RISK ANALYSIS PHASE
    # =========================================================================

    "blind_spots": PromptTemplate(
        step_id="6",
        step_name="Blind Spots",
        phase="Risk",
        purpose="Reveal overlooked areas or hidden assumptions",
        desired_outcome="Reduce risk of missed issues or unchallenged assumptions",
        prompt='''Identify any areas in this content that may be overlooked, biased,
or based on hidden assumptions. Consider perspectives that may not be represented.

CONTENT:
{text}

EVALUATION CONTEXT:
{evaluation_summary}

Provide your analysis in this JSON format:
```json
{{
    "hidden_assumptions": [
        {{"assumption": "the assumption", "location": "where found", "risk": "why this is problematic", "fix": "how to address"}}
    ],
    "overlooked_perspectives": [
        {{"perspective": "missing viewpoint", "importance": "why it matters", "suggestion": "how to include"}}
    ],
    "bias_indicators": [
        {{"type": "type of bias", "evidence": "where observed", "severity": "high/medium/low"}}
    ],
    "missing_counterarguments": [
        {{"counterargument": "potential objection", "strength": "how strong", "how_to_address": "response strategy"}}
    ],
    "coverage_gaps": ["gap 1", "gap 2"],
    "recommendations": ["recommendation 1", "recommendation 2"],
    "confidence": 0.75
}}
```''',
        system_role="You are an expert in critical analysis, bias detection, and assumption identification. Your role is to surface what may be missing or assumed.",
        example_output={
            "hidden_assumptions": [
                {"assumption": "Reader has technical background", "location": "Throughout", "risk": "Excludes general audience", "fix": "Add brief explanations of technical terms"}
            ],
            "overlooked_perspectives": [
                {"perspective": "Small business owners", "importance": "Major stakeholder group", "suggestion": "Include case study or interview data"}
            ],
            "bias_indicators": [
                {"type": "Selection bias", "evidence": "Only positive examples cited", "severity": "medium"}
            ],
            "missing_counterarguments": [
                {"counterargument": "Cost concerns", "strength": "Strong - common objection", "how_to_address": "Acknowledge and provide ROI data"}
            ],
            "coverage_gaps": ["Implementation challenges", "Long-term sustainability"],
            "recommendations": ["Add glossary for technical terms", "Include opposing viewpoint section"],
            "confidence": 0.75
        },
        output_schema={
            "type": "object",
            "required": ["hidden_assumptions", "overlooked_perspectives", "recommendations"],
            "properties": {
                "hidden_assumptions": {"type": "array"},
                "overlooked_perspectives": {"type": "array"},
                "bias_indicators": {"type": "array"},
                "missing_counterarguments": {"type": "array"},
                "coverage_gaps": {"type": "array"},
                "recommendations": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
        chain_context_keys=["evaluation_summary"],
    ),

    "shatter_points": PromptTemplate(
        step_id="7",
        step_name="Shatter Points",
        phase="Risk",
        purpose="Pinpoint vulnerabilities or potential breaking points",
        desired_outcome="Prepare for or prevent critical failures in the argument",
        prompt='''Analyze the content for potential vulnerabilities or weak points
that could cause the argument to fail under scrutiny or criticism.

CONTENT:
{text}

PREVIOUS FINDINGS:
{previous_findings}

Provide your analysis in this JSON format:
```json
{{
    "critical_vulnerabilities": [
        {{"vulnerability": "description", "location": "where found", "severity": "high/medium/low", "attack_vector": "how it could be exploited", "fix": "how to reinforce"}}
    ],
    "weak_evidence": [
        {{"claim": "the claim", "current_support": "existing evidence", "vulnerability": "why it's weak", "reinforcement": "how to strengthen"}}
    ],
    "logical_fallacies": [
        {{"fallacy_type": "name of fallacy", "location": "where found", "example": "the text", "correction": "how to fix"}}
    ],
    "credibility_risks": [
        {{"risk": "description", "likelihood": "high/medium/low", "mitigation": "how to address"}}
    ],
    "overall_resilience": {{
        "score": 70,
        "assessment": "overall vulnerability assessment"
    }},
    "priority_fixes": ["fix 1", "fix 2", "fix 3"],
    "confidence": 0.80
}}
```''',
        system_role="You are an expert in risk assessment, argument vulnerability analysis, and rhetorical defense strategies. Identify points where the argument could break under criticism.",
        example_output={
            "critical_vulnerabilities": [
                {"vulnerability": "Over-reliance on single study", "location": "Core argument in P3", "severity": "high", "attack_vector": "If study is contested, entire argument fails", "fix": "Add corroborating sources"}
            ],
            "weak_evidence": [
                {"claim": "Industry-wide trend", "current_support": "One company example", "vulnerability": "Anecdotal, not systematic", "reinforcement": "Add industry survey data"}
            ],
            "logical_fallacies": [
                {"fallacy_type": "Appeal to authority", "location": "Paragraph 4", "example": "Experts agree...", "correction": "Name specific experts and cite"}
            ],
            "credibility_risks": [
                {"risk": "Outdated statistics", "likelihood": "medium", "mitigation": "Update to current year data"}
            ],
            "overall_resilience": {
                "score": 70,
                "assessment": "Moderate resilience with key vulnerabilities in evidence base"
            },
            "priority_fixes": ["Diversify source base", "Update statistics", "Remove logical fallacy"],
            "confidence": 0.80
        },
        output_schema={
            "type": "object",
            "required": ["critical_vulnerabilities", "overall_resilience", "priority_fixes"],
            "properties": {
                "critical_vulnerabilities": {"type": "array"},
                "weak_evidence": {"type": "array"},
                "logical_fallacies": {"type": "array"},
                "credibility_risks": {"type": "array"},
                "overall_resilience": {"type": "object"},
                "priority_fixes": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
        chain_context_keys=["previous_findings"],
    ),

    # =========================================================================
    # GROWTH PHASE
    # =========================================================================

    "bloom": PromptTemplate(
        step_id="8",
        step_name="Bloom (Emergent Insights)",
        phase="Growth",
        purpose="Highlight new ideas or opportunities for growth",
        desired_outcome="Generate innovative directions or perspectives for development",
        prompt='''From the reviewed content and accumulated analysis findings, generate innovative ideas,
new directions, or emergent insights that could enhance or expand the content's impact.

CONTENT SUMMARY:
{text_summary}

ANALYSIS FINDINGS:
{all_findings}

THEME CONNECTIONS DETECTED:
{theme_connections}

RECURRING CONCEPTS:
{recurring_concepts}

Provide your analysis in this JSON format:
```json
{{
    "emergent_patterns": [
        {{"pattern": "description", "evidence": "where observed", "significance": "why it matters"}}
    ],
    "growth_opportunities": [
        {{"opportunity": "description", "implementation": "how to pursue", "impact": "expected benefit", "effort": "high/medium/low"}}
    ],
    "innovation_directions": [
        {{"direction": "description", "rationale": "why this direction", "first_steps": "how to begin"}}
    ],
    "cross_theme_insights": [
        {{"themes": ["theme 1", "theme 2"], "connection": "how they relate", "synthesis": "what new understanding emerges"}}
    ],
    "expansion_potential": {{
        "immediate": ["opportunity 1", "opportunity 2"],
        "medium_term": ["opportunity 3"],
        "long_term": ["opportunity 4"]
    }},
    "creative_recommendations": ["recommendation 1", "recommendation 2"],
    "confidence": 0.70
}}
```''',
        system_role="You are a creative strategist and innovation consultant. Your role is to find novel insights, hidden connections, and growth opportunities in the content.",
        example_output={
            "emergent_patterns": [
                {"pattern": "Integration theme across sections", "evidence": "Recurring language about connection", "significance": "Central but unstated thesis"}
            ],
            "growth_opportunities": [
                {"opportunity": "Visual infographic version", "implementation": "Convert key statistics to graphics", "impact": "Broader audience reach", "effort": "medium"}
            ],
            "innovation_directions": [
                {"direction": "Interactive assessment tool", "rationale": "Content lends itself to self-evaluation", "first_steps": "Identify scorable criteria"}
            ],
            "cross_theme_insights": [
                {"themes": ["efficiency", "satisfaction"], "connection": "Inverse relationship in data", "synthesis": "Balance framework needed"}
            ],
            "expansion_potential": {
                "immediate": ["Add visual elements", "Create executive summary"],
                "medium_term": ["Develop workshop curriculum"],
                "long_term": ["Write expanded book treatment"]
            },
            "creative_recommendations": ["Develop companion podcast episode", "Create shareable quote graphics"],
            "confidence": 0.70
        },
        output_schema={
            "type": "object",
            "required": ["emergent_patterns", "growth_opportunities", "creative_recommendations"],
            "properties": {
                "emergent_patterns": {"type": "array"},
                "growth_opportunities": {"type": "array"},
                "innovation_directions": {"type": "array"},
                "cross_theme_insights": {"type": "array"},
                "expansion_potential": {"type": "object"},
                "creative_recommendations": {"type": "array"},
                "confidence": {"type": "number"}
            }
        },
        chain_context_keys=["all_findings", "theme_connections", "recurring_concepts"],
    ),

    "evolve": PromptTemplate(
        step_id="9",
        step_name="Evolve (Iterative Refinement)",
        phase="Growth",
        purpose="Integrate feedback and improve continuously",
        desired_outcome="Produce a stronger, more refined, and resilient final product",
        prompt='''Incorporate all feedback and analysis findings to create
a strategic improvement plan for this content.

PHASE SCORES:
{phase_scores}

ALL RECOMMENDATIONS FROM ANALYSIS:
{all_recommendations}

CRITICAL ISSUES IDENTIFIED:
{critical_issues}

GROWTH OPPORTUNITIES:
{growth_opportunities}

Provide your strategic improvement plan in this JSON format:
```json
{{
    "executive_summary": "Brief overview of content state and improvement potential",
    "quick_wins": [
        {{"action": "what to do", "impact": "expected result", "effort": "minimal", "priority": 1}}
    ],
    "structural_changes": [
        {{"change": "what to modify", "rationale": "why needed", "implementation": "how to do it", "dependencies": ["dependency 1"]}}
    ],
    "implementation_sequence": [
        {{"phase": 1, "focus": "description", "actions": ["action 1", "action 2"], "milestone": "what success looks like"}}
    ],
    "expected_outcomes": {{
        "score_improvements": {{"evaluation": "+X", "risk": "+Y", "growth": "+Z"}},
        "qualitative_gains": ["gain 1", "gain 2"]
    }},
    "iteration_recommendations": {{
        "next_review_focus": "what to analyze next",
        "metrics_to_track": ["metric 1", "metric 2"],
        "feedback_loop": "how to gather ongoing feedback"
    }},
    "confidence": 0.85
}}
```''',
        system_role="You are a strategic writing coach and improvement specialist. Your role is to synthesize all feedback into an actionable, prioritized improvement plan.",
        example_output={
            "executive_summary": "Content has strong foundational arguments but needs evidence strengthening and emotional connection. Quick fixes can raise score by 15+ points.",
            "quick_wins": [
                {"action": "Add 3 source citations to key claims", "impact": "Significant credibility boost", "effort": "minimal", "priority": 1},
                {"action": "Insert transition sentences between sections", "impact": "Improved flow", "effort": "minimal", "priority": 2}
            ],
            "structural_changes": [
                {"change": "Reorganize middle section", "rationale": "Current order buries strongest argument", "implementation": "Move paragraph 4 before paragraph 2", "dependencies": ["Update transitions"]}
            ],
            "implementation_sequence": [
                {"phase": 1, "focus": "Quick fixes", "actions": ["Add citations", "Fix transitions"], "milestone": "No unsupported claims"},
                {"phase": 2, "focus": "Structure", "actions": ["Reorder sections", "Strengthen conclusion"], "milestone": "Logical flow verified"}
            ],
            "expected_outcomes": {
                "score_improvements": {"evaluation": "+12", "risk": "+8", "growth": "+5"},
                "qualitative_gains": ["Stronger credibility", "Better reader engagement", "More resilient argument"]
            },
            "iteration_recommendations": {
                "next_review_focus": "Evidence quality after citations added",
                "metrics_to_track": ["Reader engagement", "Argument resilience"],
                "feedback_loop": "Conduct peer review after Phase 1"
            },
            "confidence": 0.85
        },
        output_schema={
            "type": "object",
            "required": ["executive_summary", "quick_wins", "implementation_sequence", "expected_outcomes"],
            "properties": {
                "executive_summary": {"type": "string"},
                "quick_wins": {"type": "array"},
                "structural_changes": {"type": "array"},
                "implementation_sequence": {"type": "array"},
                "expected_outcomes": {"type": "object"},
                "iteration_recommendations": {"type": "object"},
                "confidence": {"type": "number"}
            }
        },
        chain_context_keys=["phase_scores", "all_recommendations", "critical_issues", "growth_opportunities"],
    ),
}


class RhetoricalPromptLibrary:
    """
    Manager for rhetorical evaluation prompts.

    Provides access to prompts by step name or ID, and handles
    the sequencing for chain execution.
    """

    # Define the 4-phase execution order
    PHASE_ORDER = ["Evaluation", "Reinforcement", "Risk", "Growth"]

    # Step execution order within the 4-phase flow
    STEP_ORDER = [
        "critique",      # 1 - Evaluation
        "logos",         # 3 - Evaluation
        "pathos",        # 4 - Evaluation
        "ethos",         # 5 - Evaluation
        "logic_check",   # 2 - Reinforcement (moved after initial evaluation)
        "blind_spots",   # 6 - Risk
        "shatter_points", # 7 - Risk
        "bloom",         # 8 - Growth
        "evolve",        # 9 - Growth
    ]

    # Map step names to step numbers
    STEP_NUMBERS = {
        "critique": 1,
        "logic_check": 2,
        "logos": 3,
        "pathos": 4,
        "ethos": 5,
        "blind_spots": 6,
        "shatter_points": 7,
        "bloom": 8,
        "evolve": 9,
    }

    def __init__(self):
        self.prompts = RHETORICAL_PROMPTS

    def get_prompt(self, step_name: str) -> Optional[PromptTemplate]:
        """Get prompt template by step name."""
        return self.prompts.get(step_name)

    def get_prompt_by_id(self, step_id: str) -> Optional[PromptTemplate]:
        """Get prompt template by step ID."""
        for prompt in self.prompts.values():
            if prompt.step_id == step_id:
                return prompt
        return None

    def get_prompts_for_phase(self, phase: str) -> List[PromptTemplate]:
        """Get all prompts for a given phase."""
        return [
            self.prompts[name]
            for name in self.STEP_ORDER
            if name in self.prompts and self.prompts[name].phase == phase
        ]

    def get_execution_order(self) -> List[str]:
        """Get the recommended step execution order."""
        return self.STEP_ORDER.copy()

    def get_step_number(self, step_name: str) -> int:
        """Get the step number for a step name."""
        return self.STEP_NUMBERS.get(step_name, 0)

    def get_all_steps(self) -> List[str]:
        """Get all step names in execution order."""
        return self.STEP_ORDER.copy()

    def get_phases(self) -> Dict[str, List[str]]:
        """Get steps organized by phase."""
        phases = {}
        for name in self.STEP_ORDER:
            if name in self.prompts:
                phase = self.prompts[name].phase
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(name)
        return phases


# Singleton instance for convenience
prompt_library = RhetoricalPromptLibrary()
