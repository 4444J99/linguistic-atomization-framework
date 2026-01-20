"""
Prompt Chain Executor - Multi-step reasoning with context accumulation.

Orchestrates the execution of evaluation steps as a chain where:
- Each step builds on findings from previous steps
- Context is accumulated and passed between steps
- Prompt/response pairs are tracked for visualization
- Retry logic handles parsing failures
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .parsing import RhetoricalOutputParser, OutputParser
from .prompts import PromptTemplate, RhetoricalPromptLibrary, prompt_library

if TYPE_CHECKING:
    from .providers import LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


@dataclass
class ChainStep:
    """
    Record of a single step in the prompt chain.

    Captures the full context of what was sent to the LLM and
    what was received back, for transparency and debugging.
    """
    step_id: str
    step_name: str
    step_number: int
    phase: str
    prompt_sent: str
    response_received: str
    parsed_output: Dict[str, Any]
    confidence: float
    timestamp: str
    success: bool = True
    error: Optional[str] = None
    usage: Dict[str, int] = field(default_factory=dict)
    retry_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "step_number": self.step_number,
            "phase": self.phase,
            "prompt_preview": self._truncate(self.prompt_sent, 500),
            "response_preview": self._truncate(self.response_received, 500),
            "parsed_output": self.parsed_output,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
            "usage": self.usage,
            "retry_count": self.retry_count,
        }

    def _truncate(self, text: str, max_len: int) -> str:
        """Truncate text with ellipsis."""
        if len(text) <= max_len:
            return text
        return text[:max_len] + "..."

    def to_visualization_dict(self) -> Dict[str, Any]:
        """Get minimal dict for dashboard visualization."""
        return {
            "step": self.step_name.replace("_", " ").title(),
            "step_number": self.step_number,
            "phase": self.phase,
            "prompt_preview": self._truncate(self.prompt_sent, 200),
            "output_preview": self._format_output_preview(),
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "success": self.success,
        }

    def _format_output_preview(self) -> str:
        """Format parsed output for preview display."""
        if "_parse_error" in self.parsed_output:
            return f"Parse error: {self.parsed_output.get('_parse_error', 'Unknown')}"

        # Show key findings
        preview_parts = []

        for key in ['strengths', 'weaknesses', 'recommendations', 'findings',
                    'issues', 'insights', 'quick_wins']:
            if key in self.parsed_output:
                items = self.parsed_output[key]
                if isinstance(items, list) and items:
                    count = len(items)
                    preview_parts.append(f"{key.title()}: {count} items")

        if preview_parts:
            return "; ".join(preview_parts)

        # Fallback to truncated JSON
        return self._truncate(json.dumps(self.parsed_output), 300)


@dataclass
class ChainContext:
    """
    Accumulated context passed between chain steps.

    Stores findings, scores, and recommendations from previous steps
    to inform subsequent analysis.
    """
    text: str = ""
    text_summary: str = ""
    previous_findings: Dict[str, Any] = field(default_factory=dict)
    evaluation_summary: str = ""
    all_findings: Dict[str, Any] = field(default_factory=dict)
    phase_scores: Dict[str, float] = field(default_factory=dict)
    all_recommendations: List[str] = field(default_factory=list)
    critical_issues: List[str] = field(default_factory=list)
    growth_opportunities: List[str] = field(default_factory=list)
    theme_connections: str = ""
    recurring_concepts: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dict with string values for prompt formatting."""
        return {
            "text": self.text,
            "text_summary": self.text_summary,
            "previous_findings": json.dumps(self.previous_findings, indent=2),
            "evaluation_summary": self.evaluation_summary or json.dumps(self.all_findings, indent=2),
            "all_findings": json.dumps(self.all_findings, indent=2),
            "phase_scores": json.dumps(self.phase_scores, indent=2),
            "all_recommendations": "\n".join(f"- {r}" for r in self.all_recommendations),
            "critical_issues": "\n".join(f"- {i}" for i in self.critical_issues),
            "growth_opportunities": "\n".join(f"- {o}" for o in self.growth_opportunities),
            "theme_connections": self.theme_connections,
            "recurring_concepts": self.recurring_concepts,
        }

    def update_from_step(
        self,
        step_name: str,
        parsed_output: Dict[str, Any],
        parser: RhetoricalOutputParser,
    ):
        """Update context with results from a completed step."""
        # Store in findings
        self.all_findings[step_name] = parsed_output

        # Update previous findings for next step
        self.previous_findings = {step_name: parsed_output}

        # Extract and accumulate recommendations
        recs = parser.extract_recommendations(parsed_output)
        self.all_recommendations.extend(recs)

        # Track critical issues
        if 'critical_vulnerabilities' in parsed_output:
            for vuln in parsed_output['critical_vulnerabilities']:
                if isinstance(vuln, dict) and vuln.get('severity') == 'high':
                    desc = vuln.get('vulnerability', str(vuln))
                    self.critical_issues.append(desc)

        if 'logical_gaps' in parsed_output:
            for gap in parsed_output['logical_gaps']:
                if isinstance(gap, dict):
                    desc = gap.get('description', str(gap))
                    self.critical_issues.append(f"Logic: {desc}")

        # Track growth opportunities
        if 'growth_opportunities' in parsed_output:
            for opp in parsed_output['growth_opportunities']:
                if isinstance(opp, dict):
                    desc = opp.get('opportunity', str(opp))
                    self.growth_opportunities.append(desc)
                elif isinstance(opp, str):
                    self.growth_opportunities.append(opp)

    def build_evaluation_summary(self) -> str:
        """Build summary of evaluation phase results."""
        eval_steps = ['critique', 'logos', 'pathos', 'ethos']
        summary_parts = []

        for step in eval_steps:
            if step in self.all_findings:
                findings = self.all_findings[step]

                # Get confidence if available
                conf = findings.get('confidence', 'N/A')
                if isinstance(conf, float):
                    conf = f"{conf:.0%}"

                summary_parts.append(f"**{step.title()}** (confidence: {conf})")

                # Add key findings
                for key in ['strengths', 'weaknesses', 'recommendations', 'key_observations']:
                    if key in findings and findings[key]:
                        items = findings[key]
                        if isinstance(items, list):
                            summary_parts.append(f"  {key.title()}: {len(items)} items")

        self.evaluation_summary = "\n".join(summary_parts) if summary_parts else "No evaluation results yet"
        return self.evaluation_summary


