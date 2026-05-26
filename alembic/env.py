"""
Alembic env.py — configuração do ambiente de migração.

Lê DATABASE_URL da variável de ambiente (suporta both sync e async URLs).
Suporta modo online (conexão ativa) e offline (gera SQL puro).
"""
from __future__ import annotations

import os
import re
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# Importa os modelos para que o autogenerate detecte as tabelas
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from packages.db.models import Base  # noqa: E402

# ── Configuração do Alembic ───────────────────────────────────────────────────
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_sync_url() -> str:
    """
    Retorna a URL de conexão síncrona (psycopg2) para o Alembic.
    Converte 'postgresql+asyncpg://' → 'postgresql://' se necessário.
    """
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise RuntimeError(
            "DATABASE_URL não definida. "
            "Execute: export DATABASE_URL=postgresql://user:pass@host/db"
        )
    # Converte URL asyncpg → psycopg2 para uso síncrono do Alembic
    url = re.sub(r"^postgresql\+asyncpg://", "postgresql://", url)
    return url


def run_migrations_offline() -> None:
    """
    Modo offline: gera SQL puro sem conectar ao banco.
    Útil para revisar as migrations antes de aplicar.
    """
    url = _get_sync_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Modo online: conecta ao banco e aplica as migrations diretamente.
    """
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = _get_sync_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
