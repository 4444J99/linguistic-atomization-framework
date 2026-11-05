#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sqlalchemy import select  # noqa: E402

from nexus_babel.config import Settings  # noqa: E402
from nexus_babel.db import DBManager  # noqa: E402
from nexus_babel.models import Atom, Document  # noqa: E402
from nexus_babel.services.text_utils import ATOM_FILENAME_SCHEMA_VERSION, normalize_atom_token  # noqa: E402


def _doc_dir_name(document: Document) -> str:
    return normalize_atom_token(Path(document.title).stem, max_len=48).upper()


def _write_text_file(path: Path, content: str, *, overwrite: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return
        if not overwrite:
            raise FileExistsError(f"Refusing to overwrite changed file without --overwrite: {path}")
    path.write_text(content, encoding="utf-8")


def _write_json_file(path: Path, payload: dict[str, Any], *, overwrite: bool) -> None:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    _write_text_file(path, serialized, overwrite=overwrite)


def export_atom_library(*, database_url: str, output_root: Path, overwrite: bool = False) -> dict[str, Any]:
    db = DBManager(database_url)
    export_root = output_root / "ARC4N" / "SEED_TEXTS"
    export_root.mkdir(parents=True, exist_ok=True)

    summary_docs: list[dict[str, Any]] = []
    with db.session() as session:
        docs = session.scalars(select(Document).where(Document.ingested.is_(True)).order_by(Document.created_at, Document.id)).all()
        for doc in docs:
            atoms = session.scalars(
                select(Atom).where(Atom.document_id == doc.id).order_by(Atom.atom_level, Atom.ordinal, Atom.id)
            ).all()
            if not atoms:
                continue

            counts = Counter(a.atom_level for a in atoms)
            doc_dir = export_root / _doc_dir_name(doc)
            written = 0
            for atom in atoms:
                atom_meta = atom.atom_metadata or {}
                filename = str(atom_meta.get("filename") or f"{atom.id}.txt")
                level_dir = doc_dir / atom.atom_level.replace("-", "_").upper()
                atom_path = level_dir / filename
                _write_text_file(atom_path, atom.content, overwrite=overwrite)
                written += 1

            manifest = {
                "document_id": doc.id,
                "title": doc.title,
                "path": doc.path,
                "checksum": doc.checksum,
                "atom_count": len(atoms),
                "atom_level_counts": dict(sorted(counts.items())),
                "filename_schema_version": (atoms[0].atom_metadata or {}).get(
                    "filename_schema_version",
                    ATOM_FILENAME_SCHEMA_VERSION,
                ),
                "source_lineage": {
                    "document_path": doc.path,
                    "raw_storage_path": (doc.provenance or {}).get("raw_storage_path"),
                    "ingest_scope": (doc.provenance or {}).get("ingest_scope"),
                },
            }
            _write_json_file(doc_dir / "manifest.json", manifest, overwrite=overwrite)
            summary_docs.append(
                {
                    "document_id": doc.id,
                    "title": doc.title,
                    "export_dir": str(doc_dir),
                    "atom_count": len(atoms),
                    "atom_level_counts": dict(sorted(counts.items())),
                    "files_written": written,
                }
            )

    return {
        "export_root": str(export_root),
        "documents": summary_docs,
        "documents_exported": len(summary_docs),
        "atoms_exported": sum(int(d["atom_count"]) for d in summary_docs),
    }


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export ingested atoms into an ARC4N seed-text library tree.")
    parser.add_argument("--output-root", default=str(REPO_ROOT), help="Base directory for export output")
    parser.add_argument("--database-url", default=None, help="Override database URL (defaults to NEXUS_DATABASE_URL / Settings)")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite changed files if they already exist")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON summary")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = Settings()
    try:
        summary = export_atom_library(
            database_url=args.database_url or settings.database_url,
            output_root=Path(args.output_root).resolve(),
            overwrite=bool(args.overwrite),
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.pretty:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

