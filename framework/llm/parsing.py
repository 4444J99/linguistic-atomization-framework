"""
Output Parsing for LLM Responses - Structured extraction from AI outputs.

Provides parsers to extract structured data from various LLM response formats:
- JSON blocks (markdown-wrapped or raw)
- Section-based text (Strengths/Weaknesses/etc.)
- Key-value pairs
- Lists and bullet points
"""

from __future__ import annotations

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


class OutputParser(ABC):
    """
    Abstract base class for parsing LLM responses into structured data.

    Subclasses implement specific parsing strategies for different
    output formats (JSON, sections, etc.).
    """

    @abstractmethod
    def parse(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response text into structured data.

        Args:
            response_text: Raw text from LLM response

        Returns:
            Parsed structured data as dictionary
        """
        pass

    def validate(
        self,
        parsed: Dict[str, Any],
        schema: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Validate parsed output against expected schema.

        Args:
            parsed: Parsed data dictionary
            schema: Optional JSON schema to validate against

        Returns:
            True if valid, False otherwise
        """
        if schema is None:
            return True

        required = schema.get("required", [])
        for field in required:
            if field not in parsed:
                logger.warning(f"Missing required field: {field}")
                return False

        return True


class JSONOutputParser(OutputParser):
    """
    Parse JSON from LLM responses.

    Handles:
    - JSON in markdown code blocks (```json ... ```)
    - Raw JSON responses
    - Fallback to section parsing if JSON fails
    """

    # Patterns for JSON extraction
    JSON_BLOCK_PATTERN = re.compile(
        r'```(?:json)?\s*\n?(\{[\s\S]*?\})\s*\n?```',
        re.MULTILINE
    )
    JSON_ARRAY_BLOCK_PATTERN = re.compile(
        r'```(?:json)?\s*\n?(\[[\s\S]*?\])\s*\n?```',
        re.MULTILINE
    )
    RAW_JSON_PATTERN = re.compile(
        r'^\s*(\{[\s\S]*\})\s*$',
        re.MULTILINE
    )

    def __init__(self, fallback_parser: Optional[OutputParser] = None):
        """
        Initialize JSON parser with optional fallback.

        Args:
            fallback_parser: Parser to use if JSON extraction fails
        """
        self._fallback = fallback_parser

    def parse(self, response_text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON from response text.

        Tries multiple extraction strategies in order:
        1. JSON in markdown code block
        2. Raw JSON object
        3. Fallback parser (if provided)
        4. Empty dict with raw text preserved
        """
        if not response_text:
            return {"_raw": "", "_parse_error": "Empty response"}

        # Try markdown code block first
        match = self.JSON_BLOCK_PATTERN.search(response_text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.debug(f"JSON decode failed for code block: {e}")

        # Try array in code block
        match = self.JSON_ARRAY_BLOCK_PATTERN.search(response_text)
        if match:
            try:
                return {"items": json.loads(match.group(1))}
            except json.JSONDecodeError as e:
                logger.debug(f"JSON array decode failed: {e}")

        # Try raw JSON object
        match = self.RAW_JSON_PATTERN.search(response_text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.debug(f"Raw JSON decode failed: {e}")

        # Try to find any JSON-like structure in the text
        json_start = response_text.find('{')
        if json_start != -1:
            # Find matching closing brace
            depth = 0
            for i, char in enumerate(response_text[json_start:], json_start):
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(response_text[json_start:i+1])
                        except json.JSONDecodeError:
                            break

        # Use fallback parser if available
        if self._fallback:
            return self._fallback.parse(response_text)

        # Return raw text with error marker
        return {
            "_raw": response_text,
            "_parse_error": "Could not extract JSON",
        }


class SectionParser(OutputParser):
    """
    Parse responses with labeled sections.

    Extracts content from sections like:
    - Strengths: ...
    - Weaknesses: ...
    - Observation: ...
    - Recommendation: ...

    Handles various formats (bullets, colons, dashes).
    """

    # Common section labels to look for
    SECTION_LABELS = [
        # Evaluation sections
        "strength", "strengths", "strong point", "strong points",
        "weakness", "weaknesses", "weak point", "weak points",
        "observation", "observations",
        "recommendation", "recommendations",
        "finding", "findings",
        # Analysis sections
        "assessment", "analysis", "evaluation",
        "issue", "issues", "problem", "problems",
        "suggestion", "suggestions",
        "insight", "insights",
        # Risk sections
        "vulnerability", "vulnerabilities",
        "gap", "gaps", "blind spot", "blind spots",
        "risk", "risks",
        # Growth sections
        "opportunity", "opportunities",
        "improvement", "improvements",
        "action", "actions", "next step", "next steps",
    ]

    # Pattern to match section headers
    SECTION_PATTERN = re.compile(
        r'(?:^|\n)\s*[-•*]?\s*(?:\d+\.)?\s*'
        r'([A-Za-z][A-Za-z\s]+?):\s*(.+?)(?=\n\s*[-•*]?\s*(?:\d+\.)?\s*[A-Za-z][A-Za-z\s]+?:|$)',
        re.DOTALL | re.IGNORECASE
    )

    def parse(self, response_text: str) -> Dict[str, Any]:
        """
        Parse section-based response into structured data.
        """
        if not response_text:
            return {"_raw": "", "_parse_error": "Empty response"}

        result: Dict[str, Any] = {}
        found_sections = False

        # Find all section matches
        for match in self.SECTION_PATTERN.finditer(response_text):
            label = match.group(1).strip().lower()
            content = match.group(2).strip()

            # Normalize label
            normalized = self._normalize_label(label)
            if normalized:
                found_sections = True
                items = self._extract_items(content)

                # Store as list if multiple items, otherwise as single value
                if len(items) > 1:
                    result[normalized] = items
                elif len(items) == 1:
                    result[normalized] = items[0]

        # Also try bullet-point extraction
        if not found_sections:
            bullets = self._extract_bullets(response_text)
            if bullets:
                result["items"] = bullets
                found_sections = True

        # If no structured data found, preserve raw text
        if not found_sections:
            result["_raw"] = response_text
            result["_parse_error"] = "No sections found"

        return result

    def _normalize_label(self, label: str) -> Optional[str]:
        """Normalize section label to consistent key."""
        label = label.lower().strip()

        # Map to canonical names
        mappings = {
            "strength": "strengths",
            "strong point": "strengths",
            "strong points": "strengths",
            "weakness": "weaknesses",
            "weak point": "weaknesses",
            "weak points": "weaknesses",
            "observation": "observations",
            "recommendation": "recommendations",
            "suggestion": "recommendations",
            "finding": "findings",
            "issue": "issues",
            "problem": "issues",
            "vulnerability": "vulnerabilities",
            "gap": "gaps",
            "blind spot": "blind_spots",
            "risk": "risks",
            "opportunity": "opportunities",
            "improvement": "improvements",
            "action": "actions",
            "next step": "next_steps",
            "insight": "insights",
        }

        # Check exact match first
        if label in mappings:
            return mappings[label]

        # Check if label ends with plural 's'
        if label.endswith('s') and label[:-1] in mappings:
            return mappings[label[:-1]]

        # Return normalized label if it's a known section type
        for known in self.SECTION_LABELS:
            if label == known or label == known + 's':
                return label.replace(' ', '_') + ('s' if not label.endswith('s') else '')

        return None

    def _extract_items(self, content: str) -> List[str]:
        """Extract individual items from section content."""
        items = []

        # Try bullet points first
        bullet_pattern = re.compile(r'[-•*]\s*(.+?)(?=\n[-•*]|\n\n|$)', re.DOTALL)
        bullets = bullet_pattern.findall(content)

        if bullets:
            items = [b.strip() for b in bullets if b.strip()]
        else:
            # Try numbered items
            numbered_pattern = re.compile(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', re.DOTALL)
            numbered = numbered_pattern.findall(content)

            if numbered:
                items = [n.strip() for n in numbered if n.strip()]
            else:
                # Split by sentences or newlines
                parts = re.split(r'[.\n]+', content)
                items = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]

        return items

    def _extract_bullets(self, text: str) -> List[str]:
        """Extract all bullet points from text."""
        bullet_pattern = re.compile(r'^\s*[-•*]\s*(.+)$', re.MULTILINE)
        matches = bullet_pattern.findall(text)
        return [m.strip() for m in matches if m.strip()]


class KeyValueParser(OutputParser):
    """
    Parse key-value pair responses.

    Handles formats like:
    - Key: Value
    - **Key**: Value
    - Key = Value
    """

    KV_PATTERNS = [
        re.compile(r'\*\*([^*]+)\*\*:\s*(.+?)(?=\n\*\*|$)', re.DOTALL),  # **Key**: Value
        re.compile(r'^([A-Za-z][A-Za-z\s]+):\s*(.+?)(?=\n[A-Za-z]|$)', re.MULTILINE | re.DOTALL),  # Key: Value
        re.compile(r'^([A-Za-z][A-Za-z\s]+)\s*=\s*(.+?)(?=\n[A-Za-z]|$)', re.MULTILINE | re.DOTALL),  # Key = Value
    ]

    def parse(self, response_text: str) -> Dict[str, Any]:
        """Parse key-value pairs from response."""
        if not response_text:
            return {"_raw": "", "_parse_error": "Empty response"}

        result: Dict[str, Any] = {}

        for pattern in self.KV_PATTERNS:
            for match in pattern.finditer(response_text):
                key = match.group(1).strip().lower().replace(' ', '_')
                value = match.group(2).strip()

                # Clean up value
                if value.endswith('.'):
                    value = value[:-1]

                # Try to parse numeric values
                try:
                    if '.' in value:
                        result[key] = float(value)
                    else:
                        result[key] = int(value)
                except ValueError:
                    result[key] = value

        if not result:
            result["_raw"] = response_text
            result["_parse_error"] = "No key-value pairs found"

        return result


class CompositeParser(OutputParser):
    """
    Try multiple parsers in sequence until one succeeds.

    Useful for handling varied LLM output formats.
    """

    def __init__(self, parsers: Optional[List[OutputParser]] = None):
        """
        Initialize with list of parsers to try.

        Args:
            parsers: List of parsers to try in order.
                    Defaults to JSON -> Section -> KeyValue
        """
        if parsers is None:
            self._parsers = [
                JSONOutputParser(),
                SectionParser(),
                KeyValueParser(),
            ]
        else:
            self._parsers = parsers

    def parse(self, response_text: str) -> Dict[str, Any]:
        """Try each parser until one succeeds without errors."""
        for parser in self._parsers:
            result = parser.parse(response_text)

            # Check if parsing was successful (no error marker)
            if "_parse_error" not in result:
                return result

        # All parsers failed, return best effort
        return {
            "_raw": response_text,
            "_parse_error": "All parsers failed",
        }


class RhetoricalOutputParser(OutputParser):
    """
    Specialized parser for rhetorical evaluation outputs.

    Combines JSON and section parsing with specific handling for
    evaluation step outputs, including normalization of findings,
    recommendations, and scores.
    """

    def __init__(self):
        self._json_parser = JSONOutputParser()
        self._section_parser = SectionParser()

    def parse(self, response_text: str) -> Dict[str, Any]:
        """Parse rhetorical evaluation output."""
        if not response_text:
            return {"_raw": "", "_parse_error": "Empty response"}

        # Try JSON first
        result = self._json_parser.parse(response_text)

        # If JSON parsing failed, try section parsing
        if "_parse_error" in result:
            result = self._section_parser.parse(response_text)

        # Normalize the output
        return self._normalize_output(result)

    def _normalize_output(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize parsed output to consistent format."""
        normalized = {}

        for key, value in parsed.items():
            # Skip internal keys
            if key.startswith('_'):
                normalized[key] = value
                continue

            # Normalize key
            norm_key = key.lower().replace(' ', '_').replace('-', '_')

            # Ensure lists are lists
            if norm_key in ['strengths', 'weaknesses', 'recommendations', 'findings',
                           'issues', 'gaps', 'vulnerabilities', 'opportunities',
                           'insights', 'actions']:
                if isinstance(value, str):
                    normalized[norm_key] = [value]
                elif isinstance(value, list):
                    normalized[norm_key] = value
                else:
                    normalized[norm_key] = [str(value)]
            else:
                normalized[norm_key] = value

        # Extract confidence if present
        if 'confidence' in normalized:
            try:
                conf = normalized['confidence']
                if isinstance(conf, str):
                    conf = float(conf.replace('%', '')) / 100 if '%' in conf else float(conf)
                normalized['confidence'] = min(1.0, max(0.0, conf))
            except (ValueError, TypeError):
                normalized['confidence'] = 0.5

        return normalized

    def extract_recommendations(self, parsed: Dict[str, Any]) -> List[str]:
        """Extract recommendations from parsed output."""
        recs = []

        # Check common recommendation fields
        for key in ['recommendations', 'suggestions', 'fixes', 'improvements',
                    'actions', 'next_steps', 'priority_fixes', 'quick_wins']:
            if key in parsed:
                value = parsed[key]
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            recs.append(item)
                        elif isinstance(item, dict):
                            # Extract text from dict item
                            for text_key in ['action', 'recommendation', 'fix', 'text', 'description']:
                                if text_key in item:
                                    recs.append(str(item[text_key]))
                                    break
                elif isinstance(value, str):
                    recs.append(value)

        return recs

    def extract_findings(self, parsed: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract findings from parsed output."""
        findings = []

        # Process strengths
        for item in parsed.get('strengths', []):
            finding = self._item_to_finding(item, 'strength')
            if finding:
                findings.append(finding)

        # Process weaknesses
        for item in parsed.get('weaknesses', []):
            finding = self._item_to_finding(item, 'weakness')
            if finding:
                findings.append(finding)

        # Process issues/vulnerabilities/gaps
        for key, finding_type in [('issues', 'issue'), ('vulnerabilities', 'vulnerability'),
                                   ('gaps', 'gap'), ('blind_spots', 'blind_spot'),
                                   ('insights', 'insight')]:
            for item in parsed.get(key, []):
                finding = self._item_to_finding(item, finding_type)
                if finding:
                    findings.append(finding)

        return findings

    def _item_to_finding(
        self,
        item: Union[str, Dict[str, Any]],
        finding_type: str,
    ) -> Optional[Dict[str, Any]]:
        """Convert an item to a finding dict."""
        if isinstance(item, str):
            return {
                "type": finding_type,
                "description": item,
            }
        elif isinstance(item, dict):
            finding = {"type": finding_type}

            # Extract description
            for key in ['point', 'description', 'text', 'issue', 'vulnerability', 'finding']:
                if key in item:
                    finding['description'] = item[key]
                    break

            if 'description' not in finding:
                finding['description'] = str(item)

            # Copy other useful fields
            for key in ['example', 'location', 'severity', 'impact', 'fix', 'score_impact']:
                if key in item:
                    finding[key] = item[key]

            return finding

        return None


# Default parser instance for convenience
default_parser = RhetoricalOutputParser()
