"""Schema inicial — tabelas companies, accounts, journal_entries, journal_items, documents, reports.

Revision ID: 001
Revises: 
Create Date: 2026-05-05 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "companies",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("cnpj", sa.String(14), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=True),
        sa.CheckConstraint("type IN ('ativo','passivo','receita','despesa','pl')", name="accounts_type_check"),
        sa.UniqueConstraint("company_id", "code", name="uq_accounts_company_code"),
    )

    op.create_table(
        "journal_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    op.create_table(
        "journal_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("entry_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("accounts.id"), nullable=False),
        sa.Column("type", sa.String(10), nullable=False),
        sa.Column("amount", sa.Numeric(14, 2), nullable=False),
        sa.CheckConstraint("type IN ('debit','credit')", name="journal_items_type_check"),
        sa.CheckConstraint("amount > 0", name="journal_items_amount_positive"),
    )

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_url", sa.Text(), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("parsed", sa.Boolean(), nullable=False, server_default=sa.text("FALSE")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('pdf','excel','sped')", name="documents_type_check"),
    )

    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("companies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('dre','balanco')", name="reports_type_check"),
        sa.UniqueConstraint("company_id", "type", "year", name="uq_reports_company_type_year"),
    )

    # Índices de performance
    op.create_index("idx_journal_entries_company_date", "journal_entries", ["company_id", "date"])
    op.create_index("idx_journal_items_entry", "journal_items", ["entry_id"])
    op.create_index("idx_journal_items_account", "journal_items", ["account_id"])
    op.create_index("idx_documents_company", "documents", ["company_id"])
    op.create_index("idx_reports_company_type_year", "reports", ["company_id", "type", "year"])


def downgrade() -> None:
    op.drop_index("idx_reports_company_type_year")
    op.drop_index("idx_documents_company")
    op.drop_index("idx_journal_items_account")
    op.drop_index("idx_journal_items_entry")
    op.drop_index("idx_journal_entries_company_date")
    op.drop_table("reports")
    op.drop_table("documents")
    op.drop_table("journal_items")
    op.drop_table("journal_entries")
    op.drop_table("accounts")
    op.drop_table("companies")
