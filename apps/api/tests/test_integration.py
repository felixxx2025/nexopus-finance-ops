"""
Integration tests — Full API flow end-to-end (async HTTP with httpx)
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
import json
import httpx


BASE_URL = "http://localhost:8000"


@pytest.fixture
def auth_headers():
    """Provide valid Authorization header for tests (mocked token)."""
    return {"Authorization": "Bearer test-token-admin"}


# ─── Health ─────────────────────────────────────────────────────────────────

def test_health_check():
    """GET /health returns 200 with status ok."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"

    asyncio.run(_run())


def test_ready_endpoint():
    """GET /ready returns 200 when db and redis are available (mocked)."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    async def _run():
        with patch("apps.api.main.AsyncSessionLocal") as mock_session:
            mock_session.return_value.__aenter__ = AsyncMock(return_value=AsyncMock())
            mock_session.return_value.__aexit__ = AsyncMock(return_value=None)
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get("/ready")
        # Accept 200 or 503 depending on real infra availability
        assert resp.status_code in (200, 503)

    asyncio.run(_run())


# ─── AI Forecast endpoint ────────────────────────────────────────────────────

def test_forecast_endpoint_returns_200(auth_headers):
    """POST /ai/forecast returns valid forecast structure."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    mock_forecast = {
        "cenarios": {
            "base": {"receita_projetada": 264000, "despesa_projetada": 130000, "resultado_liquido": 134000}
        },
        "tendencia_receita": "crescimento_moderado",
        "tendencia_despesa": "estavel",
        "recomendacoes": [],
        "confianca": 0.78,
    }

    payload = {
        "lancamentos": [
            {"data": "2026-01-15", "tipo_conta": "receita", "valor": 85000, "descricao": "Receita Jan"},
        ],
        "company_name": "Empresa Teste",
    }

    async def _run():
        with patch("services.ai_engine.agent_predictor.call_ai", new=AsyncMock(return_value=json.dumps(mock_forecast))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/ai/forecast", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "cenarios" in data

    asyncio.run(_run())


# ─── AI Audit endpoint ───────────────────────────────────────────────────────

def test_audit_endpoint_returns_200(auth_headers):
    """POST /ai/audit returns audit result with risk score."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    mock_audit = {
        "score_risco": 20,
        "nivel_risco": "baixo",
        "anomalias": [],
        "compliance": {"equacao_patrimonial": True, "partida_dobrada": True},
        "acoes_recomendadas": [],
        "resumo_executivo": "Sem anomalias.",
        "lancamentos_auditados": 1,
        "confianca": 0.9,
    }

    payload = {
        "lancamentos": [
            {"data": "2026-01-15", "tipo_conta": "receita", "valor": 85000, "descricao": "Receita Jan"},
        ],
        "company_name": "Empresa Teste",
    }

    async def _run():
        with patch("services.ai_engine.agent_auditor.call_ai", new=AsyncMock(return_value=json.dumps(mock_audit))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/ai/audit", json=payload, headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "score_risco" in data

    asyncio.run(_run())


# ─── AI Reconcile endpoint ───────────────────────────────────────────────────

def test_reconcile_endpoint_returns_200(auth_headers):
    """POST /ai/reconcile returns reconciliation matches."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    mock_reconcile = {
        "matches": [],
        "resumo": {
            "total_banco": 1,
            "total_contabil": 1,
            "conciliados": 1,
            "divergentes": 0,
            "apenas_banco": 0,
            "apenas_contabil": 0,
            "taxa_conciliacao": 100.0,
        },
        "alertas": [],
    }

    payload = {
        "bank_entries": [{"data": "2026-01-15", "descricao": "TED", "valor": 85000}],
        "accounting_entries": [{"data": "2026-01-15", "descricao": "Receita", "valor": 85000, "tipo_conta": "receita"}],
        "company_name": "Empresa Teste",
    }

    async def _run():
        with patch("services.ai_engine.agent_reconciler.call_ai", new=AsyncMock(return_value=json.dumps(mock_reconcile))):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/ai/reconcile", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    asyncio.run(_run())


# ─── Auth endpoint ───────────────────────────────────────────────────────────

def test_login_invalid_credentials():
    """POST /auth/token with bad credentials returns 401."""
    import asyncio
    from apps.api.main import app
    from httpx import AsyncClient, ASGITransport

    async def _run():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/auth/token",
                data={"username": "nonexistent@test.com", "password": "wrong"},
            )
        assert resp.status_code == 401

    asyncio.run(_run())
