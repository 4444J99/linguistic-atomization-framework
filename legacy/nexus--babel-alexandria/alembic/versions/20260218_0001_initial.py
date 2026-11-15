"""Initial Nexus Babel Alexandria schema

Revision ID: 20260218_0001
Revises:
Create Date: 2026-02-18 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260218_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingest_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("request_payload", sa.JSON(), nullable=False),
        sa.Column("result_summary", sa.JSON(), nullable=False),
        sa.Column("errors", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "documents",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("path", sa.String(length=1024), nullable=False),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("modality", sa.String(length=32), nullable=False),
        sa.Column("checksum", sa.String(length=128), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("ingested", sa.Boolean(), nullable=False),
        sa.Column("ingest_status", sa.String(length=32), nullable=False),
        sa.Column("conflict_flag", sa.Boolean(), nullable=False),
        sa.Column("conflict_reason", sa.String(length=256), nullable=True),
        sa.Column("provenance", sa.JSON(), nullable=False),
        sa.Column("atom_count", sa.Integer(), nullable=False),
        sa.Column("graph_projected_atom_count", sa.Integer(), nullable=False),
        sa.Column("graph_projection_status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("path"),
    )
    op.create_index(op.f("ix_documents_checksum"), "documents", ["checksum"], unique=False)
    op.create_index(op.f("ix_documents_modality"), "documents", ["modality"], unique=False)
    op.create_index(op.f("ix_documents_path"), "documents", ["path"], unique=True)

    op.create_table(
        "branches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("parent_branch_id", sa.String(length=36), nullable=True),
        sa.Column("root_document_id", sa.String(length=36), nullable=True),
        sa.Column("name", sa.String(length=256), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("created_by", sa.String(length=128), nullable=True),
        sa.Column("state_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["parent_branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["root_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_branches_parent_branch_id"), "branches", ["parent_branch_id"], unique=False)
    op.create_index(op.f("ix_branches_root_document_id"), "branches", ["root_document_id"], unique=False)

    op.create_table(
        "document_variants",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("variant_group", sa.String(length=128), nullable=False),
        sa.Column("variant_type", sa.String(length=64), nullable=False),
        sa.Column("related_document_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "variant_group",
            "variant_type",
            "related_document_id",
            name="uq_variant",
        ),
    )
    op.create_index(op.f("ix_document_variants_document_id"), "document_variants", ["document_id"], unique=False)
    op.create_index(op.f("ix_document_variants_variant_group"), "document_variants", ["variant_group"], unique=False)

    op.create_table(
        "atoms",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("atom_level", sa.String(length=32), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("atom_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_atoms_atom_level"), "atoms", ["atom_level"], unique=False)
    op.create_index(op.f("ix_atoms_document_id"), "atoms", ["document_id"], unique=False)

    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("layers", sa.JSON(), nullable=False),
        sa.Column("confidence", sa.JSON(), nullable=False),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_analysis_runs_branch_id"), "analysis_runs", ["branch_id"], unique=False)
    op.create_index(op.f("ix_analysis_runs_document_id"), "analysis_runs", ["document_id"], unique=False)

    op.create_table(
        "branch_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("branch_id", sa.String(length=36), nullable=False),
        sa.Column("event_index", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("event_payload", sa.JSON(), nullable=False),
        sa.Column("diff_summary", sa.JSON(), nullable=False),
        sa.Column("result_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_branch_events_branch_id"), "branch_events", ["branch_id"], unique=False)

    op.create_table(
        "mode_policies",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("policy", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("mode"),
    )

    op.create_table(
        "policy_decisions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("input_hash", sa.String(length=128), nullable=False),
        sa.Column("allow", sa.Boolean(), nullable=False),
        sa.Column("policy_hits", sa.JSON(), nullable=False),
        sa.Column("redactions", sa.JSON(), nullable=False),
        sa.Column("audit_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_policy_decisions_audit_id"), "policy_decisions", ["audit_id"], unique=False)
    op.create_index(op.f("ix_policy_decisions_input_hash"), "policy_decisions", ["input_hash"], unique=False)
    op.create_index(op.f("ix_policy_decisions_mode"), "policy_decisions", ["mode"], unique=False)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("username", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("key_hash", sa.String(length=128), nullable=False),
        sa.Column("owner", sa.String(length=128), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("key_hash"),
    )
    op.create_index(op.f("ix_api_keys_key_hash"), "api_keys", ["key_hash"], unique=True)
    op.create_index(op.f("ix_api_keys_owner"), "api_keys", ["owner"], unique=False)
    op.create_index(op.f("ix_api_keys_role"), "api_keys", ["role"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=128), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("actor", sa.String(length=128), nullable=False),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audit_logs_action"), "audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_audit_logs_mode"), "audit_logs", ["mode"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_logs_mode"), table_name="audit_logs")
    op.drop_index(op.f("ix_audit_logs_action"), table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index(op.f("ix_api_keys_role"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_owner"), table_name="api_keys")
    op.drop_index(op.f("ix_api_keys_key_hash"), table_name="api_keys")
    op.drop_table("api_keys")

    op.drop_table("users")

    op.drop_index(op.f("ix_policy_decisions_mode"), table_name="policy_decisions")
    op.drop_index(op.f("ix_policy_decisions_input_hash"), table_name="policy_decisions")
    op.drop_index(op.f("ix_policy_decisions_audit_id"), table_name="policy_decisions")
    op.drop_table("policy_decisions")

    op.drop_table("mode_policies")

    op.drop_index(op.f("ix_branch_events_branch_id"), table_name="branch_events")
    op.drop_table("branch_events")

    op.drop_index(op.f("ix_analysis_runs_document_id"), table_name="analysis_runs")
    op.drop_index(op.f("ix_analysis_runs_branch_id"), table_name="analysis_runs")
    op.drop_table("analysis_runs")

    op.drop_index(op.f("ix_atoms_document_id"), table_name="atoms")
    op.drop_index(op.f("ix_atoms_atom_level"), table_name="atoms")
    op.drop_table("atoms")

    op.drop_index(op.f("ix_document_variants_variant_group"), table_name="document_variants")
    op.drop_index(op.f("ix_document_variants_document_id"), table_name="document_variants")
    op.drop_table("document_variants")

    op.drop_index(op.f("ix_branches_root_document_id"), table_name="branches")
    op.drop_index(op.f("ix_branches_parent_branch_id"), table_name="branches")
    op.drop_table("branches")

    op.drop_index(op.f("ix_documents_path"), table_name="documents")
    op.drop_index(op.f("ix_documents_modality"), table_name="documents")
    op.drop_index(op.f("ix_documents_checksum"), table_name="documents")
    op.drop_table("documents")

    op.drop_table("ingest_jobs")
