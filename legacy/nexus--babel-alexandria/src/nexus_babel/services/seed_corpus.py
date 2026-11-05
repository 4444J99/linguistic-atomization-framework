"""Seed text registry, ingest profiles, and Project Gutenberg provisioning."""

from __future__ import annotations

from copy import deepcopy
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class SeedText:
    title: str
    author: str
    language: str
    source_url: str
    local_path: Path | None = None
    atomization_status: str = "not_provisioned"


SEED_REGISTRY: list[dict[str, Any]] = [
    {
        "title": "The Odyssey",
        "author": "Homer",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/1727/pg1727.txt",
    },
    {
        "title": "The Divine Comedy",
        "author": "Dante Alighieri",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/8800/pg8800.txt",
    },
    {
        "title": "Leaves of Grass",
        "author": "Walt Whitman",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/1322/pg1322.txt",
    },
    {
        "title": "Ulysses",
        "author": "James Joyce",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/4300/pg4300.txt",
    },
    {
        "title": "Frankenstein",
        "author": "Mary Shelley",
        "language": "English",
        "source_url": "https://www.gutenberg.org/cache/epub/84/pg84.txt",
    },
]

DEFAULT_INGEST_PROFILES: dict[str, dict[str, Any]] = {
    "arc4n-seed": {
        "name": "arc4n-seed",
        "description": "Canonical ARC4N pilot corpus ingest profile for the five seed texts.",
        "seed_titles": [entry["title"] for entry in SEED_REGISTRY],
        "atom_tracks": ["literary", "glyphic_seed"],
        "parse_options": {"atomize": True},
    }
}

DEFAULT_REGISTRY_PAYLOAD: dict[str, Any] = {
    "schema_version": "1.0",
    "seeds": deepcopy(SEED_REGISTRY),
    "profiles": deepcopy(DEFAULT_INGEST_PROFILES),
}


def _safe_yaml_load(path: Path) -> Any:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("PyYAML is required to load seed registry profiles; install project dependencies first.") from exc
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_seed_registry_payload(registry_path: Path | None = None) -> dict[str, Any]:
    if registry_path and registry_path.exists():
        raw = _safe_yaml_load(registry_path) or {}
        if not isinstance(raw, dict):
            raise ValueError(f"Seed registry must be a mapping: {registry_path}")
        seeds = raw.get("seeds")
        if not isinstance(seeds, list) or not seeds:
            raise ValueError(f"Seed registry missing non-empty 'seeds' list: {registry_path}")
        profiles = raw.get("profiles") or {}
        if not isinstance(profiles, dict):
            raise ValueError(f"Seed registry 'profiles' must be a mapping: {registry_path}")
        payload = {
            "schema_version": str(raw.get("schema_version", "1.0")),
            "seeds": seeds,
            "profiles": profiles,
        }
        return payload
    return deepcopy(DEFAULT_REGISTRY_PAYLOAD)


def load_ingest_profile(name: str, registry_path: Path | None = None) -> dict[str, Any]:
    profile_name = (name or "").strip()
    if not profile_name:
        raise ValueError("Profile name is required")
    payload = load_seed_registry_payload(registry_path)
    profiles = payload.get("profiles") or {}
    profile = profiles.get(profile_name)
    if profile is None:
        raise ValueError(f"Unknown ingest profile: {profile_name}")
    if not isinstance(profile, dict):
        raise ValueError(f"Ingest profile '{profile_name}' must be a mapping")

    seed_titles = profile.get("seed_titles") or []
    source_paths = profile.get("source_paths") or []
    atom_tracks = profile.get("atom_tracks") or []
    parse_options = profile.get("parse_options") or {}

    if not isinstance(seed_titles, list):
        raise ValueError(f"Profile '{profile_name}' seed_titles must be a list")
    if not isinstance(source_paths, list):
        raise ValueError(f"Profile '{profile_name}' source_paths must be a list")
    if not isinstance(atom_tracks, list):
        raise ValueError(f"Profile '{profile_name}' atom_tracks must be a list")
    if not isinstance(parse_options, dict):
        raise ValueError(f"Profile '{profile_name}' parse_options must be a mapping")

    return {
        "name": str(profile.get("name") or profile_name),
        "description": str(profile.get("description") or ""),
        "seed_titles": [str(v) for v in seed_titles],
        "source_paths": [str(v) for v in source_paths],
        "atom_tracks": [str(v) for v in atom_tracks],
        "parse_options": deepcopy(parse_options),
        "registry_schema_version": str(payload.get("schema_version", "1.0")),
    }


class SeedCorpusService:
    def __init__(self, seeds_dir: Path, registry_path: Path | None = None):
        self.seeds_dir = seeds_dir
        self.registry_path = registry_path
        self.seeds_dir.mkdir(parents=True, exist_ok=True)
        self.registry_payload = load_seed_registry_payload(registry_path)
        self.seed_registry: list[dict[str, Any]] = list(self.registry_payload.get("seeds", []))

    def list_seed_texts(self) -> list[dict[str, Any]]:
        result = []
        for entry in self.seed_registry:
            local_path = self._local_path_for(entry["title"])
            exists = local_path.exists()
            result.append(
                {
                    "title": entry["title"],
                    "author": entry["author"],
                    "language": entry["language"],
                    "source_url": entry["source_url"],
                    "local_path": str(local_path) if exists else None,
                    "atomization_status": "provisioned" if exists else "not_provisioned",
                }
            )
        return result

    def provision_seed_text(self, title: str) -> dict[str, Any]:
        entry = self._find_entry(title)
        if not entry:
            raise ValueError(f"Unknown seed text: {title}")

        local_path = self._local_path_for(entry["title"])
        if local_path.exists():
            return {
                "title": entry["title"],
                "status": "already_provisioned",
                "local_path": str(local_path),
            }

        self._download(entry["source_url"], local_path)
        return {
            "title": entry["title"],
            "status": "provisioned",
            "local_path": str(local_path),
        }

    def _find_entry(self, title: str) -> dict[str, Any] | None:
        title_lower = title.lower()
        for entry in self.seed_registry:
            if entry["title"].lower() == title_lower:
                return entry
        return None

    def _local_path_for(self, title: str) -> Path:
        safe_name = title.lower().replace(" ", "_").replace("'", "")
        return self.seeds_dir / f"{safe_name}.txt"

    def _download(self, url: str, dest: Path) -> None:
        urllib.request.urlretrieve(url, str(dest))  # noqa: S310

