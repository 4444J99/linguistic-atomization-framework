"""
Analysis Reproducibility Module for LingFrame.

Ensures that any analysis can be exactly reproduced by capturing:
- Configuration used
- Framework version
- Timestamps
- Random seeds (if applicable)
- Input checksums

This supports scholarly rigor by enabling verification and replication
of analysis results.
"""

from __future__ import annotations

import hashlib
import json
import platform
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# Framework version - should match pyproject.toml or setup.py
LINGFRAME_VERSION = "0.1.0"


@dataclass
class InputFingerprint:
    """Fingerprint of analysis input for reproducibility verification."""
    checksum: str  # SHA-256 of input content
    byte_size: int
    char_count: int
    source_path: Optional[str] = None
    format: str = "text"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checksum": self.checksum,
            "byte_size": self.byte_size,
            "char_count": self.char_count,
            "source_path": self.source_path,
            "format": self.format,
        }

    @classmethod
    def from_text(cls, text: str, source_path: Optional[str] = None) -> "InputFingerprint":
        """Create fingerprint from text content."""
        encoded = text.encode("utf-8")
        checksum = hashlib.sha256(encoded).hexdigest()
        return cls(
            checksum=checksum,
            byte_size=len(encoded),
            char_count=len(text),
            source_path=source_path,
            format="text",
        )

    @classmethod
    def from_file(cls, path: Path) -> "InputFingerprint":
        """Create fingerprint from file."""
        content = path.read_bytes()
        checksum = hashlib.sha256(content).hexdigest()
        return cls(
            checksum=checksum,
            byte_size=len(content),
            char_count=len(content.decode("utf-8", errors="replace")),
            source_path=str(path),
            format=path.suffix.lstrip(".") or "unknown",
        )


@dataclass
class EnvironmentInfo:
    """Capture of runtime environment for reproducibility."""
    python_version: str
    platform: str
    platform_version: str
    lingframe_version: str
    dependencies: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "python_version": self.python_version,
            "platform": self.platform,
            "platform_version": self.platform_version,
            "lingframe_version": self.lingframe_version,
            "dependencies": self.dependencies,
        }

    @classmethod
    def capture(cls) -> "EnvironmentInfo":
        """Capture current environment."""
        deps = {}

        # Try to capture key dependency versions
        try:
            import spacy
            deps["spacy"] = spacy.__version__
        except ImportError:
            pass

        try:
            from vaderSentiment import vaderSentiment
            deps["vaderSentiment"] = getattr(vaderSentiment, "__version__", "unknown")
        except ImportError:
            pass

        try:
            import numpy
            deps["numpy"] = numpy.__version__
        except ImportError:
            pass

        return cls(
            python_version=sys.version,
            platform=platform.system(),
            platform_version=platform.version(),
            lingframe_version=LINGFRAME_VERSION,
            dependencies=deps,
        )


@dataclass
class AnalysisConfig:
    """Configuration snapshot for reproducibility."""
    modules: List[str]
    domain: Optional[str]
    schema_name: str
    options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "modules": self.modules,
            "domain": self.domain,
            "schema_name": self.schema_name,
            "options": self.options,
        }

    def to_json(self) -> str:
        """Serialize to JSON for storage."""
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AnalysisConfig":
        """Create from dictionary."""
        return cls(
            modules=data.get("modules", []),
            domain=data.get("domain"),
            schema_name=data.get("schema_name", "default"),
            options=data.get("options", {}),
        )


