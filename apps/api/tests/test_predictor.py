"""
Tests for agent_predictor — Cashflow Forecast Agent
"""
import pytest
from unittest.mock import patch, AsyncMock
import json


@pytest.fixture
def lancamentos_sample():
    return [
        {"data": "2026-01-15", "tipo_conta": "receita", "valor": 85000, "descricao": "Receita Jan"},
        {"data": "2026-01-20", "tipo_conta": "despesa", "valor": 42000, "descricao": "Despesa Jan"},
        {"data": "2026-02-10", "tipo_conta": "receita", "valor": 91000, "descricao": "Receita Fev"},
        {"data": "2026-02-25", "tipo_conta": "despesa", "valor": 45000, "descricao": "Despesa Fev"},
        {"data": "2026-03-05", "tipo_conta": "receita", "valor": 88000, "descricao": "Receita Mar"},
        {"data": "2026-03-18", "tipo_conta": "despesa", "valor": 43000, "descricao": "Despesa Mar"},
    ]


@pytest.mark.asyncio
async def test_predict_cashflow_success(lancamentos_sample):
    """AI agent returns structured forecast when LLM succeeds."""
    from services.ai_engine.agent_predictor import predict_cashflow

    mock_response = {
        "cenarios": {
            "otimista": {"receita_projetada": 300000, "despesa_projetada": 130000, "resultado_liquido": 170000},
            "base": {"receita_projetada": 264000, "despesa_projetada": 130000, "resultado_liquido": 134000},
            "pessimista": {"receita_projetada": 220000, "despesa_projetada": 135000, "resultado_liquido": 85000},
        },
        "tendencia_receita": "crescimento_moderado",
        "tendencia_despesa": "estavel",
        "recomendacoes": ["Manter reserva de caixa mínima de 60 dias"],
        "confianca": 0.78,
        "narrativa": "Com base na tendência histórica...",
        "projecoes_mensais": [],
    }

    with patch(
        "services.ai_engine.agent_predictor.call_ai",
        new=AsyncMock(return_value=json.dumps(mock_response)),
    ):
        result = await predict_cashflow(lancamentos_sample, "Empresa Teste")

    assert result["cenarios"]["base"]["receita_projetada"] == 264000
    assert result["tendencia_receita"] == "crescimento_moderado"
    assert 0 <= result["confianca"] <= 1
    assert "recomendacoes" in result


@pytest.mark.asyncio
async def test_predict_cashflow_fallback_on_ai_error(lancamentos_sample):
    """Falls back to statistical model when AI call fails."""
    from services.ai_engine.agent_predictor import predict_cashflow

    with patch(
        "services.ai_engine.agent_predictor.call_ai",
        new=AsyncMock(side_effect=Exception("AI timeout")),
    ):
        result = await predict_cashflow(lancamentos_sample, "Empresa Teste")

    # Fallback must still return valid structure
    assert "cenarios" in result
    assert "base" in result["cenarios"]
    assert "tendencia_receita" in result


@pytest.mark.asyncio
async def test_predict_cashflow_empty_lancamentos():
    """Handles empty dataset gracefully."""
    from services.ai_engine.agent_predictor import predict_cashflow

    result = await predict_cashflow([], "Empresa Sem Dados")
    assert "cenarios" in result


def test_aggregate_by_month(lancamentos_sample):
    """_aggregate_by_month groups entries correctly."""
    from services.ai_engine.agent_predictor import _aggregate_by_month

    monthly = _aggregate_by_month(lancamentos_sample)
    assert "2026-01" in monthly
    assert monthly["2026-01"]["receita"] == 85000
    assert monthly["2026-01"]["despesa"] == 42000


def test_simple_trend():
    """_simple_trend detects growing, stable, or declining."""
    from services.ai_engine.agent_predictor import _simple_trend

    growing = [100, 110, 120, 130, 140, 150]
    declining = [150, 140, 130, 120, 110, 100]
    stable = [100, 101, 99, 100, 102, 100]

    assert _simple_trend(growing) == "crescimento"
    assert _simple_trend(declining) == "queda"
    assert _simple_trend(stable) == "estavel"
    assert _simple_trend([]) == "estavel"
