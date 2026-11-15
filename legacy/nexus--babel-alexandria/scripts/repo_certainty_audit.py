#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional dependency in non-dev environments
    from pypdf import PdfReader
except Exception:  # pragma: no cover
    PdfReader = None


ROADMAP_TASK_RE = re.compile(r"Task ID:\s*([A-Z0-9-]+)")
ENDPOINT_RE = re.compile(r"/api/v1/[A-Za-z0-9/_{}-]+")
ROUTE_RE = re.compile(r'@router\.(?:get|post|put|patch|delete)\("([^"]+)"')
CONFLICT_RE = re.compile(r"^(<<<<<<<|=======|>>>>>>>|\|\|\|\|\|\|\|)", flags=re.MULTILINE)
PROMPT_RE = re.compile(
    r"(would you like|should i|should we|which prototype|build prototype tracker|must model|next step)",
    flags=re.IGNORECASE,
)


@dataclass
class FileEntry:
    path: str
    sha256: str
    size_bytes: int
    kind: str
    lines: int | None
    pdf_pages: int | None = None
    pdf_text_chars: int | None = None
    conflict_markers: bool = False


def _git_ls_files(root: Path) -> list[Path]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            stderr=subprocess.DEVNULL,
        )
        paths = [root / p for p in out.decode("utf-8", errors="ignore").split("\x00") if p]
        for extra in ("Makefile",):
            extra_path = root / extra
            if extra_path.is_file() and extra_path not in paths:
                paths.append(extra_path)
        return sorted([p for p in paths if p.is_file()])
    except Exception:
        skip_dirs = {".git", ".venv", "__pycache__", ".pytest_cache"}
        files: list[Path] = []
        for path in root.rglob("*"):
            if any(part in skip_dirs for part in path.parts):
                continue
            if path.is_file():
                files.append(path)
        return sorted(files)


def _is_binary(data: bytes) -> bool:
    if not data:
        return False
    if b"\x00" in data[:8192]:
        return True
    sample = data[:8192]
    text_bytes = sum(32 <= b <= 126 or b in (9, 10, 13) for b in sample)
    return (text_bytes / max(1, len(sample))) < 0.75


def _sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _load_text(data: bytes) -> str:
    return data.decode("utf-8", errors="ignore")


def _extract_pdf_details(path: Path) -> tuple[int | None, int | None]:
    if PdfReader is None:
        return None, None
    try:
        reader = PdfReader(str(path))
        chunks = []
        for page in reader.pages:
            chunks.append(page.extract_text() or "")
        return len(reader.pages), len("\n".join(chunks))
    except Exception:
        return None, None


