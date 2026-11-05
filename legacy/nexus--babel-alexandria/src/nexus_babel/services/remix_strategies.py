from __future__ import annotations

import random
import re


def apply_strategy(source: str, target: str, strategy: str, rng: random.Random) -> str:
    if strategy == "interleave":
        return interleave(source, target)
    if strategy == "thematic_blend":
        return thematic_blend(source, target, rng)
    if strategy == "temporal_layer":
        return temporal_layer(source, target, rng)
    if strategy == "glyph_collide":
        return glyph_collide(source, target, rng)
    raise ValueError(f"Unknown remix strategy: {strategy}")


def interleave(source: str, target: str) -> str:
    source_words = re.findall(r"\S+", source)
    target_words = re.findall(r"\S+", target)
    result: list[str] = []
    max_len = max(len(source_words), len(target_words))
    for i in range(max_len):
        if i < len(source_words):
            result.append(source_words[i])
        if i < len(target_words):
            result.append(target_words[i])
    return " ".join(result)


def thematic_blend(source: str, target: str, rng: random.Random) -> str:
    source_sentences = [s.strip() for s in re.split(r"[.!?]+", source) if s.strip()]
    target_sentences = [s.strip() for s in re.split(r"[.!?]+", target) if s.strip()]
    combined = source_sentences + target_sentences
    rng.shuffle(combined)
    if not combined:
        return ""
    return ". ".join(combined[: max(len(source_sentences), len(target_sentences), 1)]) + "."


def temporal_layer(source: str, target: str, rng: random.Random) -> str:
    source_paras = [p.strip() for p in re.split(r"\n\s*\n", source) if p.strip()]
    target_paras = [p.strip() for p in re.split(r"\n\s*\n", target) if p.strip()]
    result: list[str] = []
    max_len = max(len(source_paras), len(target_paras), 1)
    for i in range(max_len):
        if i < len(source_paras):
            result.append(source_paras[i])
        if i < len(target_paras) and rng.random() > 0.3:
            result.append(f"[temporal overlay] {target_paras[i]}")
    return "\n\n".join(result)


def glyph_collide(source: str, target: str, rng: random.Random) -> str:
    source_glyphs = [c for c in source if not c.isspace()]
    target_glyphs = [c for c in target if not c.isspace()]
    result: list[str] = []
    max_len = max(len(source_glyphs), len(target_glyphs))
    for i in range(min(max_len, 2000)):
        s = source_glyphs[i] if i < len(source_glyphs) else ""
        t = target_glyphs[i] if i < len(target_glyphs) else ""
        if s == t:
            result.append(s)
        elif s and t:
            result.append(s if rng.random() > 0.5 else t)
        else:
            result.append(s or t)
    return "".join(result)
