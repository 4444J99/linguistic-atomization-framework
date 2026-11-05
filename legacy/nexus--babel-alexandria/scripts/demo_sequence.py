#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
from textwrap import dedent
from typing import Any

import httpx


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nexus_babel.services.text_utils import atomize_text_rich  # noqa: E402


ODYSSEY_EXCERPT = dedent(
    """
    Sing to me of the man, Muse, the man of twists and turns
    driven time and again off course, once he had plundered
    the hallowed heights of Troy.
    """
).strip()

PARADISE_LOST_EXCERPT = dedent(
    """
    Of Man's first disobedience, and the fruit
    Of that forbidden tree whose mortal taste
    Brought death into the World, and all our woe.
    """
).strip()


def _print_step(n: int, title: str) -> None:
    print(f"\n{'=' * 78}\nSTEP {n}: {title}\n{'=' * 78}")


def _preview(payload: Any, *, limit: int = 1200) -> str:
    text = json.dumps(payload, indent=2, ensure_ascii=False, default=str)
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... [truncated]"


def _request(client: httpx.Client, method: str, path: str, **kwargs) -> dict[str, Any]:
    resp = client.request(method, path, **kwargs)
    resp.raise_for_status()
    if resp.content:
        return resp.json()
    return {}


def _write_excerpt(temp_dir: Path, name: str, content: str) -> Path:
    path = temp_dir / name
    path.write_text(content, encoding="utf-8")
    return path


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a scripted Alexandria-Babel demo sequence against a running API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL (default: %(default)s)")
    parser.add_argument(
        "--api-key",
        default=os.environ.get("NEXUS_BOOTSTRAP_OPERATOR_KEY", "nexus-dev-operator-key"),
        help="Operator API key (default: NEXUS_BOOTSTRAP_OPERATOR_KEY or nexus-dev-operator-key)",
    )
    parser.add_argument("--viewer-key", default=os.environ.get("NEXUS_BOOTSTRAP_VIEWER_KEY", "nexus-dev-viewer-key"))
    parser.add_argument("--researcher-key", default=os.environ.get("NEXUS_BOOTSTRAP_RESEARCHER_KEY", "nexus-dev-researcher-key"))
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout seconds")
    parser.add_argument("--work-dir", default=None, help="Optional working directory for temporary demo excerpts")
    parser.add_argument("--dry-run", action="store_true", help="Print planned steps and exit without API calls")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    if args.dry_run:
        print(_preview({
            "base_url": args.base_url,
            "steps": [
                "Authenticate /auth/whoami",
                "Ingest Odyssey excerpt",
                "Inspect document + atomization provenance",
                "Preview glyph-seed metadata",
                "Run 9-layer analyze",
                "Run governance evaluation",
                "Branch evolution",
                "Ingest Paradise Lost excerpt",
                "Remix compose (glyph_collide)",
                "Timeline + compare climax",
            ],
            "docs_url": f"{args.base_url.rstrip('/')}/docs",
        }))
        return 0

    headers_operator = {"X-Nexus-API-Key": args.api_key}
    headers_viewer = {"X-Nexus-API-Key": args.viewer_key}
    headers_researcher = {"X-Nexus-API-Key": args.researcher_key}

    temp_root_ctx = None
    if args.work_dir:
        temp_dir = Path(args.work_dir).resolve()
        temp_dir.mkdir(parents=True, exist_ok=True)
    else:
        demo_tmp_parent = REPO_ROOT / "artifacts" / "prix-ars-2026"
        demo_tmp_parent.mkdir(parents=True, exist_ok=True)
        temp_root_ctx = tempfile.TemporaryDirectory(prefix="nexus_babel_demo_", dir=demo_tmp_parent)
        temp_dir = Path(temp_root_ctx.name)

    try:
        with httpx.Client(base_url=args.base_url.rstrip("/"), timeout=args.timeout) as client:
            _print_step(1, "Authenticate")
            whoami = _request(client, "GET", "/api/v1/auth/whoami", headers=headers_operator)
            print(_preview(whoami))
            print(f"\nFastAPI docs for recording: {args.base_url.rstrip('/')}/docs")

            _print_step(2, "Provision Seed Text (Odyssey excerpt via local ingest file)")
            odyssey_path = _write_excerpt(temp_dir, "odyssey_excerpt.txt", ODYSSEY_EXCERPT)
            ingest_1 = _request(
                client,
                "POST",
                "/api/v1/ingest/batch",
                headers=headers_operator,
                json={
                    "source_paths": [str(odyssey_path)],
                    "atom_tracks": ["literary", "glyphic_seed"],
                    "parse_options": {"atomize": True, "ingest_profile": "demo-odyssey-excerpt"},
                },
            )
            print(_preview(ingest_1))
            job_1 = _request(client, "GET", f"/api/v1/ingest/jobs/{ingest_1['ingest_job_id']}", headers=headers_viewer)
            odyssey_doc_id = job_1["files"][0]["document_id"]

            _print_step(3, "Show Atomization Breakdown (document -> paragraph -> sentence -> word -> glyph-seed)")
            doc_1 = _request(client, "GET", f"/api/v1/documents/{odyssey_doc_id}", headers=headers_viewer)
            print(_preview({
                "document_id": odyssey_doc_id,
                "atom_count": doc_1.get("atom_count"),
                "graph_projection_status": doc_1.get("graph_projection_status"),
                "atomization": (doc_1.get("provenance") or {}).get("atomization"),
                "segments": (doc_1.get("provenance") or {}).get("segments"),
            }))

            _print_step(4, "Inspect Glyph-Seeds With Rich Metadata (local preview for screen readability)")
            glyphs = atomize_text_rich(ODYSSEY_EXCERPT)["glyph-seed"][:8]
            print(_preview([g.model_dump() for g in glyphs], limit=1800))

            _print_step(5, "Run 9-Layer Plexus Analysis")
            analyze = _request(
                client,
                "POST",
                "/api/v1/analyze",
                headers=headers_operator,
                json={"document_id": odyssey_doc_id, "mode": "PUBLIC"},
            )
            print(_preview({
                "analysis_run_id": analyze.get("analysis_run_id"),
                "layers": sorted((analyze.get("layers") or {}).keys()),
                "hypergraph_ids": analyze.get("hypergraph_ids"),
            }))

            _print_step(6, "Governance Evaluation")
            gov = _request(
                client,
                "POST",
                "/api/v1/governance/evaluate",
                headers=headers_operator,
                json={"candidate_output": "We preserve memory through language and symbol.", "mode": "PUBLIC"},
            )
            print(_preview(gov))

            _print_step(7, "Branch Evolution")
            evolve = _request(
                client,
                "POST",
                "/api/v1/evolve/branch",
                headers=headers_researcher,
                json={
                    "root_document_id": odyssey_doc_id,
                    "event_type": "natural_drift",
                    "event_payload": {"seed": 7},
                    "mode": "PUBLIC",
                },
            )
            print(_preview(evolve))
            left_branch_id = evolve["new_branch_id"]

            _print_step(8, "Provision Second Text (Paradise Lost excerpt via local ingest file)")
            milton_path = _write_excerpt(temp_dir, "paradise_lost_excerpt.txt", PARADISE_LOST_EXCERPT)
            ingest_2 = _request(
                client,
                "POST",
                "/api/v1/ingest/batch",
                headers=headers_operator,
                json={
                    "source_paths": [str(milton_path)],
                    "atom_tracks": ["literary", "glyphic_seed"],
                    "parse_options": {"atomize": True, "ingest_profile": "demo-paradise-lost-excerpt"},
                },
            )
            print(_preview(ingest_2))
            job_2 = _request(client, "GET", f"/api/v1/ingest/jobs/{ingest_2['ingest_job_id']}", headers=headers_viewer)
            milton_doc_id = job_2["files"][0]["document_id"]

            _print_step(9, "Remix Compose (glyph_collide)")
            remix = _request(
                client,
                "POST",
                "/api/v1/remix/compose",
                headers=headers_operator,
                json={
                    "source_document_id": odyssey_doc_id,
                    "target_document_id": milton_doc_id,
                    "strategy": "glyph_collide",
                    "seed": 42,
                    "atom_levels": ["glyph-seed"],
                    "create_branch": True,
                    "persist_artifact": True,
                    "mode": "PUBLIC",
                },
            )
            print(_preview({
                "remix_artifact_id": remix.get("remix_artifact_id"),
                "text_hash": remix.get("text_hash"),
                "new_branch_id": remix.get("new_branch_id"),
                "event_id": remix.get("event_id"),
                "source_atom_refs_preview": remix.get("source_atom_refs", [])[:6],
                "remixed_text_preview": (remix.get("remixed_text") or "")[:300],
            }, limit=2200))
            right_branch_id = remix["new_branch_id"]

            _print_step(10, "Branch Timeline + Remix Compare Climax")
            timeline = _request(client, "GET", f"/api/v1/branches/{right_branch_id}/timeline", headers=headers_viewer)
            compare = _request(client, "GET", f"/api/v1/branches/{left_branch_id}/compare/{right_branch_id}", headers=headers_viewer)
            print(_preview({
                "timeline_event_count": len(timeline.get("events", [])),
                "last_event": (timeline.get("events") or [])[-1] if timeline.get("events") else None,
                "compare": compare,
            }, limit=2500))

        print("\nDemo sequence completed successfully.")
        return 0
    except httpx.HTTPStatusError as exc:
        print(f"HTTP ERROR {exc.response.status_code} on {exc.request.method} {exc.request.url}: {exc.response.text}", file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - CLI safety
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if temp_root_ctx is not None:
            temp_root_ctx.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
