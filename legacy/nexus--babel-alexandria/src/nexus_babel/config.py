from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="NEXUS_", extra="ignore")

    app_name: str = "Nexus Babel Alexandria MVP"
    environment: Literal["dev", "test", "prod"] = "dev"
    database_url: str = "sqlite:///./nexus_babel.db"
    schema_management_mode: Literal["auto_create", "migrate_only", "off"] | None = None
    neo4j_uri: str | None = None
    neo4j_username: str | None = None
    neo4j_password: str | None = None
    raw_mode_enabled: bool = True
    async_jobs_enabled: bool = True
    plugin_ml_enabled: bool = False
    shadow_execution_enabled: bool = False
    worker_poll_seconds: float = 1.0
    worker_lease_seconds: int = 30
    worker_name: str = "nexus-worker"
    corpus_root: Path = Field(default_factory=lambda: Path.cwd())
    object_storage_root: Path = Field(default_factory=lambda: Path.cwd() / "object_storage")
    seed_registry_path: Path = Field(default_factory=lambda: Path.cwd() / "docs" / "alexandria_babel" / "seed_corpus_registry.yaml")
    bootstrap_keys_enabled: bool | None = None
    bootstrap_viewer_key: str = "nexus-dev-viewer-key"
    bootstrap_operator_key: str = "nexus-dev-operator-key"
    bootstrap_researcher_key: str = "nexus-dev-researcher-key"
    bootstrap_admin_key: str = "nexus-dev-admin-key"
    public_blocked_terms: list[str] = Field(
        default_factory=lambda: [
            "kill",
            "self-harm",
            "hate",
            "ethnic cleansing",
            "bioweapon",
            "how to make a bomb",
        ]
    )

    def resolved_schema_management_mode(self) -> Literal["auto_create", "migrate_only", "off"]:
        if self.schema_management_mode:
            return self.schema_management_mode
        return "auto_create" if self.environment in {"dev", "test"} else "migrate_only"

    def resolved_bootstrap_keys_enabled(self) -> bool:
        if self.bootstrap_keys_enabled is not None:
            return self.bootstrap_keys_enabled
        return self.environment in {"dev", "test"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