@dataclass
class ReproducibilityRecord:
    """
    Complete record for reproducing an analysis.

    Contains all information needed to verify or replicate results:
    - When the analysis was run
    - What configuration was used
    - What input was analyzed (via checksum)
    - What environment was used
    """
    run_id: str
    timestamp: str
    config: AnalysisConfig
    input_fingerprint: InputFingerprint
    environment: EnvironmentInfo
    output_checksum: Optional[str] = None
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "config": self.config.to_dict(),
            "input": self.input_fingerprint.to_dict(),
            "environment": self.environment.to_dict(),
            "output_checksum": self.output_checksum,
            "notes": self.notes,
        }

    def to_json(self) -> str:
        """Serialize to JSON for storage/sharing."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> "ReproducibilityRecord":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return cls(
            run_id=data["run_id"],
            timestamp=data["timestamp"],
            config=AnalysisConfig.from_dict(data["config"]),
            input_fingerprint=InputFingerprint(**data["input"]),
            environment=EnvironmentInfo(**data["environment"]),
            output_checksum=data.get("output_checksum"),
            notes=data.get("notes", ""),
        )

    def verify_input(self, text: str) -> bool:
        """Verify that input matches the recorded fingerprint."""
        current = InputFingerprint.from_text(text)
        return current.checksum == self.input_fingerprint.checksum

    def verify_output(self, output: Dict[str, Any]) -> bool:
        """Verify that output matches the recorded checksum."""
        if not self.output_checksum:
            return True  # No output checksum recorded
        current = _compute_output_checksum(output)
        return current == self.output_checksum


class ReproducibilityTracker:
    """
    Tracks analysis runs for reproducibility.

    Usage:
        tracker = ReproducibilityTracker()
        record = tracker.start_run(config, input_text)
        # ... run analysis ...
        tracker.finish_run(record, output)
        tracker.save(record, "analysis_record.json")
    """

    def __init__(self):
        self._run_counter = 0

    def start_run(
        self,
        config: AnalysisConfig,
        input_text: str,
        source_path: Optional[str] = None,
    ) -> ReproducibilityRecord:
        """
        Start tracking a new analysis run.

        Args:
            config: Analysis configuration
            input_text: Text being analyzed
            source_path: Optional source file path

        Returns:
            ReproducibilityRecord to be completed after analysis
        """
        self._run_counter += 1
        timestamp = datetime.now().isoformat()
        run_id = f"run_{timestamp.replace(':', '-').replace('.', '-')}_{self._run_counter}"

        return ReproducibilityRecord(
            run_id=run_id,
            timestamp=timestamp,
            config=config,
            input_fingerprint=InputFingerprint.from_text(input_text, source_path),
            environment=EnvironmentInfo.capture(),
        )

    def finish_run(
        self,
        record: ReproducibilityRecord,
        output: Dict[str, Any],
        notes: str = "",
    ) -> ReproducibilityRecord:
        """
        Complete a run record with output information.

        Args:
            record: The record from start_run
            output: Analysis output dictionary
            notes: Optional notes about the run

        Returns:
            Updated record with output checksum
        """
        record.output_checksum = _compute_output_checksum(output)
        record.notes = notes
        return record

    def save(
        self,
        record: ReproducibilityRecord,
        path: Path,
    ) -> Path:
        """Save record to JSON file."""
        path = Path(path)
        path.write_text(record.to_json(), encoding="utf-8")
        return path

    def load(self, path: Path) -> ReproducibilityRecord:
        """Load record from JSON file."""
        path = Path(path)
        return ReproducibilityRecord.from_json(path.read_text(encoding="utf-8"))


def _compute_output_checksum(output: Dict[str, Any]) -> str:
    """Compute deterministic checksum of analysis output."""
    # Sort keys for deterministic serialization
    json_str = json.dumps(output, sort_keys=True, default=str)
    return hashlib.sha256(json_str.encode("utf-8")).hexdigest()


def create_reproducibility_record(
    config_dict: Dict[str, Any],
    input_text: str,
    output: Optional[Dict[str, Any]] = None,
    source_path: Optional[str] = None,
) -> ReproducibilityRecord:
    """
    Convenience function to create a complete reproducibility record.

    Args:
        config_dict: Configuration dictionary
        input_text: Analyzed text
        output: Analysis output (optional)
        source_path: Source file path (optional)

    Returns:
        Complete ReproducibilityRecord
    """
    tracker = ReproducibilityTracker()
    config = AnalysisConfig.from_dict(config_dict)
    record = tracker.start_run(config, input_text, source_path)

    if output:
        record = tracker.finish_run(record, output)

    return record


def format_reproducibility_citation(record: ReproducibilityRecord) -> str:
    """
    Format a reproducibility record as a citation for papers.

    Returns a string suitable for inclusion in academic papers.
    """
    lines = [
        "Analysis Reproducibility Information",
        "=" * 40,
        f"Run ID: {record.run_id}",
        f"Timestamp: {record.timestamp}",
        f"LingFrame Version: {record.environment.lingframe_version}",
        f"Python Version: {record.environment.python_version.split()[0]}",
        "",
        "Configuration:",
        f"  Modules: {', '.join(record.config.modules)}",
        f"  Domain: {record.config.domain or 'None'}",
        f"  Schema: {record.config.schema_name}",
        "",
        "Input Verification:",
        f"  SHA-256: {record.input_fingerprint.checksum}",
        f"  Size: {record.input_fingerprint.byte_size} bytes",
        "",
    ]

    if record.output_checksum:
        lines.append(f"Output SHA-256: {record.output_checksum}")

    return "\n".join(lines)
