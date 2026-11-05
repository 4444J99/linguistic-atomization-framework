from __future__ import annotations

from dataclasses import dataclass
from typing import Any, NotRequired, TypedDict


@dataclass
class DriftResult:
    output_text: str
    diff_summary: dict[str, Any]


class VisualizationNode(TypedDict):
    id: str
    kind: str
    branch_id: str
    lineage_role: str
    parent_branch_id: str | None
    root_document_id: str | None
    event_index: int
    event_type: str
    phase: str | None
    mode: str
    created_at: Any
    metadata: dict[str, Any]


class VisualizationEdge(TypedDict):
    id: str
    source: str
    target: str
    type: str
    metadata: dict[str, Any]


class VisualizationSummary(TypedDict):
    event_count: int
    edge_count: int
    lineage_depth: int
    secondary_lineage_branch_count: int
    merge_secondary_edge_count: int


class MergeConflictSemantics(TypedDict, total=False):
    resolution: str
    strategy_effect: str
    inputs_identical: bool
    drops_non_selected_input: bool
    left_chars: int
    right_chars: int
    merged_chars: int
    left_words: int
    right_words: int
    merged_words: int
    shared_word_count: int
    left_only_word_count: int
    right_only_word_count: int
    common_prefix_chars: int
    common_suffix_chars: int
    note: NotRequired[str]
