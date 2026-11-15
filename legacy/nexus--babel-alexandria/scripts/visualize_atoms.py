#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from sqlalchemy import select  # noqa: E402

from nexus_babel.config import Settings  # noqa: E402
from nexus_babel.db import DBManager  # noqa: E402
from nexus_babel.models import Atom, Document, RemixArtifact  # noqa: E402
from nexus_babel.services.text_utils import atomize_text_rich  # noqa: E402


FALLBACK_TEXT = (
    "Language fractures into atoms, glyphs, and echoes. "
    "Meaning returns as structure, rhythm, and relation."
)


def _lazy_import_matplotlib():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover - CLI dependency guard
        raise RuntimeError("matplotlib is required for visualize_atoms.py. Install with `pip install -e '.[dev]'`.") from exc
    return plt


def _pick_document(session, document_id: str | None) -> Document | None:
    if document_id:
        return session.scalar(select(Document).where(Document.id == document_id))
    return session.scalar(
        select(Document)
        .where(Document.ingested.is_(True), Document.atom_count > 0)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .limit(1)
    )


def _load_atom_data(*, database_url: str, document_id: str | None, remix_id: str | None) -> dict[str, Any]:
    db = DBManager(database_url)
    try:
        with db.session() as session:
            doc = _pick_document(session, document_id)
            remix = session.scalar(select(RemixArtifact).where(RemixArtifact.id == remix_id)) if remix_id else None

            if doc:
                atoms = session.scalars(select(Atom).where(Atom.document_id == doc.id).order_by(Atom.atom_level, Atom.ordinal)).all()
                if atoms:
                    by_level: dict[str, list[Atom]] = {}
                    for atom in atoms:
                        by_level.setdefault(atom.atom_level, []).append(atom)
                    return {
                        "title": doc.title,
                        "document_id": doc.id,
                        "levels": {k: len(v) for k, v in by_level.items()},
                        "glyph_atoms": by_level.get("glyph-seed", []),
                        "word_atoms": by_level.get("word", []),
                        "sentence_atoms": by_level.get("sentence", []),
                        "paragraph_atoms": by_level.get("paragraph", []),
                        "remix": remix,
                        "source": "database",
                    }
    except Exception:
        pass

    rich = atomize_text_rich(FALLBACK_TEXT)
    return {
        "title": "Fallback Atomization Sample",
        "document_id": None,
        "levels": {k: len(v) for k, v in rich.items()},
        "glyph_atoms": rich.get("glyph-seed", []),
        "word_atoms": rich.get("word", []),
        "sentence_atoms": rich.get("sentence", []),
        "paragraph_atoms": rich.get("paragraph", []),
        "remix": None,
        "source": "fallback",
    }


