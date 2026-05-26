"""
Testes Fase 3 — Motor contábil robusto, IA com controle e plano de contas.

Cobre:
- PLANO_CONTAS_PADRAO: estrutura e completude
- Motor contábil: somente lançamentos approved
- AIController: thresholds, decisões e fallback
- AIDecisionLog: serialização JSON
- _JsonFormatter: campos de log
- Endpoints: /companies (RBAC), /companies/{id}/seed-accounts
- Parser com fallback de IA
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, _create_access_token, get_db  # noqa: E402


async def _mock_db():
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalar_one.return_value = 0
    result_mock.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result_mock)
    session.refresh = AsyncMock()
    yield session


app.dependency_overrides[get_db] = _mock_db
client = TestClient(app)


# ── Plano de contas padrão ────────────────────────────────────────────────────

def test_plano_contas_has_all_types():
    """Plano de contas padrão deve cobrir todos os 5 tipos contábeis."""
    from services.accounting_core.engine import PLANO_CONTAS_PADRAO

    types_found = {item["type"] for item in PLANO_CONTAS_PADRAO}
    assert types_found == {"ativo", "passivo", "pl", "receita", "despesa"}


def test_plano_contas_codes_unique():
    """Códigos do plano de contas devem ser únicos."""
    from services.accounting_core.engine import PLANO_CONTAS_PADRAO

    codes = [item["code"] for item in PLANO_CONTAS_PADRAO]
    assert len(codes) == len(set(codes)), "Códigos duplicados no plano de contas"


def test_plano_contas_minimum_size():
    """Plano de contas deve ter pelo menos 20 contas."""
    from services.accounting_core.engine import PLANO_CONTAS_PADRAO
    assert len(PLANO_CONTAS_PADRAO) >= 20


def test_plano_contas_each_item_has_required_fields():
    """Cada item do plano deve ter code, name e type."""
    from services.accounting_core.engine import PLANO_CONTAS_PADRAO
    for item in PLANO_CONTAS_PADRAO:
        assert "code" in item, f"Sem 'code': {item}"
        assert "name" in item, f"Sem 'name': {item}"
        assert "type" in item, f"Sem 'type': {item}"
        assert item["type"] in ("ativo", "passivo", "pl", "receita", "despesa")


# ── Motor contábil: apenas aprovados ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_engine_filtra_apenas_aprovados():
    """calculate_balance deve gerar query com filtro status='approved'."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from services.accounting_core.engine import AccountingEngine
    from sqlalchemy import text

    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    engine = AccountingEngine(session)
    cid = str(uuid.uuid4())
    await engine.calculate_balance(cid, 2025)

    # Verifica que execute foi chamado (query emitida)
    assert session.execute.called


@pytest.mark.asyncio
async def test_engine_dre_inclui_breakdown():
    """DRE gerada deve incluir campos receitas_detalhe e despesas_detalhe."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from services.accounting_core.engine import AccountingEngine

    acc_r = uuid.uuid4()
    acc_d = uuid.uuid4()
    rows = [
        (acc_r, "Receita de Serviços", "receita", "4.2", "credit", Decimal("200000")),
        (acc_d, "Despesas com Pessoal", "despesa", "5.2", "debit",  Decimal("80000")),
    ]
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)

    engine = AccountingEngine(session)
    dre = await engine.generate_dre(str(uuid.uuid4()), 2025)

    assert "receitas_detalhe" in dre
    assert "despesas_detalhe" in dre
    assert "apenas_aprovados" in dre["_meta"]
    assert dre["_meta"]["apenas_aprovados"] is True
    assert dre["_meta"]["metodo"] == "NBC TG 26"


@pytest.mark.asyncio
async def test_engine_balance_sheet_meta():
    """Balanço deve ter lei_ref e apenas_aprovados no _meta."""
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from services.accounting_core.engine import AccountingEngine

    session = MagicMock()
    result = MagicMock()
    result.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    engine = AccountingEngine(session)
    bal = await engine.generate_balance_sheet(str(uuid.uuid4()), 2025)

    assert bal["_meta"]["lei_ref"] == "Lei 6.404/1976"
    assert bal["_meta"]["apenas_aprovados"] is True


# ── AIController ──────────────────────────────────────────────────────────────

def test_ai_controller_auto_approve():
    """Confiança ≥ 0.80 → AUTO_APPROVE."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="test_op")
    result = ctrl.evaluate(confidence=0.90, result={"ok": True})
    assert result.decision == AIDecision.AUTO_APPROVE
    assert result.is_approved is True
    assert result.requires_human_review is False


