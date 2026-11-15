from __future__ import annotations

import random

from nexus_babel.services import remix_strategies
from nexus_babel.services.remix_context import (
    join_atoms_for_strategy,
    pick_atom_level,
    preferred_levels_for_strategy,
)
from nexus_babel.services.remix_types import RemixAtomRef, RemixContext


def compose_text(
    *,
    source_text: str,
    target_text: str,
    strategy: str,
    rng: random.Random,
    source_ctx: RemixContext,
    target_ctx: RemixContext,
    atom_levels: list[str],
) -> tuple[str, list[RemixAtomRef]]:
    source_atom_refs: list[RemixAtomRef] = []
    target_atom_refs: list[RemixAtomRef] = []
    if atom_levels:
        preferred = preferred_levels_for_strategy(strategy)
        selected_source = pick_atom_level(source_ctx.get("atoms_by_level", {}), preferred)
        selected_target = pick_atom_level(target_ctx.get("atoms_by_level", {}), preferred)
        if selected_source and selected_target:
            source_atoms = source_ctx["atoms_by_level"][selected_source]
            target_atoms = target_ctx["atoms_by_level"][selected_target]
            source_text = join_atoms_for_strategy(source_atoms, selected_source)
            target_text = join_atoms_for_strategy(target_atoms, selected_target)
            source_atom_refs = [
                {"atom_id": a.id, "atom_level": a.atom_level, "ordinal": a.ordinal, "role": "source"}
                for a in source_atoms
            ]
            target_atom_refs = [
                {"atom_id": a.id, "atom_level": a.atom_level, "ordinal": a.ordinal, "role": "target"}
                for a in target_atoms
            ]

    remixed = apply_strategy(source_text, target_text, strategy, rng)
    return remixed, source_atom_refs + target_atom_refs


def apply_strategy(source: str, target: str, strategy: str, rng: random.Random) -> str:
    return remix_strategies.apply_strategy(source=source, target=target, strategy=strategy, rng=rng)
