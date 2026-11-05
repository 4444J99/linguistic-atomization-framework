from __future__ import annotations

import random
from dataclasses import dataclass

from nexus_babel.services.remix_compose import compose_text
from nexus_babel.services.remix_context import join_atoms_for_strategy, preferred_levels_for_strategy
from nexus_babel.services.remix_hashing import build_payload_hash, build_remix_rng


@dataclass
class _AtomStub:
    id: str
    atom_level: str
    ordinal: int
    content: str


def test_build_remix_rng_is_deterministic():
    kwargs = {
        "strategy": "thematic_blend",
        "seed": 7,
        "source_text": "alpha beta",
        "target_text": "gamma delta",
        "atom_levels": ["word", "sentence"],
    }
    rng1, seed_hex_1 = build_remix_rng(**kwargs)
    rng2, seed_hex_2 = build_remix_rng(**kwargs)

    assert seed_hex_1 == seed_hex_2
    assert [rng1.random() for _ in range(4)] == [rng2.random() for _ in range(4)]

    _, different_seed_hex = build_remix_rng(**{**kwargs, "seed": 8})
    assert different_seed_hex != seed_hex_1


def test_build_payload_hash_normalizes_mode_case():
    base = {
        "strategy": "interleave",
        "seed": 3,
        "source_document_id": "src-doc",
        "source_branch_id": None,
        "target_document_id": "tgt-doc",
        "target_branch_id": None,
        "atom_levels": ["word"],
        "text_hash": "abc123",
    }
    lower = build_payload_hash(mode="raw", **base)
    upper = build_payload_hash(mode="RAW", **base)
    assert lower == upper


def test_preferred_levels_and_join_atoms_strategy_helpers():
    assert preferred_levels_for_strategy("thematic_blend") == ["sentence", "word", "paragraph", "glyph-seed", "syllable"]
    assert preferred_levels_for_strategy("glyph_collide") == ["glyph-seed", "word", "syllable", "sentence", "paragraph"]
    assert preferred_levels_for_strategy("unknown")[0] == "word"

    atoms = [
        _AtomStub(id="a1", atom_level="paragraph", ordinal=1, content="Para A"),
        _AtomStub(id="a2", atom_level="paragraph", ordinal=2, content="Para B"),
    ]
    assert join_atoms_for_strategy(atoms, "paragraph") == "Para A\n\nPara B"
    assert join_atoms_for_strategy(atoms, "sentence") == "Para A Para B"
    assert join_atoms_for_strategy(atoms, "glyph-seed") == "Para APara B"


def test_compose_text_uses_atom_levels_and_returns_refs():
    source_atoms = [
        _AtomStub(id="s1", atom_level="word", ordinal=1, content="one"),
        _AtomStub(id="s2", atom_level="word", ordinal=2, content="two"),
    ]
    target_atoms = [
        _AtomStub(id="t1", atom_level="word", ordinal=1, content="alpha"),
        _AtomStub(id="t2", atom_level="word", ordinal=2, content="beta"),
    ]
    source_ctx = {
        "role": "source",
        "document_id": "src",
        "branch_id": None,
        "root_document_id": "src",
        "text": "ignored source text",
        "atoms_by_level": {"word": source_atoms},
    }
    target_ctx = {
        "role": "target",
        "document_id": "tgt",
        "branch_id": None,
        "root_document_id": "tgt",
        "text": "ignored target text",
        "atoms_by_level": {"word": target_atoms},
    }

    remixed, refs = compose_text(
        source_text=source_ctx["text"],
        target_text=target_ctx["text"],
        strategy="interleave",
        rng=random.Random(0),
        source_ctx=source_ctx,  # type: ignore[arg-type]
        target_ctx=target_ctx,  # type: ignore[arg-type]
        atom_levels=["word"],
    )

    assert remixed == "one alpha two beta"
    assert [r["atom_id"] for r in refs] == ["s1", "s2", "t1", "t2"]
    assert [r["role"] for r in refs] == ["source", "source", "target", "target"]
