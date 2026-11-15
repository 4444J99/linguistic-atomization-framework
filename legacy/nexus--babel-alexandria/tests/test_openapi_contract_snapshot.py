from __future__ import annotations

import json
from pathlib import Path

from nexus_babel.api.openapi_contract import normalized_openapi_contract


SNAPSHOT_PATH = Path(__file__).with_name("snapshots") / "openapi_contract_normalized.json"


def test_openapi_normalized_contract_snapshot(client):
    normalized = normalized_openapi_contract(client.app.openapi())
    assert SNAPSHOT_PATH.is_file(), f"Missing snapshot file: {SNAPSHOT_PATH}"
    expected = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    assert normalized == expected
