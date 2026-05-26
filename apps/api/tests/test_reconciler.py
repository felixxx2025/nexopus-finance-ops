"""
Tests for agent_reconciler — Bank Reconciliation Agent
"""
import pytest
from unittest.mock import patch, AsyncMock
import json


@pytest.fixture
def bank_entries():
    return [
        {"data": "2026-01-15", "descricao": "TED Recebido ABC", "valor": 85000},
        {"data": "2026-01-20", "descricao": "Débito Folha", "valor": 42000},
        {"data": "2026-02-10", "descricao": "Pix Recebido XYZ", "valor": 91000},
    ]


@pytest.fixture
def accounting_entries():
    return [
        {"data": "2026-01-15", "descricao": "Receita ABC", "valor": 85000, "tipo_conta": "receita"},
        {"data": "2026-01-20", "descricao": "Folha Pagamento", "valor": 42000, "tipo_conta": "despesa"},
        {"data": "2026-04-01", "descricao": "Despesa extra", "valor": 35000, "tipo_conta": "despesa"},
    ]


@pytest.mark.asyncio
async def test_reconcile_success(bank_entries, accounting_entries):
    """AI agent returns structured reconciliation."""
    from services.ai_engine.agent_reconciler import reconcile

    mock_response = {
        "matches": [
            {"banco": bank_entries[0], "contabil": accounting_entries[0], "status": "CONCILIADO", "diferenca_valor": 0},
            {"banco": bank_entries[1], "contabil": accounting_entries[1], "status": "CONCILIADO", "diferenca_valor": 0},
            {"banco": bank_entries[2], "contabil": None, "status": "APENAS_BANCO", "observacao": "Sem match contábil"},
            {"banco": None, "contabil": accounting_entries[2], "status": "APENAS_CONTABIL"},
        ],
        "resumo": {
            "total_banco": 3,
            "total_contabil": 3,
            "conciliados": 2,
            "divergentes": 0,
            "apenas_banco": 1,
            "apenas_contabil": 1,
            "taxa_conciliacao": 66.7,
        },
        "alertas": ["1 lançamento bancário sem correspondência contábil"],
    }

    with patch(
        "services.ai_engine.agent_reconciler.call_ai",
        new=AsyncMock(return_value=json.dumps(mock_response)),
    ):
        result = await reconcile(bank_entries, accounting_entries, "Empresa Teste")

    assert len(result["matches"]) == 4
    assert result["resumo"]["conciliados"] == 2
    assert result["resumo"]["taxa_conciliacao"] > 0


@pytest.mark.asyncio
async def test_reconcile_fallback(bank_entries, accounting_entries):
    """Falls back to local matcher when AI call fails."""
    from services.ai_engine.agent_reconciler import reconcile

    with patch(
        "services.ai_engine.agent_reconciler.call_ai",
        new=AsyncMock(side_effect=Exception("timeout")),
    ):
        result = await reconcile(bank_entries, accounting_entries, "Empresa Teste")

    assert "matches" in result
    assert "resumo" in result


def test_simple_match(bank_entries, accounting_entries):
    """_simple_match correctly pairs entries by date and amount."""
    from services.ai_engine.agent_reconciler import _simple_match

    result = _simple_match(bank_entries, accounting_entries)
    matched = [m for m in result["matches"] if m["status"] == "CONCILIADO"]
    # Jan 15 and Jan 20 should match (same date + value)
    assert len(matched) >= 2


@pytest.mark.asyncio
async def test_reconcile_empty_inputs():
    """Handles empty datasets gracefully."""
    from services.ai_engine.agent_reconciler import reconcile

    result = await reconcile([], [], "Empresa Vazia")
    assert "matches" in result
    assert result["resumo"]["total_banco"] == 0
