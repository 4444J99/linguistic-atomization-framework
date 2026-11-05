#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def main() -> None:
    try:
        from nexus_babel.api.openapi_contract import default_snapshot_path, normalized_openapi_contract
        from nexus_babel.config import Settings
        from nexus_babel.main import create_app
    except ModuleNotFoundError as exc:
        missing = getattr(exc, "name", "dependency")
        raise SystemExit(
            f"Missing runtime dependency '{missing}'. Run this script with the project environment "
            "(for example: .venv/bin/python scripts/generate_openapi_contract_snapshot.py)."
        ) from exc

    parser = argparse.ArgumentParser(description="Regenerate the normalized /api/v1 OpenAPI contract snapshot.")
    parser.add_argument(
        "--output",
        help="Snapshot output path (defaults to tests/snapshots/openapi_contract_normalized.json)",
    )
    args = parser.parse_args()

    repo_root = REPO_ROOT
    output_path = Path(args.output).resolve() if args.output else default_snapshot_path(repo_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="openapi-snapshot-") as tmp_dir:
        tmp_root = Path(tmp_dir)
        settings = Settings(
            environment="test",
            database_url=f"sqlite:///{tmp_root / 'snapshot.db'}",
            corpus_root=tmp_root / "corpus",
            object_storage_root=tmp_root / "object_storage",
            schema_management_mode="off",
            bootstrap_keys_enabled=False,
            neo4j_uri=None,
            neo4j_username=None,
            neo4j_password=None,
        )
        app = create_app(settings)
        normalized = normalized_openapi_contract(app.openapi())

    output_path.write_text(json.dumps(normalized, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    print(output_path)


if __name__ == "__main__":
    main()
