#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


def _lazy_import_matplotlib():
    try:
        import matplotlib.pyplot as plt
        from matplotlib.patches import FancyBboxPatch
    except ImportError as exc:  # pragma: no cover - CLI dependency guard
        raise RuntimeError("matplotlib is required for render_architecture_diagram.py. Install with `pip install -e '.[dev]'`.") from exc
    return plt, FancyBboxPatch


LAYERS = [
    ("Layer 1", "Corpus Ingestion", "Seed texts, uploads, parsing, atomization"),
    ("Layer 2", "Atom Library", "5-level atoms + deterministic filenames"),
    ("Layer 3", "Hypergraph Projection", "Document/atom graph projection + integrity"),
    ("Layer 4", "Plexus Analysis", "9-layer rhetorical and linguistic analysis"),
    ("Layer 5", "Governance Audit", "Policy decisions, redactions, audit logs"),
    ("Layer 6", "Evolution Branching", "Branch events, replay, compare"),
    ("Layer 7", "Remix Composer", "Atom-pool recombination + lineage refs"),
    ("Layer 8", "Artifact & Retrieval", "Remix artifacts, source links, exports"),
    ("Layer 9", "Explorer & Submission Surface", "API/docs, demo scripts, visuals"),
]


def render_architecture_png(*, output_path: Path, dpi: int = 240) -> dict[str, str]:
    plt, FancyBboxPatch = _lazy_import_matplotlib()
    fig, ax = plt.subplots(figsize=(14, 10), dpi=dpi)
    bg = "#0b1220"
    fg = "#e8eef9"
    grid = "#263349"
    accent = ["#00d4ff", "#79e68c", "#ffd166", "#ff7b72", "#c792ea", "#6dd3ce", "#f2a65a", "#9ec1ff", "#f78fb3"]
    fig.patch.set_facecolor(bg)
    ax.set_facecolor(bg)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    x0, width = 0.7, 6.9
    box_h, gap = 0.78, 0.17
    y = 9.0
    centers: list[tuple[float, float]] = []
    for i, (layer_no, title, desc) in enumerate(LAYERS):
        color = accent[i % len(accent)]
        y1 = y - box_h
        patch = FancyBboxPatch(
            (x0, y1),
            width,
            box_h,
            boxstyle="round,pad=0.02,rounding_size=0.08",
            linewidth=1.8,
            edgecolor=color,
            facecolor="#111b2d",
        )
        ax.add_patch(patch)
        ax.text(x0 + 0.18, y1 + box_h * 0.62, f"{layer_no}  |  {title}", color=fg, fontsize=12, fontweight="bold", va="center")
        ax.text(x0 + 0.18, y1 + box_h * 0.28, desc, color="#c3d1e8", fontsize=9.7, va="center")
        centers.append((x0 + width / 2.0, y1 + box_h / 2.0))
        y = y1 - gap

    # Primary vertical flow arrows
    for i in range(len(centers) - 1):
        x1, y1 = centers[i]
        x2, y2 = centers[i + 1]
        ax.annotate("", xy=(x2, y2 + box_h * 0.42), xytext=(x1, y1 - box_h * 0.42),
                    arrowprops={"arrowstyle": "->", "color": grid, "linewidth": 1.8})

    # Side-band flow callouts
    callouts = [
        (8.2, 8.6, "Ingestion -> Plexus"),
        (8.2, 6.0, "Remix + Evolution"),
        (8.2, 4.5, "Governance Trace"),
        (8.2, 3.1, "Hypergraph Links"),
    ]
    for idx, (x, y_pos, label) in enumerate(callouts):
        ax.text(
            x,
            y_pos,
            label,
            color=fg,
            fontsize=10,
            ha="left",
            va="center",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "#151f33", "edgecolor": accent[idx * 2 % len(accent)], "linewidth": 1.2},
        )

    # Connect callouts to relevant layers
    ax.annotate("", xy=(7.6, centers[0][1]), xytext=(8.1, 8.6), arrowprops={"arrowstyle": "-|>", "color": accent[0], "linewidth": 1.4})
    ax.annotate("", xy=(7.6, centers[6][1]), xytext=(8.1, 6.0), arrowprops={"arrowstyle": "-|>", "color": accent[2], "linewidth": 1.4})
    ax.annotate("", xy=(7.6, centers[4][1]), xytext=(8.1, 4.5), arrowprops={"arrowstyle": "-|>", "color": accent[3], "linewidth": 1.4})
    ax.annotate("", xy=(7.6, centers[2][1]), xytext=(8.1, 3.1), arrowprops={"arrowstyle": "-|>", "color": accent[4], "linewidth": 1.4})

    ax.text(0.7, 9.6, "Nexus Babel Alexandria — 9-Layer Plexus Architecture", color=fg, fontsize=16, fontweight="bold")
    ax.text(0.7, 9.28, "Prix Ars Electronica (Digital Humanity) juror-facing overview", color="#c3d1e8", fontsize=10)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", dpi=dpi, facecolor=bg)
    plt.close(fig)
    return {"output": str(output_path)}


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a 9-layer plexus architecture diagram PNG.")
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "artifacts" / "prix-ars-2026" / "architecture_9_layer_plexus.png"),
        help="Output PNG path",
    )
    parser.add_argument("--dpi", type=int, default=240)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        summary = render_architecture_png(output_path=Path(args.output).resolve(), dpi=int(args.dpi))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

