"""
SQLAlchemy ORM models — espelham o schema.sql.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    cnpj: Mapped[str] = mapped_column(String(14), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    accounts: Mapped[list["Account"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    documents: Mapped[list["Document"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="company", cascade="all, delete-orphan")


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (UniqueConstraint("company_id", "code"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('ativo','passivo','receita','despesa','pl')"),
        nullable=False,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("accounts.id"), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="accounts")


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('draft','approved','rejected')"),
        nullable=False,
        default="approved",
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="journal_entries")
    items: Mapped[list["JournalItem"]] = relationship(back_populates="entry", cascade="all, delete-orphan")


class JournalItem(Base):
    __tablename__ = "journal_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entry_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("accounts.id"), nullable=False)
    type: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("type IN ('debit','credit')"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)

    entry: Mapped["JournalEntry"] = relationship(back_populates="items")
    account: Mapped["Account"] = relationship()


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    original_filename: Mapped[str | None] = mapped_column(Text, nullable=True)
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('pdf','excel','sped')"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('uploaded','processing','processed','failed','needs_review')"),
        nullable=False,
        default="uploaded",
    )
    parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence: Mapped[Decimal | None] = mapped_column(Numeric(4, 3), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="documents")


class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (UniqueConstraint("company_id", "type", "year"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('dre','balanco')"),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("status IN ('preliminary','approved','closed')"),
        nullable=False,
        default="preliminary",
    )
    approved_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="reports")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("role IN ('admin','analista','viewer')"),
        nullable=False,
        default="viewer",
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    companies: Mapped[list["UserCompany"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class UserCompany(Base):
    __tablename__ = "user_companies"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), primary_key=True)
    role: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("role IN ('admin','analista','viewer')"),
        nullable=False,
        default="viewer",
    )

    user: Mapped["User"] = relationship(back_populates="companies")
    company: Mapped["Company"] = relationship()


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ── Knowledge Base Models ────────────────────────────────────────────────────────


class KnowledgeArticle(Base):
    __tablename__ = "knowledge_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("category IN ('norma','conceito','exemplo','caso_uso','glossario')"),
        nullable=False,
    )
    subcategory: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="pt-BR")
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    embeddings: Mapped[list["KnowledgeEmbedding"]] = relationship(back_populates="article", cascade="all, delete-orphan")


class KnowledgeEmbedding(Base):
    __tablename__ = "knowledge_embeddings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    article_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False)
    embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    model: Mapped[str] = mapped_column(String(50), nullable=False, default="text-embedding-3-small")
    chunk_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    article: Mapped["KnowledgeArticle"] = relationship(back_populates="embeddings")


class ReportTemplate(Base):
    __tablename__ = "report_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("type IN ('dre','balanco','fluxo_caixa','mrr','lrr')"),
        nullable=False,
    )
    sector: Mapped[str | None] = mapped_column(String(50), nullable=True)
    structure: Mapped[dict] = mapped_column(JSONB, nullable=False)
    formulas: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class AccountTemplate(Base):
    __tablename__ = "account_templates"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    sector: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("sector IN ('servicos','comercio','industria','tecnologia','saude','outros')"),
        nullable=False,
    )
    accounts: Mapped[dict] = mapped_column(JSONB, nullable=False)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class GlossaryTerm(Base):
    __tablename__ = "glossary_terms"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    term: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    related_terms: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    examples: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="pt-BR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class UseCase(Base):
    __tablename__ = "use_cases"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scenario: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[dict] = mapped_column(JSONB, nullable=False)
    expected_outcome: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint("category IN ('abertura','operacao','relatorio','auditoria','fechamento')"),
        nullable=False,
    )
    complexity: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("complexity IN ('basic','medium','advanced')"),
        nullable=False,
        default="medium",
    )
    related_articles: Mapped[list[uuid.UUID] | None] = mapped_column(ARRAY(UUID), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
