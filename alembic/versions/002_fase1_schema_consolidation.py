"""Fase 1 — Schema consolidation: document status, review fields, users, audit_logs.

Revision ID: 002
Revises: 001
Create Date: 2026-05-26 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── documents: novos campos ───────────────────────────────────────────────
    op.add_column("documents", sa.Column("original_filename", sa.Text(), nullable=True))
    op.add_column(
        "documents",
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="uploaded",
        ),
    )
    op.create_check_constraint(
        "documents_status_check",
        "documents",
        "status IN ('uploaded','processing','processed','failed','needs_review')",
    )
    op.add_column("documents", sa.Column("error_message", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("ai_confidence", sa.Numeric(4, 3), nullable=True))
    op.add_column(
        "documents",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_documents_status", "documents", ["status"])

    # ── journal_entries: campos de revisão humana ─────────────────────────────
    op.add_column(
        "journal_entries",
        sa.Column("status", sa.String(20), nullable=False, server_default="approved"),
    )
    op.create_check_constraint(
        "journal_entries_status_check",
        "journal_entries",
        "status IN ('draft','approved','rejected')",
    )
    op.add_column("journal_entries", sa.Column("review_note", sa.Text(), nullable=True))
    op.add_column("journal_entries", sa.Column("reviewed_by", sa.String(100), nullable=True))
    op.add_column("journal_entries", sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("journal_entries", sa.Column("ai_generated", sa.Boolean(), nullable=False, server_default="FALSE"))
    op.add_column("journal_entries", sa.Column("ai_confidence", sa.Numeric(4, 3), nullable=True))
    op.add_column("journal_entries", sa.Column("created_by", sa.String(100), nullable=True))
    op.add_column(
        "journal_entries",
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_journal_entries_status", "journal_entries", ["status"])

    # ── reports: versionamento e aprovação ────────────────────────────────────
    op.add_column("reports", sa.Column("version", sa.Integer(), nullable=False, server_default="1"))
    op.add_column(
        "reports",
        sa.Column("status", sa.String(20), nullable=False, server_default="preliminary"),
    )
    op.create_check_constraint(
        "reports_status_check",
        "reports",
        "status IN ('preliminary','approved','closed')",
    )
    op.add_column("reports", sa.Column("approved_by", sa.String(100), nullable=True))
    op.add_column("reports", sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "reports",
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # ── users ─────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="TRUE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("role IN ('admin','analista','viewer')", name="users_role_check"),
    )

    # ── user_companies ────────────────────────────────────────────────────────
    op.create_table(
        "user_companies",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="viewer"),
        sa.CheckConstraint("role IN ('admin','analista','viewer')", name="user_companies_role_check"),
    )

    # ── audit_logs ────────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("username", sa.String(100), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_logs_username", "audit_logs", ["username"])
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_created", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("user_companies")
    op.drop_table("users")

    op.drop_index("idx_journal_entries_status")
    for col in ["created_at", "created_by", "ai_confidence", "ai_generated", "reviewed_at", "reviewed_by", "review_note", "status"]:
        op.drop_column("journal_entries", col)

    op.drop_index("idx_documents_status")
    for col in ["updated_at", "ai_confidence", "error_message", "status", "original_filename"]:
        op.drop_column("documents", col)

    for col in ["updated_at", "approved_at", "approved_by", "status", "version"]:
        op.drop_column("reports", col)