def render_visualization(
    *,
    database_url: str,
    output_path: Path,
    document_id: str | None = None,
    remix_id: str | None = None,
    dpi: int = 220,
    theme: str = "dark",
) -> dict[str, Any]:
    plt = _lazy_import_matplotlib()
    data = _load_atom_data(database_url=database_url, document_id=document_id, remix_id=remix_id)

    dark = theme.lower() == "dark"
    bg = "#070b12" if dark else "#f4f5f7"
    fg = "#e7edf7" if dark else "#1f2937"
    grid = "#314059" if dark else "#c7d2e0"
    accent = ["#00d4ff", "#79e68c", "#ffd166", "#ff7b72", "#c792ea"]

    plt.style.use("dark_background" if dark else "default")
    fig = plt.figure(figsize=(14, 8), dpi=dpi, facecolor=bg)
    gs = fig.add_gridspec(2, 2, height_ratios=[1.05, 1.0], hspace=0.3, wspace=0.2)
    ax_counts = fig.add_subplot(gs[0, 0])
    ax_glyphs = fig.add_subplot(gs[0, 1])
    ax_tree = fig.add_subplot(gs[1, :])

    for ax in (ax_counts, ax_glyphs, ax_tree):
        ax.set_facecolor(bg)
        ax.tick_params(colors=fg)
        for spine in ax.spines.values():
            spine.set_color(grid)

    # Panel 1: atom-level counts
    level_order = ["paragraph", "sentence", "word", "syllable", "glyph-seed"]
    levels = [lvl for lvl in level_order if lvl in data["levels"]]
    values = [data["levels"][lvl] for lvl in levels]
    ax_counts.bar(range(len(levels)), values, color=[accent[i % len(accent)] for i in range(len(levels))], alpha=0.9)
    ax_counts.set_xticks(range(len(levels)))
    ax_counts.set_xticklabels(levels, rotation=20, ha="right", color=fg)
    ax_counts.set_ylabel("Atom Count", color=fg)
    ax_counts.set_title("Atomization Level Counts", color=fg, fontsize=12, fontweight="bold")
    ax_counts.grid(axis="y", color=grid, alpha=0.35, linestyle="--")

    # Panel 2: glyph garden (scatter)
    glyphs = data["glyph_atoms"][:256]
    xs: list[float] = []
    ys: list[float] = []
    labels: list[str] = []
    colors: list[str] = []
    for idx, glyph in enumerate(glyphs):
        if hasattr(glyph, "model_dump"):
            meta = glyph.model_dump()
            ch = meta.get("character", "?")
            tags = meta.get("thematic_tags") or []
            label_color_idx = (len(tags) + idx) % len(accent)
        else:
            ch = getattr(glyph, "content", "?") or "?"
            tags = []
            label_color_idx = idx % len(accent)
        angle = idx * 0.41
        radius = 1.0 + (idx % 17) * 0.12
        xs.append(math.cos(angle) * radius)
        ys.append(math.sin(angle) * radius)
        labels.append(ch)
        colors.append(accent[label_color_idx])
    ax_glyphs.scatter(xs, ys, s=80, c=colors, alpha=0.35, edgecolors="none")
    for x, y, label, color in zip(xs[:80], ys[:80], labels[:80], colors[:80], strict=False):
        ax_glyphs.text(x, y, label, color=color, fontsize=9, ha="center", va="center")
    ax_glyphs.set_title("Glyph Garden (sampled glyph-seeds)", color=fg, fontsize=12, fontweight="bold")
    ax_glyphs.set_xticks([])
    ax_glyphs.set_yticks([])
    ax_glyphs.grid(color=grid, alpha=0.15)

    # Panel 3: hierarchy tree summary
    ax_tree.set_title("Hierarchy Flow: document -> paragraphs -> sentences -> words -> glyph-seeds", color=fg, fontsize=12, fontweight="bold")
    ax_tree.axis("off")
    nodes = [
        ("Document", 0.08, 0.52, data["title"]),
        ("Paragraphs", 0.28, 0.70, str(len(data["paragraph_atoms"]))),
        ("Sentences", 0.28, 0.34, str(len(data["sentence_atoms"]))),
        ("Words", 0.50, 0.52, str(len(data["word_atoms"]))),
        ("Glyph-Seeds", 0.74, 0.52, str(len(data["glyph_atoms"]))),
    ]
    for label, x, y, value in nodes:
        ax_tree.text(
            x,
            y,
            f"{label}\n{value}",
            transform=ax_tree.transAxes,
            ha="center",
            va="center",
            fontsize=11,
            color=fg,
            bbox={"boxstyle": "round,pad=0.45", "facecolor": "#111827" if dark else "#ffffff", "edgecolor": grid, "linewidth": 1.2},
        )
    arrows = [
        ((0.13, 0.55), (0.23, 0.67)),
        ((0.13, 0.49), (0.23, 0.37)),
        ((0.33, 0.70), (0.45, 0.56)),
        ((0.33, 0.34), (0.45, 0.48)),
        ((0.56, 0.52), (0.68, 0.52)),
    ]
    for (x1, y1), (x2, y2) in arrows:
        ax_tree.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            xycoords=ax_tree.transAxes,
            arrowprops={"arrowstyle": "->", "color": grid, "linewidth": 1.6},
        )

    title = "Alexandria-Babel Atomization Visualization"
    subtitle = f"Source: {data['source']}" + (f" | Document: {data['document_id']}" if data.get("document_id") else "")
    if data.get("remix") is not None:
        subtitle += f" | Remix: {data['remix'].id}"
    fig.suptitle(title, color=fg, fontsize=16, fontweight="bold", y=0.98)
    fig.text(0.5, 0.945, subtitle, color=fg, ha="center", va="center", fontsize=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight", facecolor=bg)
    plt.close(fig)
    return {"output": str(output_path), "source": data["source"], "document_id": data.get("document_id"), "levels": data["levels"]}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a submission-ready atomization visualization PNG.")
    parser.add_argument("--database-url", default=None, help="Override database URL (defaults to Settings)")
    parser.add_argument("--document-id", default=None, help="Specific document ID to visualize")
    parser.add_argument("--remix-id", default=None, help="Optional remix artifact ID for caption context")
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "artifacts" / "prix-ars-2026" / "atomization_visualization.png"),
        help="Output PNG path",
    )
    parser.add_argument("--dpi", type=int, default=220)
    parser.add_argument("--theme", choices=["dark", "light"], default="dark")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    settings = Settings()
    try:
        summary = render_visualization(
            database_url=args.database_url or settings.database_url,
            output_path=Path(args.output).resolve(),
            document_id=args.document_id,
            remix_id=args.remix_id,
            dpi=int(args.dpi),
            theme=args.theme,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
