from __future__ import annotations

from dataclasses import dataclass

from nexus_babel.services.evolution_merge import (
    build_merge_conflict_semantics,
    common_prefix_chars,
    common_suffix_chars,
    find_lca,
    merge_texts,
    simple_distance,
)


@dataclass
class _BranchStub:
    id: str
    parent_branch_id: str | None = None


def test_merge_texts_strategies():
    assert merge_texts("left", "right", "left_wins") == "left"
    assert merge_texts("left", "right", "right_wins") == "right"
    assert merge_texts("one two", "alpha beta gamma", "interleave") == "one alpha two beta gamma"


def test_merge_conflict_semantics_resolution_labels_and_keyset():
    identical = build_merge_conflict_semantics(
        left_text="same text",
        right_text="same text",
        merged_text="same text",
        strategy="left_wins",
    )
    assert identical["resolution"] == "identical_inputs"

    left_preferred = build_merge_conflict_semantics(
        left_text="left value",
        right_text="right value",
        merged_text="left value",
        strategy="left_wins",
    )
    assert left_preferred["resolution"] == "left_preferred"
    assert left_preferred["strategy_effect"] == "preserve_left"

    right_preferred = build_merge_conflict_semantics(
        left_text="left value",
        right_text="right value",
        merged_text="right value",
        strategy="right_wins",
    )
    assert right_preferred["resolution"] == "right_preferred"

    interleaved = build_merge_conflict_semantics(
        left_text="one two",
        right_text="alpha beta",
        merged_text="one alpha two beta",
        strategy="interleave",
    )
    assert interleaved["resolution"] == "interleaved_union"
    assert {
        "common_prefix_chars",
        "common_suffix_chars",
        "shared_word_count",
        "left_only_word_count",
        "right_only_word_count",
    }.issubset(interleaved.keys())


def test_prefix_suffix_and_simple_distance_helpers():
    assert common_prefix_chars("alphabet", "alphaX") == 5
    assert common_suffix_chars("stone.txt", "note.txt") == 5
    assert simple_distance("abc", "axcd") == 2


def test_find_lca_uses_lineage_function():
    root = _BranchStub("root")
    left = _BranchStub("left", parent_branch_id="root")
    right = _BranchStub("right", parent_branch_id="root")
    other_root = _BranchStub("other-root")

    lineage_map = {
        "left": [root, left],
        "right": [root, right],
        "other-root": [other_root],
    }

    def _lineage(_session, branch):
        return lineage_map[branch.id]

    assert find_lca(None, left, right, lineage_fn=_lineage).id == "root"  # type: ignore[arg-type]
    assert find_lca(None, left, other_root, lineage_fn=_lineage) is None  # type: ignore[arg-type]
