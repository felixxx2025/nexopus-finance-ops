"""Base de Conhecimento Contábil com pgvector - RAG e Templates Estruturados.

Revision ID: 003
Revises: 002
Create Date: 2026-05-26 00:00:00.000000

Adiciona:
- knowledge_articles: artigos de conhecimento (normas, conceitos, exemplos)
- knowledge_embeddings: embeddings vetoriais (pgvector) para RAG
- report_templates: templates estruturados de relatórios
- account_templates: planos de contas padrão por setor
- glossary_terms: glossário de termos contábeis
- use_cases: casos de uso e cenários típicos
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Habilitar extensão pgvector ─────────────────────────────────────────────
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── knowledge_articles ───────────────────────────────────────────────────────
    op.create_table(
        "knowledge_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("subcategory", sa.String(50), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=False, server_default="pt-BR"),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("category IN ('norma','conceito','exemplo','caso_uso','glossario')", name="knowledge_articles_category_check"),
    )
    op.create_index("idx_knowledge_articles_category", "knowledge_articles", ["category"])
    op.create_index("idx_knowledge_articles_tags", "knowledge_articles", ["tags"], postgresql_using="gin")
    # Índice GIN para busca lexical (tsvector)
    op.execute("""
        CREATE INDEX idx_knowledge_articles_search 
        ON knowledge_articles 
        USING gin (to_tsvector('portuguese', title || ' ' || content))
    """)

    # ── knowledge_embeddings (pgvector) ───────────────────────────────────────────
    op.create_table(
        "knowledge_embeddings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("article_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("knowledge_articles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("embedding", postgresql.ARRAY(sa.Float()), nullable=False),  # Será alterado para vector depois
        sa.Column("model", sa.String(50), nullable=False, server_default="paraphrase-multilingual-MiniLM-L12-v2"),
        sa.Column("chunk_index", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    # Alterar coluna para tipo vector do pgvector
    op.execute("ALTER TABLE knowledge_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::vector(384)")
    # Índice HNSW para busca vetorial eficiente
    op.execute("""
        CREATE INDEX idx_knowledge_embeddings_embedding_hnsw 
        ON knowledge_embeddings 
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
    """)
    op.create_index("idx_knowledge_embeddings_article", "knowledge_embeddings", ["article_id"])

    # ── report_templates ────────────────────────────────────────────────────────
    op.create_table(
        "report_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("sector", sa.String(50), nullable=True),
        sa.Column("structure", postgresql.JSONB(), nullable=False),
        sa.Column("formulas", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="FALSE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("type IN ('dre','balanco','fluxo_caixa','mrr','lrr')", name="report_templates_type_check"),
    )
    op.create_index("idx_report_templates_type", "report_templates", ["type"])
    op.create_index("idx_report_templates_sector", "report_templates", ["sector"])

    # ── account_templates ───────────────────────────────────────────────────────
    op.create_table(
        "account_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("sector", sa.String(50), nullable=False),
        sa.Column("accounts", postgresql.JSONB(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default="FALSE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("sector IN ('servicos','comercio','industria','tecnologia','saude','outros')", name="account_templates_sector_check"),
    )
    op.create_index("idx_account_templates_sector", "account_templates", ["sector"])

    # ── glossary_terms ───────────────────────────────────────────────────────────
    op.create_table(
        "glossary_terms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("term", sa.Text(), nullable=False, unique=True),
        sa.Column("definition", sa.Text(), nullable=False),
        sa.Column("category", sa.String(50), nullable=True),
        sa.Column("related_terms", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("examples", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'")),
        sa.Column("language", sa.String(10), nullable=False, server_default="pt-BR"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_glossary_terms_term", "glossary_terms", ["term"])
    op.create_index("idx_glossary_terms_category", "glossary_terms", ["category"])

    # ── use_cases ────────────────────────────────────────────────────────────────
    op.create_table(
        "use_cases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("scenario", sa.Text(), nullable=False),
        sa.Column("steps", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("expected_outcome", sa.Text(), nullable=True),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("complexity", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("related_articles", postgresql.ARRAY(postgresql.UUID()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("complexity IN ('basic','medium','advanced')", name="use_cases_complexity_check"),
        sa.CheckConstraint("category IN ('abertura','operacao','relatorio','auditoria','fechamento')", name="use_cases_category_check"),
    )
    op.create_index("idx_use_cases_category", "use_cases", ["category"])
    op.create_index("idx_use_cases_complexity", "use_cases", ["complexity"])


def downgrade() -> None:
    op.drop_table("use_cases")
    op.drop_table("glossary_terms")
    op.drop_table("account_templates")
    op.drop_table("report_templates")
    op.drop_index("idx_knowledge_embeddings_article")
    op.execute("DROP INDEX IF EXISTS idx_knowledge_embeddings_embedding_hnsw")
    op.drop_table("knowledge_embeddings")
    op.drop_index("idx_knowledge_articles_tags")
    op.drop_index("idx_knowledge_articles_category")
    op.drop_table("knowledge_articles")
    op.execute("DROP EXTENSION IF EXISTS vector")
