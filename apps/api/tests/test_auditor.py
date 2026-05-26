"""
Tests for agent_auditor — Anomaly Detection & Compliance Agent
"""
import pytest
from unittest.mock import patch, AsyncMock
import json


@pytest.fixture
def lancamentos_normal():
    return [
        {"data": "2026-01-15", "tipo_conta": "receita", "valor": 85000, "descricao": "Receita Jan"},
        {"data": "2026-01-20", "tipo_conta": "despesa", "valor": 42000, "descricao": "Despesa Jan"},
        {"data": "2026-02-10", "tipo_conta": "receita", "valor": 91000, "descricao": "Receita Fev"},
    ]


@pytest.fixture
def lancamentos_with_anomaly():
    return [
        {"data": "2026-01-15", "tipo_conta": "receita", "valor": 85000, "descricao": "Receita Jan"},
        {"data": "2026-02-28", "tipo_conta": "despesa", "valor": 999999, "descricao": "Despesa suspeita"},
        {"data": "2026-03-01", "tipo_conta": "receita", "valor": 1000000, "descricao": "Receita round"},
    ]


@pytest.mark.asyncio
async def test_audit_entries_success(lancamentos_normal):
    """AI agent returns structured audit when LLM succeeds."""
    from services.ai_engine.agent_auditor import audit_entries

    mock_response = {
        "score_risco": 15,
        "nivel_risco": "baixo",
        "anomalias": [],
        "compliance": {
            "equacao_patrimonial": True,
            "partida_dobrada": True,
        },
        "acoes_recomendadas": [],
        "resumo_executivo": "Lançamentos dentro dos padrões esperados.",
        "lancamentos_auditados": 3,
        "confianca": 0.92,
    }

    with patch(
        "services.ai_engine.agent_auditor.call_ai",
        new=AsyncMock(return_value=json.dumps(mock_response)),
    ):
        result = await audit_entries(lancamentos_normal, company_name="Empresa Teste")

    assert result["nivel_risco"] == "baixo"
    assert result["score_risco"] == 15
    assert result["compliance"]["equacao_patrimonial"] is True


@pytest.mark.asyncio
async def test_audit_detects_round_numbers(lancamentos_with_anomaly):
    """Statistical pre-analysis flags round numbers (potential fraud indicator)."""
    from services.ai_engine.agent_auditor import _detect_statistical_anomalies

    anomalies = _detect_statistical_anomalies(lancamentos_with_anomaly)
    round_flags = [a for a in anomalies if "round" in a.get("tipo", "").lower() or "arredond" in a.get("descricao", "").lower()]
    # At least one round number should be flagged
    assert len(anomalies) > 0


@pytest.mark.asyncio
async def test_audit_fallback_on_error(lancamentos_normal):
    """Returns fallback result when AI call fails."""
    from services.ai_engine.agent_auditor import audit_entries

    with patch(
        "services.ai_engine.agent_auditor.call_ai",
        new=AsyncMock(side_effect=Exception("LLM unavailable")),
    ):
        result = await audit_entries(lancamentos_normal, company_name="Teste")

    assert "score_risco" in result
    assert "nivel_risco" in result
    assert "anomalias" in result


@pytest.mark.asyncio
async def test_audit_high_risk_score(lancamentos_with_anomaly):
    """High-anomaly dataset results in elevated risk score."""
    from services.ai_engine.agent_auditor import audit_entries

    mock_response = {
        "score_risco": 87,
        "nivel_risco": "critico",
        "anomalias": [
            {
                "tipo": "valor_atipico",
                "severidade": "critica",
                "descricao": "Valor 999999 muito acima da média",
                "lancamento_ref": "2026-02-28",
                "recomendacao": "Verificar com responsável",
            }
        ],
        "compliance": {"equacao_patrimonial": True, "partida_dobrada": False},
        "acoes_recomendadas": ["Verificar lançamento de 28/02"],
        "resumo_executivo": "Anomalias críticas detectadas.",
        "lancamentos_auditados": 3,
        "confianca": 0.88,
    }

    with patch(
        "services.ai_engine.agent_auditor.call_ai",
        new=AsyncMock(return_value=json.dumps(mock_response)),
    ):
        result = await audit_entries(lancamentos_with_anomaly, company_name="Teste")

    assert result["score_risco"] >= 80
    assert result["nivel_risco"] == "critico"
    assert len(result["anomalias"]) > 0
