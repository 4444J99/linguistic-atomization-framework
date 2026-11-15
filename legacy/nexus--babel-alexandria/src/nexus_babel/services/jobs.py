from __future__ import annotations

import time
from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nexus_babel.config import Settings
from nexus_babel.models import AnalysisRun, Document, Job, JobArtifact, JobAttempt
from nexus_babel.models import utcnow

RETRY_BACKOFF_SECONDS = [2, 10, 30]


class JobService:
    def __init__(self, settings: Settings, ingestion_service, analysis_service, evolution_service, hypergraph):
        self.settings = settings
        self.ingestion_service = ingestion_service
        self.analysis_service = analysis_service
        self.evolution_service = evolution_service
        self.hypergraph = hypergraph

    def submit(
        self,
        session: Session,
        *,
        job_type: str,
        payload: dict[str, Any],
        execution_mode: str = "async",
        idempotency_key: str | None = None,
        created_by: str | None = None,
        max_attempts: int = 3,
    ) -> Job:
        if idempotency_key:
            existing = session.scalar(
                select(Job).where(
                    Job.job_type == job_type,
                    Job.idempotency_key == idempotency_key,
                )
            )
            if existing:
                return existing

        job = Job(
            job_type=job_type,
            payload=payload,
            execution_mode=execution_mode,
            idempotency_key=idempotency_key,
            max_attempts=max_attempts,
            created_by=created_by,
            status="queued",
            next_run_at=utcnow(),
        )
        session.add(job)
        session.flush()
        return job

    def cancel(self, session: Session, job_id: str) -> Job:
        job = session.scalar(select(Job).where(Job.id == job_id))
        if not job:
            raise ValueError(f"Job {job_id} not found")
        if job.status in {"succeeded", "failed", "cancelled"}:
            return job
        job.status = "cancelled"
        job.lease_owner = None
        job.lease_expires_at = None
        return job

    def get_job(self, session: Session, job_id: str) -> dict[str, Any]:
        job = session.scalar(select(Job).where(Job.id == job_id))
        if not job:
            raise ValueError(f"Job {job_id} not found")
        attempts = session.scalars(select(JobAttempt).where(JobAttempt.job_id == job.id).order_by(JobAttempt.started_at)).all()
        artifacts = session.scalars(select(JobArtifact).where(JobArtifact.job_id == job.id).order_by(JobArtifact.created_at)).all()
        return {
            "job_id": job.id,
            "job_type": job.job_type,
            "status": job.status,
            "payload": job.payload,
            "result": job.result,
            "error_text": job.error_text,
            "execution_mode": job.execution_mode,
            "idempotency_key": job.idempotency_key,
            "max_attempts": job.max_attempts,
            "attempt_count": job.attempt_count,
            "next_run_at": job.next_run_at,
            "lease_owner": job.lease_owner,
            "lease_expires_at": job.lease_expires_at,
            "created_by": job.created_by,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "attempts": [
                {
                    "attempt_number": a.attempt_number,
                    "status": a.status,
                    "error_text": a.error_text,
                    "started_at": a.started_at,
                    "finished_at": a.finished_at,
                    "runtime_ms": a.runtime_ms,
                }
                for a in attempts
            ],
            "artifacts": [
                {
                    "artifact_type": a.artifact_type,
                    "artifact_ref": a.artifact_ref,
                    "artifact_payload": a.artifact_payload,
                    "created_at": a.created_at,
                }
                for a in artifacts
            ],
        }

    def lease_next(self, session: Session, worker_name: str) -> Job | None:
        now = utcnow()
        job = session.scalar(
            select(Job)
            .where(
                Job.status.in_(["queued", "retry_wait"]),
                Job.next_run_at <= now,
                (Job.lease_expires_at.is_(None)) | (Job.lease_expires_at < now),
            )
            .order_by(Job.created_at)
            .limit(1)
        )
        if not job:
            return None
        job.status = "running"
        job.lease_owner = worker_name
        job.lease_expires_at = now + timedelta(seconds=self.settings.worker_lease_seconds)
        return job

    def process_next(self, session: Session, worker_name: str) -> Job | None:
        job = self.lease_next(session, worker_name)
        if not job:
            return None
        self.execute(session, job)
        return job

    def execute(self, session: Session, job: Job) -> Job:
        if job.status in {"cancelled", "succeeded"}:
            return job

        attempt_no = int(job.attempt_count) + 1
        started = time.perf_counter()
        attempt = JobAttempt(job_id=job.id, attempt_number=attempt_no, status="running")
        session.add(attempt)
        job.attempt_count = attempt_no
        job.status = "running"
        job.error_text = None
        session.flush()

        try:
            result = self._dispatch(session, job)
            job.result = result
            job.status = "succeeded"
            job.lease_owner = None
            job.lease_expires_at = None
            attempt.status = "succeeded"
            self._create_artifacts(session, job, result)
        except Exception as exc:  # pragma: no cover - defensive
            job.error_text = str(exc)
            attempt.status = "failed"
            attempt.error_text = str(exc)
            if job.attempt_count < job.max_attempts:
                delay = RETRY_BACKOFF_SECONDS[min(job.attempt_count - 1, len(RETRY_BACKOFF_SECONDS) - 1)]
                job.status = "retry_wait"
                job.next_run_at = utcnow() + timedelta(seconds=delay)
            else:
                job.status = "failed"
                job.lease_owner = None
                job.lease_expires_at = None
        finally:
            runtime_ms = int((time.perf_counter() - started) * 1000)
            attempt.runtime_ms = runtime_ms
            attempt.finished_at = utcnow()

        return job

    def _dispatch(self, session: Session, job: Job) -> dict[str, Any]:
        payload = job.payload or {}
        if job.job_type == "ingest_batch":
            result = self.ingestion_service.ingest_batch(
                session=session,
                source_paths=list(payload.get("source_paths", [])),
                modalities=list(payload.get("modalities", [])),
                parse_options=dict(payload.get("parse_options", {})),
            )
            return {
                "ingest_job_id": result["job"].id,
                "documents_ingested": result["documents_ingested"],
                "atoms_created": result["atoms_created"],
                "provenance_digest": result["provenance_digest"],
                "warnings": result.get("warnings", []),
            }

        if job.job_type == "analyze":
            run, result = self.analysis_service.analyze(
                session=session,
                document_id=payload.get("document_id"),
                branch_id=payload.get("branch_id"),
                layers=list(payload.get("layers", [])),
                mode=str(payload.get("mode", "PUBLIC")),
                execution_mode="async",
                plugin_profile=payload.get("plugin_profile"),
                job_id=job.id,
            )
            return {
                "analysis_run_id": run.id,
                "mode": result["mode"],
                "layers": result["layers"],
                "confidence_bundle": result["confidence_bundle"],
                "hypergraph_ids": result["hypergraph_ids"],
                "plugin_provenance": result.get("plugin_provenance", {}),
            }

        if job.job_type == "branch_replay":
            replay = self.evolution_service.replay_branch(session=session, branch_id=str(payload.get("branch_id")))
            return replay

        if job.job_type == "integrity_audit":
            docs = session.scalars(select(Document).where(Document.ingested.is_(True))).all()
            findings = []
            for doc in docs:
                integrity = self.hypergraph.integrity_for_document(doc)
                if not integrity.get("consistent"):
                    findings.append({"document_id": doc.id, "integrity": integrity})
            return {"document_count": len(docs), "inconsistencies": findings}

        raise ValueError(f"Unsupported job_type: {job.job_type}")

    def _create_artifacts(self, session: Session, job: Job, result: dict[str, Any]) -> None:
        artifact_payload = {}
        if job.job_type == "analyze":
            artifact_payload = {
                "analysis_run_id": result.get("analysis_run_id"),
                "layer_count": len(result.get("layers", {})),
            }
        elif job.job_type == "ingest_batch":
            artifact_payload = {
                "ingest_job_id": result.get("ingest_job_id"),
                "documents_ingested": result.get("documents_ingested", 0),
            }
        elif job.job_type == "branch_replay":
            artifact_payload = {
                "branch_id": result.get("branch_id"),
                "text_hash": result.get("text_hash"),
            }
        if artifact_payload:
            session.add(
                JobArtifact(
                    job_id=job.id,
                    artifact_type=f"{job.job_type}_result",
                    artifact_payload=artifact_payload,
                )
            )

    def complete_stale_leases(self, session: Session, worker_name: str) -> int:
        now = utcnow()
        stale = session.scalars(
            select(Job).where(
                Job.status == "running",
                Job.lease_expires_at.is_not(None),
                Job.lease_expires_at < now,
            )
        ).all()
        for job in stale:
            job.status = "retry_wait" if job.attempt_count < job.max_attempts else "failed"
            job.lease_owner = worker_name
            job.lease_expires_at = None
            if job.status == "retry_wait":
                job.next_run_at = now + timedelta(seconds=RETRY_BACKOFF_SECONDS[min(job.attempt_count, len(RETRY_BACKOFF_SECONDS) - 1)])
        return len(stale)

    def last_analysis_run_for_job(self, session: Session, job_id: str) -> AnalysisRun | None:
        return session.scalar(select(AnalysisRun).where(AnalysisRun.job_id == job_id).order_by(AnalysisRun.created_at.desc()))
