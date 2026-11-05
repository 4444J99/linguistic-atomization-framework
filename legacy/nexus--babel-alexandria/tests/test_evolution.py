from __future__ import annotations

import pytest

from nexus_babel.services.evolution import EvolutionService


def test_reverse_drift_payload_default_seed():
    service = EvolutionService()
    payload = service._validate_event_payload("reverse_drift", {})
    assert payload == {"seed": 0}


def test_reverse_drift_basic_restores_patterns():
    service = EvolutionService()
    source = "the phone"
    drifted = service._apply_event(source, "natural_drift", {"seed": 0})
    restored = service._apply_event(drifted.output_text, "reverse_drift", {"seed": 0})

    assert "th" in restored.output_text.lower()
    assert "ph" in restored.output_text.lower()
    assert restored.diff_summary["event"] == "reverse_drift"
    assert restored.diff_summary["reversals"] >= 1


def test_reverse_drift_lossy():
    service = EvolutionService()
    restored = service._apply_event("fun", "reverse_drift", {"seed": 0})
    assert restored.output_text.lower() == "phun"


@pytest.mark.parametrize(
    ("old", "new"),
    list(EvolutionService.REVERSE_NATURAL_MAP.items()),
)
def test_reverse_drift_all_reverse_map_entries(old: str, new: str):
    service = EvolutionService()
    service.REVERSE_NATURAL_MAP = {old: new}
    out = service._apply_event(f"x{old}y", "reverse_drift", {"seed": 0})
    assert new.lower() in out.output_text.lower()


def test_multi_evolve_empty_events_raises():
    service = EvolutionService()
    with pytest.raises(ValueError, match="events must not be empty"):
        service.multi_evolve(  # type: ignore[arg-type]
            session=None,
            parent_branch_id=None,
            root_document_id="doc-id",
            events=[],
            mode="PUBLIC",
        )
