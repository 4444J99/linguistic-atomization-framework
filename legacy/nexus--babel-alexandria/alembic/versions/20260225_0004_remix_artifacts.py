"""Add remix artifact persistence tables

Revision ID: 20260225_0004
Revises: 20260223_0003
Create Date: 2026-02-25 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260225_0004"
down_revision = "20260223_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "remix_artifacts",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("source_document_id", sa.String(length=36), nullable=True),
        sa.Column("source_branch_id", sa.String(length=36), nullable=True),
        sa.Column("target_document_id", sa.String(length=36), nullable=True),
        sa.Column("target_branch_id", sa.String(length=36), nullable=True),
        sa.Column("strategy", sa.String(length=64), nullable=False),
        sa.Column("seed", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=16), nullable=False),
        sa.Column("remixed_text", sa.Text(), nullable=False),
        sa.Column("text_hash", sa.String(length=128), nullable=False),
        sa.Column("rng_seed_hex", sa.String(length=128), nullable=False),
        sa.Column("payload_hash", sa.String(length=128), nullable=False),
        sa.Column("create_branch", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("branch_event_id", sa.String(length=36), nullable=True),
        sa.Column("governance_decision_id", sa.String(length=36), nullable=True),
        sa.Column("lineage_graph_refs", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("artifact_metadata", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["branch_event_id"], ["branch_events.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["governance_decision_id"], ["policy_decisions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_remix_artifacts_source_document_id", "remix_artifacts", ["source_document_id"])
    op.create_index("ix_remix_artifacts_source_branch_id", "remix_artifacts", ["source_branch_id"])
    op.create_index("ix_remix_artifacts_target_document_id", "remix_artifacts", ["target_document_id"])
    op.create_index("ix_remix_artifacts_target_branch_id", "remix_artifacts", ["target_branch_id"])
    op.create_index("ix_remix_artifacts_strategy", "remix_artifacts", ["strategy"])
    op.create_index("ix_remix_artifacts_mode", "remix_artifacts", ["mode"])
    op.create_index("ix_remix_artifacts_text_hash", "remix_artifacts", ["text_hash"])
    op.create_index("ix_remix_artifacts_payload_hash", "remix_artifacts", ["payload_hash"])
    op.create_index("ix_remix_artifacts_branch_id", "remix_artifacts", ["branch_id"])
    op.create_index("ix_remix_artifacts_branch_event_id", "remix_artifacts", ["branch_event_id"])
    op.create_index("ix_remix_artifacts_governance_decision_id", "remix_artifacts", ["governance_decision_id"])
    op.create_index("ix_remix_artifacts_created_at", "remix_artifacts", ["created_at"])

    op.create_table(
        "remix_source_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("remix_artifact_id", sa.String(length=36), nullable=False),
        sa.Column("role", sa.String(length=16), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=True),
        sa.Column("branch_id", sa.String(length=36), nullable=True),
        sa.Column("atom_level", sa.String(length=32), nullable=True),
        sa.Column("atom_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("atom_refs", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["remix_artifact_id"], ["remix_artifacts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["branch_id"], ["branches.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("remix_artifact_id", "role", name="uq_remix_source_role"),
    )
    op.create_index("ix_remix_source_links_remix_artifact_id", "remix_source_links", ["remix_artifact_id"])
    op.create_index("ix_remix_source_links_role", "remix_source_links", ["role"])
    op.create_index("ix_remix_source_links_document_id", "remix_source_links", ["document_id"])
    op.create_index("ix_remix_source_links_branch_id", "remix_source_links", ["branch_id"])


def downgrade() -> None:
    op.drop_index("ix_remix_source_links_branch_id", table_name="remix_source_links")
    op.drop_index("ix_remix_source_links_document_id", table_name="remix_source_links")
    op.drop_index("ix_remix_source_links_role", table_name="remix_source_links")
    op.drop_index("ix_remix_source_links_remix_artifact_id", table_name="remix_source_links")
    op.drop_table("remix_source_links")

    op.drop_index("ix_remix_artifacts_created_at", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_governance_decision_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_branch_event_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_branch_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_payload_hash", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_text_hash", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_mode", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_strategy", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_target_branch_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_target_document_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_source_branch_id", table_name="remix_artifacts")
    op.drop_index("ix_remix_artifacts_source_document_id", table_name="remix_artifacts")
    op.drop_table("remix_artifacts")