def _normalize_path_template(path: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", path)


def _collect_manifest(root: Path, *, exclude_prefixes: set[str] | None = None) -> tuple[list[FileEntry], dict[str, str]]:
    file_entries: list[FileEntry] = []
    text_cache: dict[str, str] = {}
    prefixes = exclude_prefixes or set()
    for path in _git_ls_files(root):
        rel = path.relative_to(root).as_posix()
        if any(rel == prefix.rstrip("/") or rel.startswith(prefix) for prefix in prefixes):
            continue
        data = path.read_bytes()
        sha = _sha256_bytes(data)
        binary = _is_binary(data)
        pdf_pages = None
        pdf_chars = None
        lines = None
        conflict = False
        kind = "binary"

        if not binary:
            text = _load_text(data)
            text_cache[rel] = text
            lines = text.count("\n") + (1 if text else 0)
            conflict = bool(CONFLICT_RE.search(text))
            kind = "text"
        elif path.suffix.lower() == ".pdf":
            kind = "pdf"
            pdf_pages, pdf_chars = _extract_pdf_details(path)
        else:
            kind = "binary"

        file_entries.append(
            FileEntry(
                path=rel,
                sha256=sha,
                size_bytes=len(data),
                kind=kind,
                lines=lines,
                pdf_pages=pdf_pages,
                pdf_text_chars=pdf_chars,
                conflict_markers=conflict,
            )
        )

    file_entries.sort(key=lambda item: item.path)
    return file_entries, text_cache


def _implemented_routes(text_cache: dict[str, str]) -> set[str]:
    routes = set()
    route_sources = [
        path
        for path in text_cache
        if path == "src/nexus_babel/api/routes.py"
        or (path.startswith("src/nexus_babel/api/routes/") and path.endswith(".py"))
    ]
    for source in route_sources:
        routes_text = text_cache.get(source, "")
        for m in ROUTE_RE.finditer(routes_text):
            path = m.group(1)
            if path.startswith("/api/v1/"):
                routes.add(path)
            else:
                routes.add(f"/api/v1{path}")
    return routes


def _extract_roadmap_tasks(text_cache: dict[str, str]) -> list[dict[str, Any]]:
    tasks = []
    source_file = "docs/roadmap.md" if "docs/roadmap.md" in text_cache else "roadmap.md"
    roadmap = text_cache.get(source_file, "")
    for m in ROADMAP_TASK_RE.finditer(roadmap):
        tasks.append(
            {
                "id": m.group(1),
                "type": "roadmap_task",
                "status": "planned",
                "source_file": source_file,
                "line": roadmap.count("\n", 0, m.start()) + 1,
                "text": f"Task {m.group(1)}",
            }
        )
    return tasks


def _extract_endpoint_requirements(text_cache: dict[str, str], implemented: set[str]) -> list[dict[str, Any]]:
    normalized_implemented = {_normalize_path_template(path) for path in implemented}
    entries = []
    for source in ("README.md", "docs/OPERATOR_RUNBOOK.md"):
        text = text_cache.get(source, "")
        for m in ENDPOINT_RE.finditer(text):
            endpoint = m.group(0)
            normalized_endpoint = _normalize_path_template(endpoint)
            is_implemented = endpoint in implemented or normalized_endpoint in normalized_implemented
            entries.append(
                {
                    "id": f"endpoint::{endpoint}",
                    "type": "api_endpoint",
                    "status": "implemented" if is_implemented else "planned",
                    "source_file": source,
                    "line": text.count("\n", 0, m.start()) + 1,
                    "text": endpoint,
                    "evidence": endpoint if is_implemented else "not found in routes.py",
                }
            )
    dedup: dict[str, dict[str, Any]] = {}
    for entry in entries:
        key = entry["id"]
        if key not in dedup:
            dedup[key] = entry
        elif dedup[key]["status"] != "implemented" and entry["status"] == "implemented":
            dedup[key] = entry
    return sorted(dedup.values(), key=lambda item: item["id"])


def _extract_prompt_suggestions(text_cache: dict[str, str]) -> list[dict[str, Any]]:
    suggestions: list[dict[str, Any]] = []
    for source, text in text_cache.items():
        if not source.endswith(".md"):
            continue
        if source not in {
            "0469-arc4n-seed-texts-and-atomization-2.md",
            "README.md",
            "# Theoria Linguae Machina Comprehensive Design Document for the….md",
            "Nexus_Bable-Alexandria.md",
            "docs/corpus/0469-arc4n-seed-texts-and-atomization-2.md",
            "docs/corpus/# Theoria Linguae Machina Comprehensive Design Document for the….md",
            "docs/corpus/Nexus_Bable-Alexandria.md",
        }:
            continue
        for line_number, line in enumerate(text.splitlines(), start=1):
            if PROMPT_RE.search(line):
                slug = hashlib.sha1(f"{source}:{line_number}:{line}".encode("utf-8")).hexdigest()[:12]
                suggestions.append(
                    {
                        "id": f"suggestion::{slug}",
                        "type": "suggested_feature_or_use_case",
                        "status": "planned",
                        "source_file": source,
                        "line": line_number,
                        "text": line.strip(),
                    }
                )
    return suggestions


def _summaries(manifest: list[FileEntry], ledger: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    for item in manifest:
        by_kind[item.kind] = by_kind.get(item.kind, 0) + 1
    by_status: dict[str, int] = {}
    by_type: dict[str, int] = {}
    for item in ledger:
        by_status[item["status"]] = by_status.get(item["status"], 0) + 1
        by_type[item["type"]] = by_type.get(item["type"], 0) + 1
    return {
        "files_total": len(manifest),
        "files_by_kind": by_kind,
        "features_total": len(ledger),
        "features_by_status": by_status,
        "features_by_type": by_type,
        "conflict_files": [entry.path for entry in manifest if entry.conflict_markers],
    }


def _write_report(
    out_path: Path,
    generated_at: str,
    summary: dict[str, Any],
    manifest: list[FileEntry],
    ledger: list[dict[str, Any]],
) -> None:
    lines: list[str] = []
    lines.append("# Repository Certainty Report")
    lines.append("")
    lines.append(f"- Generated: `{generated_at}`")
    lines.append(f"- Files processed: `{summary['files_total']}`")
    lines.append(f"- Feature/use-case entries: `{summary['features_total']}`")
    lines.append(f"- Feature status split: `{summary['features_by_status']}`")
    lines.append("")
    lines.append("## Ingestion Guarantees")
    lines.append("")
    lines.append("- Every tracked file was read as bytes and hashed (`sha256`).")
    lines.append("- Text files were decoded and scanned for conflict markers and requirement cues.")
    lines.append("- PDF files were parsed for page count and text-char extraction when parser support was available.")
    lines.append("")
    if summary["conflict_files"]:
        lines.append("### Conflict Markers Found")
        lines.append("")
        for path in summary["conflict_files"]:
            lines.append(f"- `{path}`")
        lines.append("")
    else:
        lines.append("### Conflict Markers Found")
        lines.append("")
        lines.append("- None")
        lines.append("")

    lines.append("## Feature/Use-Case Ledger Summary")
    lines.append("")
    lines.append("| Type | Count |")
    lines.append("|---|---:|")
    for key, value in sorted(summary["features_by_type"].items()):
        lines.append(f"| `{key}` | {value} |")
    lines.append("")
    lines.append("## File Manifest")
    lines.append("")
    lines.append("| Path | Kind | Bytes | Lines | SHA256 |")
    lines.append("|---|---|---:|---:|---|")
    for entry in manifest:
        line_text = "" if entry.lines is None else str(entry.lines)
        lines.append(f"| `{entry.path}` | `{entry.kind}` | {entry.size_bytes} | {line_text or '-'} | `{entry.sha256}` |")
    lines.append("")
    lines.append("## Feature/Use-Case Ledger")
    lines.append("")
    lines.append("| ID | Type | Status | Source | Line | Text |")
    lines.append("|---|---|---|---|---:|---|")
    for item in ledger:
        text = item["text"].replace("|", "\\|")
        lines.append(
            f"| `{item['id']}` | `{item['type']}` | `{item['status']}` | `{item['source_file']}` | {item['line']} | {text} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def _generate_certainty_outputs(root: Path, out_dir: Path, *, exclude_prefixes: set[str] | None = None) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest, text_cache = _collect_manifest(root, exclude_prefixes=exclude_prefixes)
    implemented = _implemented_routes(text_cache)
    ledger: list[dict[str, Any]] = []
    ledger.extend(_extract_roadmap_tasks(text_cache))
    ledger.extend(_extract_endpoint_requirements(text_cache, implemented))
    ledger.extend(_extract_prompt_suggestions(text_cache))
    ledger.sort(key=lambda item: (item["type"], item["source_file"], item["line"], item["id"]))

    summary = _summaries(manifest, ledger)
    manifest_payload = {
        "generated_at": generated_at,
        "root": str(root),
        "summary": summary,
        "files": [entry.__dict__ for entry in manifest],
    }
    ledger_payload = {
        "generated_at": generated_at,
        "root": str(root),
        "summary": summary,
        "entries": ledger,
    }

    manifest_path = out_dir / "file_manifest.json"
    ledger_path = out_dir / "feature_usecase_ledger.json"
    report_path = out_dir / "repo_certainty_report.md"
    manifest_path.write_text(json.dumps(manifest_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    ledger_path.write_text(json.dumps(ledger_payload, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_report(report_path, generated_at, summary, manifest, ledger)
    return {
        "manifest": manifest_path,
        "ledger": ledger_path,
        "report": report_path,
        "summary": summary,
    }


def _normalized_json_for_check(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized.pop("generated_at", None)
    normalized.pop("root", None)
    return normalized


def _normalized_report_for_check(text: str) -> str:
    return re.sub(r"^- Generated: `[^`]+`$", "- Generated: `<normalized>`", text, flags=re.MULTILINE)


def _check_certainty_outputs(expected_dir: Path, generated_dir: Path) -> tuple[bool, list[str]]:
    issues: list[str] = []
    json_names = ["file_manifest.json", "feature_usecase_ledger.json"]
    for name in json_names:
        expected_path = expected_dir / name
        generated_path = generated_dir / name
        if not expected_path.is_file():
            issues.append(f"missing committed artifact: {expected_path}")
            continue
        expected_payload = json.loads(expected_path.read_text(encoding="utf-8"))
        generated_payload = json.loads(generated_path.read_text(encoding="utf-8"))
        if _normalized_json_for_check(expected_payload) != _normalized_json_for_check(generated_payload):
            issues.append(f"stale artifact content: {expected_path}")

    report_name = "repo_certainty_report.md"
    expected_report_path = expected_dir / report_name
    generated_report_path = generated_dir / report_name
    if not expected_report_path.is_file():
        issues.append(f"missing committed artifact: {expected_report_path}")
    else:
        expected_report = _normalized_report_for_check(expected_report_path.read_text(encoding="utf-8"))
        generated_report = _normalized_report_for_check(generated_report_path.read_text(encoding="utf-8"))
        if expected_report != generated_report:
            issues.append(f"stale artifact content: {expected_report_path}")

    return (len(issues) == 0), issues


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate repository ingestion + feature certainty evidence.")
    parser.add_argument("--root", default=".", help="Repository root path")
    parser.add_argument("--out-dir", default="docs/certainty", help="Output directory")
    parser.add_argument("--check", action="store_true", help="Verify committed certainty artifacts are up to date")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    out_dir = (root / args.out_dir).resolve()
    exclude_prefix = Path(args.out_dir).as_posix().strip("/")
    exclude_prefixes = {f"{exclude_prefix}/"} if exclude_prefix else set()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="certainty-check-") as tmp_dir:
            _generate_certainty_outputs(root, Path(tmp_dir), exclude_prefixes=exclude_prefixes)
            ok, issues = _check_certainty_outputs(out_dir, Path(tmp_dir))
        if not ok:
            print("Certainty artifacts are stale. Regenerate with: python scripts/repo_certainty_audit.py", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            raise SystemExit(1)
        print(json.dumps({"status": "ok", "checked_dir": str(out_dir)}, indent=2))
        return

    generated = _generate_certainty_outputs(root, out_dir, exclude_prefixes=exclude_prefixes)
    print(
        json.dumps(
            {
                "manifest": str(generated["manifest"]),
                "ledger": str(generated["ledger"]),
                "report": str(generated["report"]),
                "summary": generated["summary"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
