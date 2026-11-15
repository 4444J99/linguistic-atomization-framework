from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace

from nexus_babel.services.evolution_replay import compress_snapshot, decompress_snapshot, replay_lineage_text
from nexus_babel.services.evolution_types import DriftResult


@dataclass
class _EventStub:
    event_type: str
    event_payload: dict


@dataclass
class _CheckpointStub:
    event_index: int
    snapshot_compressed: str


@dataclass
class _BranchStub:
    root_document_id: str | None


def test_snapshot_compress_decompress_round_trip():
    snapshot = {"current_text": "alpha", "phase": "peak", "nested": {"x": 1}}
    payload = compress_snapshot(snapshot)
    decoded = decompress_snapshot(payload)
    assert decoded == snapshot


def test_replay_lineage_text_checkpoint_and_full_replay_match():
    branch = _BranchStub(root_document_id="doc-1")
    lineage_nodes = [SimpleNamespace(id="b1")]
    events = [
        _EventStub("append", {"token": "A"}),
        _EventStub("append", {"token": "B"}),
        _EventStub("append", {"token": "C"}),
    ]

    def _apply(text: str, event_type: str, event_payload: dict) -> DriftResult:
        assert event_type == "append"
        return DriftResult(output_text=text + str(event_payload["token"]), diff_summary={"event": event_type})

    full_text, _, _ = replay_lineage_text(
        session=None,  # type: ignore[arg-type]
        branch=branch,  # type: ignore[arg-type]
        use_checkpoints=False,
        lineage_fn=lambda _session, _branch: lineage_nodes,
        collect_events_fn=lambda _session, _lineage: events,  # type: ignore[return-value]
        resolve_root_text_fn=lambda _session, _doc_id: "root-",
        latest_checkpoint_fn=lambda _session, _lineage: None,
        decompress_snapshot_fn=decompress_snapshot,
        apply_event_fn=_apply,
    )

    checkpoint = _CheckpointStub(event_index=2, snapshot_compressed=compress_snapshot({"current_text": "root-AB"}))
    checkpoint_text, _, _ = replay_lineage_text(
        session=None,  # type: ignore[arg-type]
        branch=branch,  # type: ignore[arg-type]
        use_checkpoints=True,
        lineage_fn=lambda _session, _branch: lineage_nodes,
        collect_events_fn=lambda _session, _lineage: events,  # type: ignore[return-value]
        resolve_root_text_fn=lambda _session, _doc_id: "root-",
        latest_checkpoint_fn=lambda _session, _lineage: checkpoint,  # type: ignore[return-value]
        decompress_snapshot_fn=decompress_snapshot,
        apply_event_fn=_apply,
    )

    assert full_text == checkpoint_text == "root-ABC"


def test_replay_lineage_text_clips_checkpoint_index_to_event_count():
    branch = _BranchStub(root_document_id="doc-1")
    lineage_nodes = [SimpleNamespace(id="b1")]
    events = [_EventStub("append", {"token": "A"})]
    checkpoint = _CheckpointStub(event_index=999, snapshot_compressed=compress_snapshot({"current_text": "prefilled"}))
    calls = {"count": 0}

    def _apply(text: str, event_type: str, event_payload: dict) -> DriftResult:
        calls["count"] += 1
        return DriftResult(output_text=text + str(event_payload["token"]), diff_summary={"event": event_type})

    text, _, _ = replay_lineage_text(
        session=None,  # type: ignore[arg-type]
        branch=branch,  # type: ignore[arg-type]
        use_checkpoints=True,
        lineage_fn=lambda _session, _branch: lineage_nodes,
        collect_events_fn=lambda _session, _lineage: events,  # type: ignore[return-value]
        resolve_root_text_fn=lambda _session, _doc_id: "root-",
        latest_checkpoint_fn=lambda _session, _lineage: checkpoint,  # type: ignore[return-value]
        decompress_snapshot_fn=decompress_snapshot,
        apply_event_fn=_apply,
    )

    assert text == "prefilled"
    assert calls["count"] == 0
