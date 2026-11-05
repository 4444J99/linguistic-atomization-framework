"""Add metadata_json column to atoms for rich glyph-seed data

Revision ID: 20260223_0003
Revises: 20260218_0002
Create Date: 2026-02-23 00:00:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260223_0003"
down_revision = "20260218_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("atoms", sa.Column("metadata_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("atoms", "metadata_json")
