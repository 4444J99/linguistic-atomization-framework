from __future__ import annotations

import hashlib
import re
from typing import Iterable

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from nexus_babel.models import AuditLog, ModePolicy, PolicyDecision
from nexus_babel.models import utcnow


class GovernanceService:
    def ensure_default_policies(self, session: Session, blocked_terms: Iterable[str]) -> None:
        blocked_terms = sorted(set(t.strip().lower() for t in blocked_terms if t.strip()))
        defaults = {
            "PUBLIC": {
                "blocked_terms": blocked_terms,
                "redaction_style": "[REDACTED]",
                "hard_block_threshold": 1,
            },
            "RAW": {
                "blocked_terms": blocked_terms,
                "redaction_style": "[FLAGGED]",
                "hard_block_threshold": 999,
            },
        }

        for mode, policy in defaults.items():
            record = session.scalar(select(ModePolicy).where(ModePolicy.mode == mode))
            if record:
                if not record.effective_from:
                    record.effective_from = utcnow()
                continue
            session.add(
                ModePolicy(
                    mode=mode,
                    policy=policy,
                    policy_version=1,
                    effective_from=utcnow(),
                )
            )

    def evaluate(self, session: Session, candidate_output: str, mode: str) -> dict:
        normalized_mode = mode.upper()
        now = utcnow()
        policy_row = session.scalar(
            select(ModePolicy).where(
                ModePolicy.mode == normalized_mode,
                (ModePolicy.effective_from.is_(None)) | (ModePolicy.effective_from <= now),
                (ModePolicy.effective_to.is_(None)) | (ModePolicy.effective_to > now),
            )
        )
        if not policy_row:
            raise ValueError(f"Policy for mode {normalized_mode} not found")

        policy = policy_row.policy or {}
        blocked_terms = [t.lower() for t in policy.get("blocked_terms", [])]
        redaction_style = policy.get("redaction_style", "[REDACTED]")
        hard_block_threshold = int(policy.get("hard_block_threshold", 1))

        policy_hits: list[str] = []
        redactions: list[str] = []
        decision_trace_hits: list[dict] = []
        redacted_text = candidate_output
        for term in blocked_terms:
            if not term:
                continue
            matches = list(re.finditer(rf"\b{re.escape(term)}\b", candidate_output, flags=re.IGNORECASE))
            if matches:
                policy_hits.append(term)
                redactions.append(term)
                for m in matches:
                    decision_trace_hits.append(
                        {
                            "term": term,
                            "start": m.start(),
                            "end": m.end(),
                            "matched_text": m.group(0),
                            "rule": "blocked_terms",
                            "mode": normalized_mode,
                        }
                    )
                redacted_text = re.sub(
                    rf"\b{re.escape(term)}\b",
                    redaction_style,
                    redacted_text,
                    flags=re.IGNORECASE,
                )

        allow = len(policy_hits) < hard_block_threshold
        decision_trace = {
            "mode": normalized_mode,
            "policy_version": policy_row.policy_version,
            "hard_block_threshold": hard_block_threshold,
            "hits": decision_trace_hits,
            "mode_rationale": "RAW allows flagged terms for research review" if normalized_mode == "RAW" else "PUBLIC blocks flagged terms",
            "redaction_style": redaction_style,
            "allow": allow,
        }

        audit = AuditLog(
            action="governance.evaluate",
            mode=normalized_mode,
            actor="system",
            details={
                "input_preview": candidate_output[:240],
                "policy_hits": policy_hits,
                "policy_version": policy_row.policy_version,
                "allow": allow,
                "decision_trace": decision_trace,
            },
        )
        session.add(audit)
        session.flush()

        decision = PolicyDecision(
            mode=normalized_mode,
            input_hash=hashlib.sha256(candidate_output.encode("utf-8")).hexdigest(),
            allow=allow,
            policy_hits=policy_hits,
            redactions=redactions,
            decision_trace=decision_trace,
            audit_id=audit.id,
        )
        session.add(decision)
        session.flush()

        return {
            "allow": allow,
            "policy_hits": policy_hits,
            "redactions": redactions,
            "audit_id": audit.id,
            "decision_id": decision.id,
            "redacted_text": redacted_text,
            "decision_trace": decision_trace,
        }

    def list_policy_decisions(self, session: Session, limit: int = 100) -> list[dict]:
        rows = session.scalars(select(PolicyDecision).order_by(desc(PolicyDecision.created_at)).limit(limit)).all()
        return [
            {
                "id": row.id,
                "mode": row.mode,
                "allow": row.allow,
                "policy_hits": row.policy_hits,
                "redactions": row.redactions,
                "decision_trace": row.decision_trace,
                "audit_id": row.audit_id,
                "created_at": row.created_at,
            }
            for row in rows
        ]
