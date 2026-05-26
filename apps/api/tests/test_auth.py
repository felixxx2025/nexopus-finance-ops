"""
Testes de autenticação — login, JWT validation, endpoints protegidos.
"""
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from main import app, _create_access_token, get_db  # noqa: E402


# Mock da sessão de banco para evitar conexão real durante testes
async def _mock_db():
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    yield session


app.dependency_overrides[get_db] = _mock_db

client = TestClient(app)


# ── Login ──────────────────────────────────────────────────────────────────────

def test_login_success():
    """POST /auth/token com credenciais válidas retorna token."""
    res = client.post("/auth/token", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20


def test_login_wrong_password():
    """POST /auth/token com senha errada retorna 401."""
    res = client.post("/auth/token", json={"username": "admin", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["detail"] == "Credenciais inválidas"


def test_login_wrong_user():
    """POST /auth/token com usuário inexistente retorna 401."""
    res = client.post("/auth/token", json={"username": "hacker", "password": "admin"})
    assert res.status_code == 401


def test_login_missing_fields():
    """POST /auth/token sem body retorna 422 (Unprocessable Entity)."""
    res = client.post("/auth/token", json={})
    assert res.status_code == 422


# ── Endpoints protegidos ───────────────────────────────────────────────────────

def test_upload_requires_auth():
    """POST /documents/upload sem token retorna 401."""
    fresh = TestClient(app, cookies={})
    res = fresh.post("/documents/upload", files={"file": ("test.pdf", b"content", "application/pdf")})
    assert res.status_code in (401, 403)


def test_upload_with_invalid_token():
    """POST /documents/upload com token inválido retorna 401."""
    res = client.post(
        "/documents/upload",
        files={"file": ("test.pdf", b"content", "application/pdf")},
        headers={"Authorization": "Bearer invalid.token.here"},
    )
    assert res.status_code == 401


def test_upload_with_valid_token_wrong_mime():
    """Upload com token válido mas MIME inválido retorna 415."""
    import uuid as _uuid
    token, _ = _create_access_token("admin")
    cid = str(_uuid.uuid4())
    res = client.post(
        f"/documents/upload?company_id={cid}",
        files={"file": ("test.exe", b"content", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 415


def test_upload_with_valid_token_valid_file():
    """Upload com token válido e PDF retorna 200 com doc_id."""
    import uuid as _uuid
    import unittest.mock as mock
    import main as main_module

    token, _ = _create_access_token("admin")
    cid = str(_uuid.uuid4())

    def _fake_upload(key, contents, content_type):
        return f"http://localhost:9000/bucket/{key}"

    with mock.patch.object(main_module, "_upload_to_s3", side_effect=_fake_upload):
        res = client.post(
            f"/documents/upload?company_id={cid}",
            files={"file": ("relatorio.pdf", b"%PDF-1.4 fake content", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "doc_id" in data
    assert data["status"] == "processing"
    assert data["filename"] == "relatorio.pdf"


def test_dre_requires_auth():
    """GET /reports/dre sem token retorna 401."""
    fresh = TestClient(app, cookies={})
    res = fresh.get("/reports/dre/some-id/2025")
    assert res.status_code in (401, 403)


def test_balance_requires_auth():
    """GET /reports/balance sem token retorna 401."""
    fresh = TestClient(app, cookies={})
    res = fresh.get("/reports/balance/some-id/2025")
    assert res.status_code in (401, 403)


# ── JWT direto ────────────────────────────────────────────────────────────────

def test_jwt_decode_valid():
    """Token gerado pelo _create_access_token deve ser aceito como Bearer."""
    from jose import jwt as jose_jwt
    from apps.api.config import settings as cfg

    token, jti = _create_access_token("testuser")
    payload = jose_jwt.decode(token, cfg.secret_key, algorithms=[cfg.algorithm])
    assert payload["sub"] == "testuser"
    assert payload["jti"] == jti


def test_jwt_expired_token_rejected():
    """Token expirado deve ser rejeitado com 401."""
    from datetime import datetime, timedelta, timezone
    from jose import jwt as jose_jwt
    from apps.api.config import settings as cfg

    expired_payload = {
        "sub": "admin",
        "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
    }
    expired_token = jose_jwt.encode(expired_payload, cfg.secret_key, algorithm=cfg.algorithm)

    res = client.post(
        "/documents/upload",
        files={"file": ("test.pdf", b"content", "application/pdf")},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
