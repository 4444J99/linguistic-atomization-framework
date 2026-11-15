from __future__ import annotations

import hashlib
from typing import Any, Callable

from sqlalchemy.orm import Session

from nexus_babel.models import Branch


def find_lca(
    session: Session,
    left_branch: Branch,
    right_branch: Branch,
    *,
    lineage_fn: Callable[[Session, Branch], list[Branch]],
) -> Branch | None:
    left_lineage = lineage_fn(session, left_branch)
    right_lineage = lineage_fn(session, right_branch)

    left_by_id = {branch.id: branch for branch in left_lineage}
    lca: Branch | None = None
    for branch in right_lineage:
        if branch.id in left_by_id:
            lca = left_by_id[branch.id]
    return lca


def merge_texts(left_text: str, right_text: str, strategy: str) -> str:
    if strategy == "left_wins":
        return left_text
    if strategy == "right_wins":
        return right_text
    if strategy == "interleave":
        left_words = left_text.split()
        right_words = right_text.split()
        merged: list[str] = []
        for idx in range(max(len(left_words), len(right_words))):
            if idx < len(left_words):
                merged.append(left_words[idx])
            if idx < len(right_words):
                merged.append(right_words[idx])
        return " ".join(merged)
    raise ValueError(f"Unsupported merge strategy: {strategy}")


def build_merge_conflict_semantics(
    *,
    left_text: str,
    right_text: str,
    merged_text: str,
    strategy: str,
) -> dict[str, Any]:
    left_words = left_text.split()
    right_words = right_text.split()
    merged_words = merged_text.split()
    left_word_set = set(left_words)
    right_word_set = set(right_words)
    left_hash = hashlib.sha256(left_text.encode("utf-8")).hexdigest()
    right_hash = hashlib.sha256(right_text.encode("utf-8")).hexdigest()
    inputs_identical = left_hash == right_hash

    if inputs_identical:
        resolution = "identical_inputs"
    elif strategy == "left_wins":
        resolution = "left_preferred"
    elif strategy == "right_wins":
        resolution = "right_preferred"
    else:
        resolution = "interleaved_union"

    return {
        "resolution": resolution,
        "strategy_effect": {
            "left_wins": "preserve_left",
            "right_wins": "preserve_right",
            "interleave": "word_interleave",
        }.get(strategy, "unknown"),
        "inputs_identical": inputs_identical,
        "drops_non_selected_input": strategy in {"left_wins", "right_wins"} and not inputs_identical,
        "left_chars": len(left_text),
        "right_chars": len(right_text),
        "merged_chars": len(merged_text),
        "left_words": len(left_words),
        "right_words": len(right_words),
        "merged_words": len(merged_words),
        "shared_word_count": len(left_word_set & right_word_set),
        "left_only_word_count": len(left_word_set - right_word_set),
        "right_only_word_count": len(right_word_set - left_word_set),
        "common_prefix_chars": common_prefix_chars(left_text, right_text),
        "common_suffix_chars": common_suffix_chars(left_text, right_text),
    }


def common_prefix_chars(left: str, right: str) -> int:
    count = 0
    for left_char, right_char in zip(left, right):
        if left_char != right_char:
            break
        count += 1
    return count


def common_suffix_chars(left: str, right: str) -> int:
    count = 0
    for left_char, right_char in zip(reversed(left), reversed(right)):
        if left_char != right_char:
            break
        count += 1
    return count


def simple_distance(left: str, right: str) -> int:
    length = max(len(left), len(right))
    distance = 0
    for idx in range(length):
        left_char = left[idx] if idx < len(left) else ""
        right_char = right[idx] if idx < len(right) else ""
        if left_char != right_char:
            distance += 1
    return distance
