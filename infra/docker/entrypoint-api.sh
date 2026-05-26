#!/bin/sh
# entrypoint-api.sh — roda migrações Alembic antes de iniciar o servidor

set -e

echo "[entrypoint] Rodando migrações Alembic..."
alembic upgrade head

echo "[entrypoint] Iniciando Nexopus Finance API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
