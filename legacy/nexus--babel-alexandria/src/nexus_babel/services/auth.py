from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.models import ApiKey

ROLE_ORDER = {
    "viewer": 1,
    "operator": 2,
    "researcher": 3,
    "admin": 4,
}


@dataclass
class AuthContext:
    api_key_id: str
    owner: str
    role: str
    raw_mode_enabled: bool


def hash_api_key(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class AuthService:
    def ensure_default_api_keys(self, session: Session, seed_keys: Iterable[tuple[str, str, str, bool]]) -> None:
        for owner, role, plaintext_key, raw_mode_enabled in seed_keys:
            key_hash = hash_api_key(plaintext_key)
            row = session.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash))
            if row:
                if not row.enabled:
                    row.enabled = True
                row.raw_mode_enabled = raw_mode_enabled
                continue
            session.add(
                ApiKey(
                    key_hash=key_hash,
                    owner=owner,
                    role=role,
                    enabled=True,
                    raw_mode_enabled=raw_mode_enabled,
                )
            )

    def authenticate(self, session: Session, plaintext_key: str | None) -> AuthContext | None:
        if not plaintext_key:
            return None
        key_hash = hash_api_key(plaintext_key)
        row = session.scalar(select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.enabled.is_(True)))
        if not row:
            return None
        row.last_used_at = datetime.now(tz=timezone.utc)
        return AuthContext(api_key_id=row.id, owner=row.owner, role=row.role, raw_mode_enabled=row.raw_mode_enabled)

    def role_allows(self, current_role: str, min_role: str) -> bool:
        return ROLE_ORDER.get(current_role, 0) >= ROLE_ORDER.get(min_role, 0)

    def mode_allows(self, current_role: str, mode: str, raw_mode_enabled: bool, key_raw_mode_enabled: bool = True) -> bool:
        normalized = mode.upper()
        if normalized == "RAW":
            if not raw_mode_enabled:
                return False
            if not key_raw_mode_enabled:
                return False
            return self.role_allows(current_role, "researcher")
        if normalized == "PUBLIC":
            return self.role_allows(current_role, "operator")
        return False
