from __future__ import annotations

import hashlib
import json
import random


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_rng_seed_hex(
    *,
    strategy: str,
    seed: int,
    source_text: str,
    target_text: str,
    atom_levels: list[str],
) -> str:
    seed_input = (
        f"remix:{strategy}:{seed}:"
        f"{sha256_text(source_text)}:"
        f"{sha256_text(target_text)}:"
        f"{','.join(atom_levels)}"
    )
    return hashlib.sha256(seed_input.encode("utf-8")).hexdigest()


def build_remix_rng(
    *,
    strategy: str,
    seed: int,
    source_text: str,
    target_text: str,
    atom_levels: list[str],
) -> tuple[random.Random, str]:
    rng_seed_hex = build_rng_seed_hex(
        strategy=strategy,
        seed=seed,
        source_text=source_text,
        target_text=target_text,
        atom_levels=atom_levels,
    )
    rng = random.Random(int(rng_seed_hex, 16) % (2**32))
    return rng, rng_seed_hex


def build_payload_hash(
    *,
    strategy: str,
    seed: int,
    mode: str,
    source_document_id: str | None,
    source_branch_id: str | None,
    target_document_id: str | None,
    target_branch_id: str | None,
    atom_levels: list[str],
    text_hash: str,
) -> str:
    payload = {
        "strategy": strategy,
        "seed": int(seed),
        "mode": mode.upper(),
        "source_document_id": source_document_id,
        "source_branch_id": source_branch_id,
        "target_document_id": target_document_id,
        "target_branch_id": target_branch_id,
        "atom_levels": atom_levels,
        "text_hash": text_hash,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
