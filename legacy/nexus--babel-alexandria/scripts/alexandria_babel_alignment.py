#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SOURCE_FILES = [
    "0469-arc4n-seed-texts-and-atomization-2.md",
    "Nexus_Bable-Alexandria.md",
]

ROUTE_RE = re.compile(r'@router\.(?:get|post|put|patch|delete)\("([^"]+)"')
ENDPOINT_RE = re.compile(r"/api/v1/[A-Za-z0-9/_{}-]+")
SUGGESTION_RE = re.compile(
    r"(would you like|should i|should we|which prototype|next step|first action|opening goals|closing prompt|prototype|build|implement|launch|create|draft|track|save receipt|must model|engine module)",
    re.IGNORECASE,
)
CORE_FUNCTION_RE = re.compile(r"((?:PHON|MORPH|SYNT|SEM|PRAG|DISC|SOCIO|ICON|RHET|SEMI|META|VIZ|SAFE|ALIGN|VIS|API)\\?_[0-9]{3})")


IMPLEMENTED_KEYWORDS: dict[str, str] = {
    "prototype tracker": "docs/alexandria_babel/Prototype_Tracker.md",
    "protocol tracker": "docs/alexandria_babel/Protocol_Tracker.md",
    "save receipt": "docs/alexandria_babel/Save_Receipt_2026-02-18.md",
    "natural drift": "src/nexus_babel/services/evolution.py",
    "synthetic drift": "src/nexus_babel/services/evolution.py",
    "synthetic mutation": "src/nexus_babel/services/evolution.py",
    "phase cycles": "src/nexus_babel/services/evolution.py",
    "phase shift": "src/nexus_babel/services/evolution.py",
    "glyph fusion": "src/nexus_babel/services/evolution.py",
}


PLAN_BUCKETS: list[tuple[str, str, list[str]]] = [
    ("AB-PLAN-01", "Corpus Atomization + Remix Library", ["atomization", "seed text", "word", "sentence", "paragraph", "remix"]),
    ("AB-PLAN-02", "Evolution + Glyphic Engines", ["drift", "mutation", "phase", "glyph", "spiral", "songbirth", "fusion"]),
    ("AB-PLAN-03", "Explorer UX + Interaction", ["ux", "portal", "wireframe", "visualization", "user agency", "thread_ux"]),
    ("AB-PLAN-04", "Governance + Artifact Ops", ["tracker", "protocol", "receipt", "approval", "archive", "sys_manage"]),
    ("AB-PLAN-05", "Academic + Funding", ["academic", "grant", "funding", "institution", "outreach"]),
    ("AB-PLAN-06", "Mythic + Cultural Layer", ["mythic", "babel", "rebirth", "ritual", "civilizations", "sung"]),
]

SCAFFOLD_TEMPLATES: dict[str, str] = {
    "Thread_Plan_UX.md": """# Thread Plan: UX

## Intent
- Capture interaction and explorer UX workstreams for Alexandria-Babel.

## Current Focus
- Define user-facing thread/cartridge flows.

## Next Actions
- Record concrete UX slices and dependencies.
""",
    "Thread_Plan_Academic.md": """# Thread Plan: Academic

## Intent
- Track scholarship-facing outputs, evidence, and framing for Alexandria-Babel.

## Current Focus
- Maintain juror/reviewer-readable documentation and evidence links.

## Next Actions
- Add publication, citation, and narrative milestones.
""",
    "Thread_Plan_Funding.md": """# Thread Plan: Funding

## Intent
- Track grants, submissions, and sponsor-facing packaging for Alexandria-Babel.

## Current Focus
- Maintain deadlines, assets, and proposal requirements.

## Next Actions
- Add funding targets, required assets, and submission status.
""",
}


@dataclass
class SourceDigest:
    path: str
    line_count: int
    char_count: int
    sha256: str


