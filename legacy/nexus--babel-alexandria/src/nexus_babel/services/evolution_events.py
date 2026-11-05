from __future__ import annotations

import hashlib
import random
import re
from typing import Any, Sequence

from .evolution_types import DriftResult

NATURAL_MAP = {
    # Original 5
    "th": "þ",
    "ae": "æ",
    "ph": "f",
    "ck": "k",
    "tion": "cion",
    # Latin → Italian
    "ct": "tt",
    "pl": "pi",
    "fl": "fi",
    "cl": "chi",
    "x": "ss",
    "li": "gli",
    "ni": "gn",
    # Old English → Modern English
    "sc": "sh",
    "cw": "qu",
    "hw": "wh",
    # Great Vowel Shift approximations
    "oo": "ou",
    "ee": "ea",
    "igh": "eye",
    # Common phonetic drifts
    "ght": "t",
    "ough": "ow",
    "wh": "w",
    "kn": "n",
    "wr": "r",
    "mb": "m",
    "gn": "n",
}

REVERSE_NATURAL_MAP = {
    "þ": "th",
    "æ": "ae",
    "f": "ph",
    "k": "ck",
    "cion": "tion",
    "tt": "ct",
    "pi": "pl",
    "fi": "fl",
    "chi": "cl",
    "ss": "x",
    "sh": "sc",
    "qu": "cw",
}

GLYPH_POOL = ["∆", "Æ", "Ω", "§", "☲", "⟁", "Ψ", "Φ", "Θ", "Ξ"]
PHASES = {"expansion", "peak", "compression", "rebirth"}
MERGE_STRATEGIES = {"left_wins", "right_wins", "interleave"}


def validate_event_payload(
    event_type: str,
    payload: dict[str, Any],
    *,
    phases: set[str],
    merge_strategies: set[str],
) -> dict[str, Any]:
    data = dict(payload or {})
    if "seed" in data:
        data["seed"] = int(data["seed"])

    if event_type == "natural_drift":
        data.setdefault("seed", 0)
        return data

    if event_type == "synthetic_mutation":
        mutation_rate = float(data.get("mutation_rate", 0.08))
        if mutation_rate < 0.0 or mutation_rate > 1.0:
            raise ValueError("mutation_rate must be between 0.0 and 1.0")
        data["mutation_rate"] = mutation_rate
        data.setdefault("seed", 0)
        return data

    if event_type == "phase_shift":
        phase = str(data.get("phase", "expansion")).lower()
        if phase not in phases:
            raise ValueError(f"phase must be one of {sorted(phases)}")
        data["phase"] = phase
        data.setdefault("seed", 0)
        return data

    if event_type == "glyph_fusion":
        left = str(data.get("left", "A"))
        right = str(data.get("right", "E"))
        fused = str(data.get("fused", "Æ"))
        if not left or not right or not fused:
            raise ValueError("glyph_fusion requires non-empty left/right/fused")
        data["left"] = left
        data["right"] = right
        data["fused"] = fused
        data.setdefault("seed", 0)
        return data

    if event_type == "remix":
        data.setdefault("seed", 0)
        data.setdefault("strategy", "interleave")
        return data

    if event_type == "reverse_drift":
        data.setdefault("seed", 0)
        return data

    if event_type == "merge":
        strategy = str(data.get("strategy", "interleave")).strip().lower()
        if strategy not in merge_strategies:
            raise ValueError(f"Unsupported merge strategy: {strategy}")
        merged_text = str(data.get("merged_text", ""))
        for key in ("left_text_hash", "right_text_hash"):
            if key in data and data[key] is not None:
                data[key] = str(data[key])
        conflict_semantics = data.get("conflict_semantics", {})
        if not isinstance(conflict_semantics, dict):
            raise ValueError("conflict_semantics must be an object")
        data["strategy"] = strategy
        data["merged_text"] = merged_text
        data["conflict_semantics"] = conflict_semantics
        data.setdefault("seed", 0)
        return data

    raise ValueError(f"Unsupported event_type: {event_type}")


