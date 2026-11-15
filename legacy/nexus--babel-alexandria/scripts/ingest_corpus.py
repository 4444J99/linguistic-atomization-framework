#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from fastapi.testclient import TestClient  # noqa: E402

from nexus_babel.config import Settings  # noqa: E402
from nexus_babel.main import create_app  # noqa: E402
from nexus_babel.services.seed_corpus import load_ingest_profile  # noqa: E402


def _safe_rel_or_abs(path: str, root: Path) -> str:
    raw = Path(path)
    candidate = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    root_resolved = root.resolve()
    try:
        candidate.relative_to(root_resolved)
    except ValueError as exc:
        raise ValueError(f"Profile source path escapes corpus_root and is not allowed: {path}") from exc
    return str(candidate)


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Provision and ingest a named seed corpus profile.")
    parser.add_argument("--profile", required=True, help="Named ingest profile from seed_corpus_registry.yaml (e.g. arc4n-seed)")
    parser.add_argument("--dry-run", action="store_true", help="Validate profile and print resolved inputs without ingesting")
    parser.add_argument("--skip-provision", action="store_true", help="Do not download/provision seed titles; use profile source_paths only")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    return parser.parse_args(argv)


def _json_dump(payload: dict[str, Any], pretty: bool) -> str:
    if pretty:
        return json.dumps(payload, indent=2, ensure_ascii=False)
    return json.dumps(payload, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = Settings()
    try:
        profile = load_ingest_profile(args.profile, settings.seed_registry_path)
        source_paths = [_safe_rel_or_abs(p, settings.corpus_root) for p in (profile.get("source_paths") or [])]
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    normalized_parse_options = {
        **(profile.get("parse_options") or {}),
        "atom_tracks": list(profile.get("atom_tracks") or []),
        "ingest_profile": profile["name"],
        "seed_registry_schema_version": profile.get("registry_schema_version"),
    }
    seed_titles = [str(v) for v in profile.get("seed_titles") or []]

    if args.dry_run:
        print(
            _json_dump(
                {
                    "status": "dry_run",
                    "profile": profile["name"],
                    "seed_titles": seed_titles,
                    "source_paths": source_paths,
                    "parse_options": normalized_parse_options,
                    "corpus_root": str(settings.corpus_root),
                },
                args.pretty,
            )
        )
        return 0

    app = create_app(settings_override=settings)
    with TestClient(app) as client:
        provision_results: list[dict[str, Any]] = []
        if seed_titles and not args.skip_provision:
            for title in seed_titles:
                result = client.app.state.seed_corpus_service.provision_seed_text(title)
                provision_results.append(result)
                if result.get("local_path"):
                    source_paths.append(str(Path(result["local_path"]).resolve()))

        source_paths = sorted(dict.fromkeys(source_paths))
        if not source_paths:
            print("ERROR: Profile resolved no source paths. Add seed_titles or source_paths to the profile.", file=sys.stderr)
            return 2

        headers = {"X-Nexus-API-Key": settings.bootstrap_operator_key}
        ingest_resp = client.post(
            "/api/v1/ingest/batch",
            headers=headers,
            json={
                "source_paths": source_paths,
                "modalities": [],
                "parse_options": normalized_parse_options,
                "atom_tracks": profile.get("atom_tracks") or [],
            },
        )
        if ingest_resp.status_code != 200:
            print(f"ERROR: ingest failed ({ingest_resp.status_code}): {ingest_resp.text}", file=sys.stderr)
            return 1
        ingest_payload = ingest_resp.json()

        job_resp = client.get(f"/api/v1/ingest/jobs/{ingest_payload['ingest_job_id']}", headers=headers)
        if job_resp.status_code != 200:
            print(f"ERROR: ingest job lookup failed ({job_resp.status_code}): {job_resp.text}", file=sys.stderr)
            return 1

        print(
            _json_dump(
                {
                    "status": "ok",
                    "profile": profile["name"],
                    "provisioned": provision_results,
                    "ingest": ingest_payload,
                    "job": job_resp.json(),
                },
                args.pretty,
            )
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
