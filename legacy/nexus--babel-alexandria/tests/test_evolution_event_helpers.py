from __future__ import annotations

import pytest

from nexus_babel.services.evolution_events import (
    GLYPH_POOL,
    MERGE_STRATEGIES,
    NATURAL_MAP,
    PHASES,
    REVERSE_NATURAL_MAP,
    apply_event,
    validate_event_payload,
)


def _apply(text: str, event_type: str, payload: dict):
    return apply_event(
        text,
        event_type,
        payload,
        natural_map=NATURAL_MAP,
        reverse_natural_map=REVERSE_NATURAL_MAP,
        glyph_pool=GLYPH_POOL,
    )


def _validate(event_type: str, payload: dict):
    return validate_event_payload(event_type, payload, phases=PHASES, merge_strategies=MERGE_STRATEGIES)


def test_apply_event_is_deterministic_for_seeded_mutation_and_reverse_drift():
    mutation_1 = _apply("alpha beta gamma delta", "synthetic_mutation", {"seed": 7, "mutation_rate": 0.6})
    mutation_2 = _apply("alpha beta gamma delta", "synthetic_mutation", {"seed": 7, "mutation_rate": 0.6})
    assert mutation_1.output_text == mutation_2.output_text
    assert mutation_1.diff_summary == mutation_2.diff_summary

    reverse_1 = _apply("þe phun", "reverse_drift", {"seed": 2})
    reverse_2 = _apply("þe phun", "reverse_drift", {"seed": 2})
    assert reverse_1.output_text == reverse_2.output_text


def test_validate_event_payload_enforces_mutation_bounds_and_phase_membership():
    with pytest.raises(ValueError, match="mutation_rate must be between 0.0 and 1.0"):
        _validate("synthetic_mutation", {"mutation_rate": 1.2})

    with pytest.raises(ValueError, match="phase must be one of"):
        _validate("phase_shift", {"phase": "entropy"})


def test_validate_event_payload_normalizes_merge_payload():
    payload = _validate(
        "merge",
        {
            "strategy": "  INTERLEAVE  ",
            "merged_text": 123,
            "left_text_hash": 42,
            "right_text_hash": None,
            "conflict_semantics": {"resolution": "interleaved_union"},
        },
    )

    assert payload["strategy"] == "interleave"
    assert payload["merged_text"] == "123"
    assert payload["left_text_hash"] == "42"
    assert "right_text_hash" in payload and payload["right_text_hash"] is None
    assert payload["conflict_semantics"]["resolution"] == "interleaved_union"
    assert payload["seed"] == 0


def test_validate_event_payload_rejects_non_object_merge_conflict_semantics():
    with pytest.raises(ValueError, match="conflict_semantics must be an object"):
        _validate("merge", {"strategy": "left_wins", "conflict_semantics": []})


def test_apply_event_merge_diff_summary_contains_contract_keys():
    result = _apply(
        "left text",
        "merge",
        {
            "merged_text": "merged text",
            "strategy": "interleave",
            "left_branch_id": "left-1",
            "right_branch_id": "right-1",
            "lca_branch_id": "lca-1",
            "left_text_hash": "abc",
            "right_text_hash": "def",
            "conflict_semantics": {"resolution": "interleaved_union"},
        },
    )

    assert result.output_text == "merged text"
    assert {
        "event",
        "strategy",
        "left_branch_id",
        "right_branch_id",
        "lca_branch_id",
        "left_text_hash",
        "right_text_hash",
        "conflict_semantics",
        "before_chars",
        "after_chars",
    }.issubset(result.diff_summary.keys())
    assert result.diff_summary["event"] == "merge"