class PromptChainExecutor:
    """
    Execute evaluation as a multi-step reasoning chain with context passing.

    Manages the full evaluation pipeline:
    1. Executes steps in the correct 4-phase order
    2. Passes accumulated context between steps
    3. Tracks all prompt/response pairs for visualization
    4. Handles parsing and retry logic
    """

    def __init__(
        self,
        provider: "LLMProvider",
        prompts: Optional[RhetoricalPromptLibrary] = None,
        parser: Optional[OutputParser] = None,
        max_retries: int = 2,
    ):
        """
        Initialize chain executor.

        Args:
            provider: LLM provider for completions
            prompts: Prompt library (defaults to global prompt_library)
            parser: Output parser (defaults to RhetoricalOutputParser)
            max_retries: Maximum retry attempts on parsing failure
        """
        self.provider = provider
        self.prompts = prompts or prompt_library
        self.parser = parser or RhetoricalOutputParser()
        self.max_retries = max_retries

        self.chain_history: List[ChainStep] = []
        self.context = ChainContext()

        # Track total usage
        self.total_usage = {
            "input_tokens": 0,
            "output_tokens": 0,
        }

    def reset(self):
        """Reset chain state for new execution."""
        self.chain_history = []
        self.context = ChainContext()
        self.total_usage = {"input_tokens": 0, "output_tokens": 0}

    def set_text(self, text: str, summary: Optional[str] = None):
        """
        Set the main text to analyze.

        Args:
            text: Full text content
            summary: Optional summary (generated if not provided)
        """
        self.context.text = text
        self.context.text_summary = summary or self._generate_summary(text)

    def set_theme_data(
        self,
        connections: Optional[List[Dict]] = None,
        concepts: Optional[List[Dict]] = None,
    ):
        """
        Set theme connection and concept data for Growth phase.

        Args:
            connections: Theme connection data
            concepts: Recurring concept data
        """
        if connections:
            conn_strs = [
                f"- {c.get('theme_1', '?')} ↔ {c.get('theme_2', '?')}: {', '.join(c.get('shared_concepts', [])[:3])}"
                for c in connections[:5]
            ]
            self.context.theme_connections = "\n".join(conn_strs) if conn_strs else "No significant connections found"

        if concepts:
            concept_strs = [f"- {c.get('concept', '?')} (frequency: {c.get('frequency', 0)})" for c in concepts[:10]]
            self.context.recurring_concepts = "\n".join(concept_strs) if concept_strs else "No recurring concepts identified"

    def _generate_summary(self, text: str, max_chars: int = 1500) -> str:
        """Generate a summary of the text for context."""
        if len(text) <= max_chars:
            return text

        # Simple truncation with paragraph awareness
        paragraphs = text.split('\n\n')
        summary_parts = []
        current_length = 0

        for para in paragraphs:
            if current_length + len(para) > max_chars:
                if summary_parts:
                    break
                # First paragraph is too long, truncate it
                summary_parts.append(para[:max_chars] + "...")
                break
            summary_parts.append(para)
            current_length += len(para) + 2  # +2 for \n\n

        return "\n\n".join(summary_parts)

    def execute_step(
        self,
        step_name: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> ChainStep:
        """
        Execute a single evaluation step.

        Args:
            step_name: Name of the step to execute
            additional_context: Extra context variables to inject

        Returns:
            ChainStep record of the execution
        """
        template = self.prompts.get_prompt(step_name)
        if not template:
            return self._create_error_step(
                step_name,
                f"Unknown step: {step_name}"
            )

        # Build context for prompt
        context_dict = self.context.to_dict()
        if additional_context:
            context_dict.update(additional_context)

        # Format prompt
        try:
            prompt = template.format(**context_dict)
        except Exception as e:
            logger.error(f"Failed to format prompt for {step_name}: {e}")
            prompt = template.prompt  # Use unformatted as fallback

        # Execute with retry logic
        for attempt in range(self.max_retries + 1):
            response = self.provider.complete(
                prompt=prompt,
                system_prompt=template.system_role,
            )

            if not response.success:
                logger.warning(f"LLM call failed for {step_name}: {response.error}")
                continue

            # Parse response
            parsed = self.parser.parse(response.text)

            # Check if parsing succeeded
            if "_parse_error" not in parsed or attempt == self.max_retries:
                # Success or final attempt
                confidence = self._calculate_confidence(parsed, template)

                step = ChainStep(
                    step_id=template.step_id,
                    step_name=step_name,
                    step_number=self.prompts.get_step_number(step_name),
                    phase=template.phase,
                    prompt_sent=prompt,
                    response_received=response.text,
                    parsed_output=parsed,
                    confidence=confidence,
                    timestamp=datetime.now().isoformat(),
                    success="_parse_error" not in parsed,
                    error=parsed.get("_parse_error"),
                    usage=response.usage,
                    retry_count=attempt,
                )

                # Track usage
                self.total_usage["input_tokens"] += response.usage.get("input_tokens", 0)
                self.total_usage["output_tokens"] += response.usage.get("output_tokens", 0)

                # Update context
                if step.success:
                    self.context.update_from_step(step_name, parsed, self.parser)

                self.chain_history.append(step)
                return step

            logger.info(f"Retrying {step_name} due to parse error (attempt {attempt + 1})")

        # All retries failed
        return self._create_error_step(
            step_name,
            f"Failed after {self.max_retries + 1} attempts",
            template,
        )

    def _create_error_step(
        self,
        step_name: str,
        error: str,
        template: Optional[PromptTemplate] = None,
    ) -> ChainStep:
        """Create an error step record."""
        step = ChainStep(
            step_id=template.step_id if template else "?",
            step_name=step_name,
            step_number=self.prompts.get_step_number(step_name),
            phase=template.phase if template else "Unknown",
            prompt_sent="",
            response_received="",
            parsed_output={"_error": error},
            confidence=0.0,
            timestamp=datetime.now().isoformat(),
            success=False,
            error=error,
        )
        self.chain_history.append(step)
        return step

    def _calculate_confidence(
        self,
        parsed: Dict[str, Any],
        template: PromptTemplate,
    ) -> float:
        """
        Calculate confidence score for parsed output.

        Based on:
        - Presence of required schema fields
        - Self-reported confidence from LLM
        - Output completeness
        """
        if "_parse_error" in parsed:
            return 0.0

        # Start with self-reported confidence if available
        base_confidence = parsed.get("confidence", 0.7)
        if isinstance(base_confidence, str):
            try:
                base_confidence = float(base_confidence.replace('%', '')) / 100
            except ValueError:
                base_confidence = 0.7

        # Check schema completeness
        schema = template.output_schema
        if schema:
            required = schema.get("required", [])
            present = sum(1 for f in required if f in parsed)
            completeness = present / len(required) if required else 1.0
        else:
            completeness = 1.0

        # Combine scores
        confidence = base_confidence * 0.6 + completeness * 0.4
        return min(1.0, max(0.0, confidence))

    def execute_phase(
        self,
        phase: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> List[ChainStep]:
        """
        Execute all steps in a phase.

        Args:
            phase: Phase name (Evaluation, Reinforcement, Risk, Growth)
            additional_context: Extra context for all steps

        Returns:
            List of ChainStep records
        """
        phase_steps = self.prompts.get_prompts_for_phase(phase)
        results = []

        for template in phase_steps:
            step = self.execute_step(template.step_name, additional_context)
            results.append(step)

        # Update phase score in context
        if results:
            scores = [s.confidence * 100 for s in results if s.success]
            if scores:
                from statistics import mean
                self.context.phase_scores[phase.lower()] = mean(scores)

        return results

    def execute_all(
        self,
        steps: Optional[List[str]] = None,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> List[ChainStep]:
        """
        Execute all specified steps in correct order.

        Args:
            steps: List of step names to run (defaults to all)
            additional_context: Extra context for all steps

        Returns:
            List of ChainStep records
        """
        if steps is None:
            step_order = self.prompts.get_execution_order()
        else:
            # Filter to only requested steps, maintaining order
            full_order = self.prompts.get_execution_order()
            step_order = [s for s in full_order if s in steps]

        results = []

        for step_name in step_order:
            # Build evaluation summary after Evaluation phase
            if step_name == "logic_check":
                self.context.build_evaluation_summary()

            step = self.execute_step(step_name, additional_context)
            results.append(step)

            logger.info(
                f"Completed step {step.step_number}: {step_name} "
                f"(confidence: {step.confidence:.0%}, success: {step.success})"
            )

        return results

    def get_chain_for_visualization(self) -> List[Dict[str, Any]]:
        """
        Export chain history for dashboard visualization.

        Returns:
            List of step dicts with visualization-friendly data
        """
        return [step.to_visualization_dict() for step in self.chain_history]

    def get_full_chain_history(self) -> List[Dict[str, Any]]:
        """
        Export complete chain history.

        Returns:
            List of full step dicts
        """
        return [step.to_dict() for step in self.chain_history]

    def get_accumulated_findings(self) -> Dict[str, Any]:
        """Get all accumulated findings from the chain."""
        return self.context.all_findings.copy()

    def get_all_recommendations(self) -> List[str]:
        """Get all accumulated recommendations."""
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for rec in self.context.all_recommendations:
            if rec not in seen:
                seen.add(rec)
                unique.append(rec)
        return unique

    def get_critical_issues(self) -> List[str]:
        """Get all identified critical issues."""
        return self.context.critical_issues.copy()

    def get_phase_scores(self) -> Dict[str, float]:
        """Get scores by phase."""
        return self.context.phase_scores.copy()

    def get_usage_summary(self) -> Dict[str, int]:
        """Get total token usage."""
        return self.total_usage.copy()