def _normalize_path_template(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


def _load_routes(repo_root: Path) -> set[str]:
    routes_path = repo_root / "src/nexus_babel/api/routes.py"
    text = routes_path.read_text(encoding="utf-8", errors="ignore")
    routes = set()
    for match in ROUTE_RE.finditer(text):
        route = match.group(1)
        if route.startswith("/api/v1/"):
            routes.add(route)
        else:
            routes.add(f"/api/v1{route}")
    return routes


def _digest(path: Path) -> SourceDigest:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return SourceDigest(
        path=path.name,
        line_count=text.count("\n") + 1,
        char_count=len(text),
        sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )


def _is_suggestion_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped.startswith("```"):
        return False
    if re.match(r"^- \*\*(ID|Alias|Created|Updated|Model|Nodes|Tags|First Prompt)\*\*:", stripped):
        return False
    if re.match(r"^aliases:|^tags:|^title:|^linter-yaml-title-alias:", stripped):
        return False
    if CORE_FUNCTION_RE.search(stripped):
        return True
    if ENDPOINT_RE.search(stripped):
        return True
    starts_structural = stripped.startswith(("-", ">", "|", "1.", "2.", "3.", "4.", "5."))
    return bool(SUGGESTION_RE.search(stripped) and (starts_structural or len(stripped) <= 220))


def _extract_entries(repo_root: Path, routes: set[str]) -> tuple[list[dict[str, Any]], list[SourceDigest]]:
    entries: list[dict[str, Any]] = []
    digests: list[SourceDigest] = []
    seen: set[str] = set()
    normalized_routes = {_normalize_path_template(route) for route in routes}

    for source_name in SOURCE_FILES:
        path = repo_root / source_name
        text = path.read_text(encoding="utf-8", errors="ignore")
        digests.append(_digest(path))
        for line_no, line in enumerate(text.splitlines(), start=1):
            if not _is_suggestion_line(line):
                continue
            stripped = line.strip()
            normalized_key = re.sub(r"\s+", " ", stripped.lower())
            if normalized_key in seen:
                continue
            seen.add(normalized_key)

            status = "planned"
            evidence = ""
            bucket_id = "AB-PLAN-01"
            bucket_name = "Corpus Atomization + Remix Library"

            endpoint_match = ENDPOINT_RE.search(stripped)
            if endpoint_match:
                endpoint = endpoint_match.group(0)
                endpoint_norm = _normalize_path_template(endpoint)
                if endpoint in routes or endpoint_norm in normalized_routes:
                    status = "implemented"
                    evidence = "src/nexus_babel/api/routes.py"
                else:
                    status = "planned"

            lowered = stripped.lower()
            for keyword, keyword_evidence in IMPLEMENTED_KEYWORDS.items():
                if keyword in lowered:
                    status = "implemented"
                    evidence = keyword_evidence
                    break

            for candidate_id, candidate_name, keywords in PLAN_BUCKETS:
                if any(k in lowered for k in keywords):
                    bucket_id = candidate_id
                    bucket_name = candidate_name
                    break

            entry_id = hashlib.sha1(f"{source_name}:{line_no}:{stripped}".encode("utf-8")).hexdigest()[:12]
            entries.append(
                {
                    "id": f"ab-{entry_id}",
                    "source_file": source_name,
                    "line": line_no,
                    "text": stripped,
                    "status": status,
                    "plan_bucket_id": bucket_id,
                    "plan_bucket_name": bucket_name,
                    "evidence": evidence or ("planned via " + bucket_id),
                }
            )

    entries.sort(key=lambda item: (item["source_file"], item["line"], item["id"]))
    return entries, digests


def _write_markdown(
    out_path: Path,
    generated_at: str,
    entries: list[dict[str, Any]],
    digests: list[SourceDigest],
) -> None:
    implemented = sum(1 for item in entries if item["status"] == "implemented")
    planned = sum(1 for item in entries if item["status"] == "planned")

    lines: list[str] = []
    lines.append("# Alexandria-Babel Feature/Use-Case Matrix")
    lines.append("")
    lines.append(f"- Generated: `{generated_at}`")
    lines.append(f"- Scope: `{SOURCE_FILES[0]}`, `{SOURCE_FILES[1]}`")
    lines.append(f"- Suggestions extracted: `{len(entries)}`")
    lines.append(f"- Status split: `implemented={implemented}`, `planned={planned}`")
    lines.append("")
    lines.append("## Source Digests")
    lines.append("")
    lines.append("| File | Lines | Chars | SHA256 |")
    lines.append("|---|---:|---:|---|")
    for digest in digests:
        lines.append(f"| `{digest.path}` | {digest.line_count} | {digest.char_count} | `{digest.sha256}` |")
    lines.append("")
    lines.append("## Plan Buckets")
    lines.append("")
    lines.append("| ID | Name |")
    lines.append("|---|---|")
    for bucket_id, bucket_name, _ in PLAN_BUCKETS:
        lines.append(f"| `{bucket_id}` | {bucket_name} |")
    lines.append("")
    lines.append("## Suggestion Ledger")
    lines.append("")
    lines.append("| ID | Source | Line | Status | Bucket | Evidence | Text |")
    lines.append("|---|---|---:|---|---|---|---|")
    for item in entries:
        safe_text = item["text"].replace("|", "\\|")
        safe_evidence = item["evidence"].replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{item['source_file']}` | {item['line']} | `{item['status']}` | `{item['plan_bucket_id']}` | `{safe_evidence}` | {safe_text} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def ensure_scaffold(out_dir: Path) -> dict[str, Any]:
    created: list[str] = []
    existing: list[str] = []
    for filename, content in SCAFFOLD_TEMPLATES.items():
        path = out_dir / filename
        if path.exists():
            existing.append(filename)
            continue
        path.write_text(content, encoding="utf-8")
        created.append(filename)
    return {"created": created, "existing": existing, "required": sorted(SCAFFOLD_TEMPLATES)}


def build_scaffold_index(out_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    for path in sorted(out_dir.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file():
            continue
        if path.name == "index.md":
            continue
        stat = path.stat()
        entries.append(
            {
                "name": path.name,
                "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "size_bytes": stat.st_size,
            }
        )

    lines = ["# Alexandria-Babel Cartridge Index", "", f"- Generated: `{datetime.now(timezone.utc).isoformat()}`", ""]
    lines.append("| File | Modified (UTC) | Size (bytes) |")
    lines.append("|---|---|---:|")
    for entry in entries:
        lines.append(f"| `{entry['name']}` | `{entry['mtime_utc']}` | {entry['size_bytes']} |")
    lines.append("")
    index_path = out_dir / "index.md"
    index_path.write_text("\n".join(lines), encoding="utf-8")
    return {"index_path": str(index_path), "entries": entries}


def check_scaffold(out_dir: Path) -> dict[str, Any]:
    missing = [name for name in sorted(SCAFFOLD_TEMPLATES) if not (out_dir / name).exists()]
    index_path = out_dir / "index.md"
    index_exists = index_path.exists()
    index_text = index_path.read_text(encoding="utf-8") if index_exists else ""
    missing_from_index = [name for name in sorted(SCAFFOLD_TEMPLATES) if index_exists and name not in index_text]
    return {
        "missing": missing,
        "index_exists": index_exists,
        "missing_from_index": missing_from_index,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Alexandria-Babel alignment, ledger, and scaffold tooling.")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--out-dir", default="docs/alexandria_babel", help="Output directory")
    parser.add_argument(
        "--mode",
        default="ledger",
        choices=["ledger", "scaffold", "check-scaffold", "all"],
        help="ledger: build feature/use-case matrix; scaffold: ensure thread-plan templates + index; check-scaffold: validate required scaffold files; all: run ledger + scaffold",
    )
    args = parser.parse_args()

    repo_root = Path(args.root).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {"mode": args.mode, "out_dir": str(out_dir)}
    if args.mode in {"ledger", "all"}:
        generated_at = datetime.now(timezone.utc).isoformat()
        routes = _load_routes(repo_root)
        entries, digests = _extract_entries(repo_root, routes)
        payload = {
            "generated_at": generated_at,
            "scope": SOURCE_FILES,
            "source_digests": [digest.__dict__ for digest in digests],
            "entries": entries,
            "summary": {
                "total": len(entries),
                "implemented": sum(1 for item in entries if item["status"] == "implemented"),
                "planned": sum(1 for item in entries if item["status"] == "planned"),
            },
        }
        json_path = out_dir / "feature_usecase_ledger.json"
        md_path = out_dir / "feature_usecase_matrix.md"
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        _write_markdown(md_path, generated_at, entries, digests)
        result["ledger"] = {"ledger": str(json_path), "matrix": str(md_path), "summary": payload["summary"]}

    if args.mode in {"scaffold", "all"}:
        scaffold_result = ensure_scaffold(out_dir)
        index_result = build_scaffold_index(out_dir)
        result["scaffold"] = {"templates": scaffold_result, "index": index_result}

    if args.mode == "check-scaffold":
        check_result = check_scaffold(out_dir)
        result["check_scaffold"] = check_result
        print(json.dumps(result, indent=2))
        if check_result["missing"] or not check_result["index_exists"] or check_result["missing_from_index"]:
            raise SystemExit(1)
        return

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