def apply_event(
    text: str,
    event_type: str,
    event_payload: dict[str, Any],
    *,
    natural_map: dict[str, str],
    reverse_natural_map: dict[str, str],
    glyph_pool: Sequence[str],
) -> DriftResult:
    seed_input = f"{event_type}:{event_payload.get('seed', '')}:{hashlib.sha256(text.encode('utf-8')).hexdigest()}"
    rng = random.Random(int(hashlib.sha256(seed_input.encode("utf-8")).hexdigest(), 16) % (2**32))
    before_chars = len(text)

    if event_type == "natural_drift":
        out = text
        replacements = 0
        for old, new in natural_map.items():
            count = out.lower().count(old)
            replacements += count
            out = re.sub(old, new, out, flags=re.IGNORECASE)
        return DriftResult(out, {"event": event_type, "replacements": replacements, "before_chars": before_chars, "after_chars": len(out)})

    if event_type == "synthetic_mutation":
        words = re.findall(r"\w+|\W+", text)
        mutations = 0
        for idx, token in enumerate(words):
            if token.isalpha() and rng.random() < float(event_payload.get("mutation_rate", 0.08)):
                words[idx] = rng.choice(list(glyph_pool))
                mutations += 1
        out = "".join(words)
        return DriftResult(out, {"event": event_type, "mutations": mutations, "before_chars": before_chars, "after_chars": len(out)})

    if event_type == "phase_shift":
        phase = str(event_payload.get("phase", "expansion")).lower()
        acceleration = float(event_payload.get("acceleration", 1.0))
        phase_order = ["expansion", "peak", "compression", "rebirth"]
        phase_idx = phase_order.index(phase) if phase in phase_order else 0
        if phase in ("expansion", "peak"):
            intensity = min(acceleration * (1.0 + phase_idx * 0.5), 5.0)
        else:
            intensity = max(acceleration * (1.0 - (phase_idx - 2) * 0.3), 0.2)

        if phase == "compression":
            chars = list(text)
            removals = 0
            for i in range(len(chars) - 1, -1, -1):
                if chars[i].lower() in "aeiou" and rng.random() < min(intensity * 0.6, 1.0):
                    chars.pop(i)
                    removals += 1
            out = "".join(chars)
        elif phase == "rebirth":
            chars = list(text)
            removals = 0
            for i in range(len(chars) - 1, -1, -1):
                if chars[i].lower() in "aeiou" and rng.random() < min(intensity * 0.4, 1.0):
                    chars.pop(i)
                    removals += 1
            out = f"{''.join(chars)}\n\n⟁ SONG-BIRTH ⟁"
        elif phase == "peak":
            out = text.upper()
            if intensity > 1.5:
                words = out.split()
                expanded: list[str] = []
                interval = max(1, int(7 / intensity))
                for i, w in enumerate(words):
                    expanded.append(w)
                    if i % interval == 0:
                        expanded.append("MYTHIC")
                out = " ".join(expanded)
        else:
            words = text.split()
            expanded = []
            interval = max(1, int(7 / intensity))
            for i, w in enumerate(words):
                expanded.append(w)
                if i % interval == 0:
                    expanded.append("mythic")
            out = " ".join(expanded)
        return DriftResult(out, {"event": event_type, "phase": phase, "acceleration": acceleration, "intensity": intensity, "before_chars": before_chars, "after_chars": len(out)})

    if event_type == "glyph_fusion":
        left = str(event_payload.get("left", "A"))
        right = str(event_payload.get("right", "E"))
        fused = str(event_payload.get("fused", "Æ"))
        pair = f"{left}{right}"
        count = text.count(pair)
        out = text.replace(pair, fused)
        return DriftResult(out, {"event": event_type, "fusions": count, "pair": pair, "fused": fused, "before_chars": before_chars, "after_chars": len(out)})

    if event_type == "remix":
        remixed_text = str(event_payload.get("remixed_text", text))
        strategy = str(event_payload.get("strategy", "interleave"))
        return DriftResult(remixed_text, {"event": event_type, "strategy": strategy, "before_chars": before_chars, "after_chars": len(remixed_text)})

    if event_type == "reverse_drift":
        out = text
        reversals = 0
        reverse_pairs = sorted(reverse_natural_map.items(), key=lambda pair: len(pair[0]), reverse=True)
        for old, new in reverse_pairs:
            out, count = re.subn(re.escape(old), new, out, flags=re.IGNORECASE)
            reversals += count
        return DriftResult(
            out,
            {
                "event": event_type,
                "reversals": reversals,
                "before_chars": before_chars,
                "after_chars": len(out),
            },
        )

    if event_type == "merge":
        merged_text = str(event_payload.get("merged_text", text))
        strategy = str(event_payload.get("strategy", "interleave"))
        conflict_semantics = event_payload.get("conflict_semantics", {})
        if not isinstance(conflict_semantics, dict):
            conflict_semantics = {}
        return DriftResult(
            merged_text,
            {
                "event": event_type,
                "strategy": strategy,
                "left_branch_id": event_payload.get("left_branch_id"),
                "right_branch_id": event_payload.get("right_branch_id"),
                "lca_branch_id": event_payload.get("lca_branch_id"),
                "left_text_hash": event_payload.get("left_text_hash"),
                "right_text_hash": event_payload.get("right_text_hash"),
                "conflict_semantics": conflict_semantics,
                "before_chars": before_chars,
                "after_chars": len(merged_text),
            },
        )

    return DriftResult(text, {"event": event_type, "before_chars": before_chars, "after_chars": len(text), "note": "no-op"})
