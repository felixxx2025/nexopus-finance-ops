"""
SQLAlchemy ORM models — espelham o schema.sql.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

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
    type: Mapped[str] = mapped_column(
        String(20),
        CheckConstraint("type IN ('pdf','excel','sped')"),
        nullable=False,
    )
    parsed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    company: Mapped["Company"] = relationship(back_populates="reports")
