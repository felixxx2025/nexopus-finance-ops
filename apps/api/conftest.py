"""
conftest.py — configurações globais de teste.

Define variáveis de ambiente ANTES de qualquer import do módulo main/config,
garantindo que settings e _user_db sejam inicializados com valores de teste.
"""
import os
import sys
from pathlib import Path

# Adiciona diretórios ao PYTHONPATH para testes
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "apps"))
sys.path.insert(0, str(project_root / "services"))
sys.path.insert(0, str(project_root / "packages"))

# Deve ser executado antes de qualquer import de main ou config
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!!")
os.environ.setdefault("ADMIN_USERNAME", "admin")
os.environ.setdefault("ADMIN_PASSWORD", "admin")
os.environ.setdefault("DOCS_ENABLED", "true")
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
