"""Wave 2 internal alpha schema additions

Revision ID: 20260218_0002
Revises: 20260218_0001
Create Date: 2026-02-18 00:30:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260218_0002"
down_revision = "20260218_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("modality_status", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.add_column("documents", sa.Column("provider_summary", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.add_column("analysis_runs", sa.Column("execution_mode", sa.String(length=16), nullable=False, server_default="sync"))
    op.add_column("analysis_runs", sa.Column("plugin_profile", sa.String(length=64), nullable=True))
    op.add_column("analysis_runs", sa.Column("job_id", sa.String(length=36), nullable=True))
    op.add_column("analysis_runs", sa.Column("run_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))
    op.create_index(op.f("ix_analysis_runs_job_id"), "analysis_runs", ["job_id"], unique=False)

    op.add_column("branches", sa.Column("branch_version", sa.Integer(), nullable=False, server_default="0"))

    op.add_column("branch_events", sa.Column("payload_schema_version", sa.String(length=16), nullable=False, server_default="v1"))
    op.add_column("branch_events", sa.Column("event_hash", sa.String(length=128), nullable=False, server_default=""))
    op.create_index(op.f("ix_branch_events_event_hash"), "branch_events", ["event_hash"], unique=False)

    op.add_column("mode_policies", sa.Column("policy_version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("mode_policies", sa.Column("effective_from", sa.DateTime(timezone=True), nullable=True))
    op.add_column("mode_policies", sa.Column("effective_to", sa.DateTime(timezone=True), nullable=True))

    op.add_column("policy_decisions", sa.Column("decision_trace", sa.JSON(), nullable=False, server_default=sa.text("'{}'")))

    op.add_column("api_keys", sa.Column("raw_mode_enabled", sa.Boolean(), nullable=False, server_default=sa.text("0")))

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("execution_mode", sa.String(length=16), nullable=False),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_owner", sa.String(length=128), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_type", "idempotency_key", name="uq_job_idempotency"),
    )
    op.create_index(op.f("ix_jobs_job_type"), "jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_jobs_next_run_at"), "jobs", ["next_run_at"], unique=False)
    op.create_index(op.f("ix_jobs_status"), "jobs", ["status"], unique=False)

    op.create_table(
        "job_attempts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("runtime_ms", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_attempts_job_id"), "job_attempts", ["job_id"], unique=False)

    op.create_table(
        "job_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("artifact_type", sa.String(length=64), nullable=False),
        sa.Column("artifact_ref", sa.String(length=512), nullable=True),
        sa.Column("artifact_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_job_artifacts_job_id"), "job_artifacts", ["job_id"], unique=False)

    op.create_table(
        "layer_outputs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("analysis_run_id", sa.String(length=36), nullable=False),
        sa.Column("layer_name", sa.String(length=64), nullable=False),
        sa.Column("output", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_version", sa.String(length=32), nullable=False),
        sa.Column("runtime_ms", sa.Integer(), nullable=False),
        sa.Column("fallback_reason", sa.String(length=256), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_layer_outputs_analysis_run_id"), "layer_outputs", ["analysis_run_id"], unique=False)
    op.create_index(op.f("ix_layer_outputs_layer_name"), "layer_outputs", ["layer_name"], unique=False)

    op.create_table(
        "projection_ledger",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("atom_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id", "atom_id", name="uq_projection_ledger_document_atom"),
    )
    op.create_index(op.f("ix_projection_ledger_atom_id"), "projection_ledger", ["atom_id"], unique=False)
    op.create_index(op.f("ix_projection_ledger_document_id"), "projection_ledger", ["document_id"], unique=False)
    op.create_index(op.f("ix_projection_ledger_status"), "projection_ledger", ["status"], unique=False)

    op.create_table(
        "branch_checkpoints",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("event_index", sa.Integer(), nullable=False),
        sa.Column("snapshot_hash", sa.String(length=128), nullable=False),
        sa.Column("snapshot_compressed", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("branch_id", "event_index", name="uq_branch_checkpoint"),
    )
    op.create_index(op.f("ix_branch_checkpoints_branch_id"), "branch_checkpoints", ["branch_id"], unique=False)
    op.create_index(op.f("ix_branch_checkpoints_event_index"), "branch_checkpoints", ["event_index"], unique=False)
    op.create_index(op.f("ix_branch_checkpoints_snapshot_hash"), "branch_checkpoints", ["snapshot_hash"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_branch_checkpoints_snapshot_hash"), table_name="branch_checkpoints")
    op.drop_index(op.f("ix_branch_checkpoints_event_index"), table_name="branch_checkpoints")
    op.drop_index(op.f("ix_branch_checkpoints_branch_id"), table_name="branch_checkpoints")
    op.drop_table("branch_checkpoints")

    op.drop_index(op.f("ix_projection_ledger_status"), table_name="projection_ledger")
    op.drop_index(op.f("ix_projection_ledger_document_id"), table_name="projection_ledger")
    op.drop_index(op.f("ix_projection_ledger_atom_id"), table_name="projection_ledger")
    op.drop_table("projection_ledger")

    op.drop_index(op.f("ix_layer_outputs_layer_name"), table_name="layer_outputs")
    op.drop_index(op.f("ix_layer_outputs_analysis_run_id"), table_name="layer_outputs")
    op.drop_table("layer_outputs")

    op.drop_index(op.f("ix_job_artifacts_job_id"), table_name="job_artifacts")
    op.drop_table("job_artifacts")

    op.drop_index(op.f("ix_job_attempts_job_id"), table_name="job_attempts")
    op.drop_table("job_attempts")

    op.drop_index(op.f("ix_jobs_status"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_next_run_at"), table_name="jobs")
    op.drop_index(op.f("ix_jobs_job_type"), table_name="jobs")
    op.drop_table("jobs")

    op.drop_column("api_keys", "raw_mode_enabled")
    op.drop_column("policy_decisions", "decision_trace")
    op.drop_column("mode_policies", "effective_to")
    op.drop_column("mode_policies", "effective_from")
    op.drop_column("mode_policies", "policy_version")
    op.drop_index(op.f("ix_branch_events_event_hash"), table_name="branch_events")
    op.drop_column("branch_events", "event_hash")
    op.drop_column("branch_events", "payload_schema_version")
    op.drop_column("branches", "branch_version")
    op.drop_index(op.f("ix_analysis_runs_job_id"), table_name="analysis_runs")
    op.drop_column("analysis_runs", "run_metadata")
    op.drop_column("analysis_runs", "job_id")
    op.drop_column("analysis_runs", "plugin_profile")
    op.drop_column("analysis_runs", "execution_mode")
    op.drop_column("documents", "provider_summary")
    op.drop_column("documents", "modality_status")