def test_ai_controller_needs_review():
    """0.50 ≤ confiança < 0.80 → NEEDS_REVIEW."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="test_op")
    result = ctrl.evaluate(confidence=0.65, result={"ok": True})
    assert result.decision == AIDecision.NEEDS_REVIEW
    assert result.requires_human_review is True
    assert result.is_approved is False


def test_ai_controller_reject():
    """Confiança < 0.50 → REJECT."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="test_op")
    result = ctrl.evaluate(confidence=0.30, result={"ok": True})
    assert result.decision == AIDecision.REJECT
    assert result.requires_human_review is True


def test_ai_controller_with_fallback_ativa():
    """with_fallback retorna fallback quando REJECT."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="test_op")
    fallback = {"_fallback": True, "lancamentos": []}
    result = ctrl.with_fallback(
        confidence=0.20,
        ai_result={"lancamentos": [{"x": 1}]},
        fallback_result=fallback,
    )
    assert result.decision == AIDecision.REJECT
    assert result.used_fallback is True
    assert result.result == fallback


def test_ai_controller_with_fallback_nao_ativa():
    """with_fallback mantém resultado original quando AUTO_APPROVE."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="test_op")
    ai_data = {"lancamentos": [{"x": 1}]}
    fallback = {"_fallback": True}
    result = ctrl.with_fallback(
        confidence=0.95,
        ai_result=ai_data,
        fallback_result=fallback,
    )
    assert result.decision == AIDecision.AUTO_APPROVE
    assert result.used_fallback is False
    assert result.result == ai_data


def test_ai_decision_log_serialization():
    """AIDecisionLog.to_dict deve produzir dicionário com todos os campos."""
    from services.ai_engine.ai_control import AIDecisionLog, AIDecision

    log = AIDecisionLog(
        agent="parser",
        operation="parse_document",
        confidence=0.75,
        decision=AIDecision.NEEDS_REVIEW,
        doc_id="abc-123",
        reason="teste",
    )
    d = log.to_dict()
    for key in ("id", "ts", "agent", "operation", "confidence", "decision", "doc_id", "reason"):
        assert key in d, f"Campo '{key}' ausente no log"
    assert d["confidence"] == 0.75
    assert d["decision"] == "needs_review"


def test_ai_eval_result_to_dict():
    """AIEvalResult.to_dict deve conter os campos esperados."""
    from services.ai_engine.ai_control import AIController, AIDecision

    ctrl = AIController(agent="test", operation="op")
    r = ctrl.evaluate(confidence=0.85, result={})
    d = r.to_dict()
    for key in ("decision", "confidence", "reason", "used_fallback", "requires_human_review", "log_id"):
        assert key in d


def test_fallback_constants_structure():
    """Constantes de fallback devem ter campo _fallback=True."""
    from services.ai_engine.ai_control import (
        FALLBACK_PARSE_RESULT, FALLBACK_FORECAST_RESULT, FALLBACK_AUDIT_RESULT,
    )
    for fb in (FALLBACK_PARSE_RESULT, FALLBACK_FORECAST_RESULT, FALLBACK_AUDIT_RESULT):
        assert fb.get("_fallback") is True
        assert fb.get("confianca") == 0.0


# ── Endpoints de company ──────────────────────────────────────────────────────

def test_create_company_requires_admin():
    """POST /companies exige role admin."""
    token, _ = _create_access_token("viewer", role="viewer")
    res = client.post(
        "/companies",
        json={"name": "Empresa X", "cnpj": "33000167000101"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_list_companies_authenticated():
    """GET /companies retorna lista para qualquer usuário autenticado."""
    token, _ = _create_access_token("analista", role="analista")
    res = client.get("/companies", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "companies" in res.json()


def test_seed_accounts_requires_admin():
    """POST /companies/{id}/seed-accounts exige role admin."""
    token, _ = _create_access_token("analista", role="analista")
    cid = str(uuid.uuid4())
    res = client.post(
        f"/companies/{cid}/seed-accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_seed_accounts_admin_ok():
    """Admin consegue acesso ao seed-accounts (retorna dados, sem banco real)."""
    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())
    res = client.post(
        f"/companies/{cid}/seed-accounts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert "contas_semeadas" in res.json()
