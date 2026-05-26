"""
Agent Predictor — previsão de fluxo de caixa e DRE (séries temporais).

Modelos:
  - text-embedding-3-large (embeddings históricos)
  - claude-sonnet-4.6 (raciocínio e narrativa preditiva)

Responsabilidade:
  Receber histórico de lançamentos e retornar projeção de 30/60/90 dias
  com cenários otimista, base e pessimista.
"""
from __future__ import annotations

import json
import logging
import math
import re
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

from services.ai_engine.github_ai_client import COPILOT_CHAT_URL, MODELS, chat_completion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um analista financeiro sênior especializado em previsão de fluxo de caixa para empresas brasileiras.

Receberá um histórico de lançamentos contábeis agregados por mês e deverá:
1. Identificar tendências de crescimento/queda em receitas e despesas.
2. Projetar os próximos 3 meses (30, 60, 90 dias) com 3 cenários:
   - otimista: crescimento de 10-20% acima da tendência
   - base: continuação da tendência atual
   - pessimista: queda de 10-20% abaixo da tendência

Retorne EXCLUSIVAMENTE um JSON válido:
{
  "tendencia": {
    "receita": "crescimento | estavel | queda",
    "despesa": "crescimento | estavel | queda",
    "margem_liquida_media": number
  },
  "projecao": {
    "30_dias": {
      "otimista": {"receita": number, "despesa": number, "resultado": number},
      "base":     {"receita": number, "despesa": number, "resultado": number},
      "pessimista":{"receita": number, "despesa": number, "resultado": number}
    },
    "60_dias": { ... },
    "90_dias": { ... }
  },
  "alertas": ["string"],
  "recomendacoes": ["string"],
  "confianca": number,
  "narrativa": "string (2-4 parágrafos)"
}
- Valores monetários em BRL (float, sem símbolo).
- Retorne SOMENTE o JSON, sem markdown, sem explicações.
"""


def _aggregate_by_month(lancamentos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Agrega lançamentos por mês calculando receita e despesa total."""
    monthly: dict[str, dict[str, Decimal]] = {}
    for l in lancamentos:
        data_str = l.get("data", "") or ""
        if not data_str or len(data_str) < 7:
            continue
        mes = data_str[:7]  # YYYY-MM
        if mes not in monthly:
            monthly[mes] = {"receita": Decimal(0), "despesa": Decimal(0)}
        tipo = l.get("tipo_conta", l.get("tipo", "")).lower()
        valor = abs(Decimal(str(l.get("valor", 0))))
        if tipo == "receita":
            monthly[mes]["receita"] += valor
        elif tipo == "despesa":
            monthly[mes]["despesa"] += valor

    return [
        {
            "mes": k,
            "receita": float(v["receita"]),
            "despesa": float(v["despesa"]),
            "resultado": float(v["receita"] - v["despesa"]),
        }
        for k, v in sorted(monthly.items())
    ]


def _simple_trend(values: list[float]) -> str:
    """Detecção simples de tendência via média das variações."""
    if len(values) < 2:
        return "estavel"
    deltas = [(values[i] - values[i - 1]) / max(abs(values[i - 1]), 1) for i in range(1, len(values))]
    avg = sum(deltas) / len(deltas)
    if avg > 0.03:
        return "crescimento"
    if avg < -0.03:
        return "queda"
    return "estavel"


def _extract_json(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Agent Predictor: falha ao parsear JSON — retornando fallback.")
        return {}


def predict_cashflow(
    lancamentos: list[dict[str, Any]],
    company_name: str = "",
) -> dict[str, Any]:
    """
    Gera previsão de fluxo de caixa para 30/60/90 dias.

    Args:
        lancamentos: lista de lançamentos classificados.
        company_name: nome da empresa (para contexto).

    Returns:
        Dicionário com tendência, projeção por cenário, alertas e narrativa.
    """
    monthly = _aggregate_by_month(lancamentos)

    if not monthly:
        return {
            "error": "Dados insuficientes para gerar previsão.",
            "monthly_data": [],
        }

    user_content = json.dumps(
        {
            "empresa": company_name,
            "historico_mensal": monthly,
            "total_lancamentos": len(lancamentos),
        },
        ensure_ascii=False,
    )

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = chat_completion(
            url=COPILOT_CHAT_URL,
            model=MODELS["classifier"],  # claude-sonnet-4.6
            messages=messages,
            temperature=0.2,
            max_tokens=2000,
        )
        result = _extract_json(raw)
        result["monthly_data"] = monthly
        result["lancamentos_processados"] = len(lancamentos)
        return result
    except Exception as e:
        logger.error("Agent Predictor falhou: %s", e)
        # Fallback estatístico simples
        receitas = [m["receita"] for m in monthly]
        despesas = [m["despesa"] for m in monthly]
        avg_rec = sum(receitas) / len(receitas) if receitas else 0
        avg_desp = sum(despesas) / len(despesas) if despesas else 0
        return {
            "tendencia": {
                "receita": _simple_trend(receitas),
                "despesa": _simple_trend(despesas),
                "margem_liquida_media": round((avg_rec - avg_desp) / max(avg_rec, 1) * 100, 2),
            },
            "projecao": {
                "30_dias": {
                    "otimista": {"receita": avg_rec * 1.1, "despesa": avg_desp * 0.95, "resultado": avg_rec * 1.1 - avg_desp * 0.95},
                    "base": {"receita": avg_rec, "despesa": avg_desp, "resultado": avg_rec - avg_desp},
                    "pessimista": {"receita": avg_rec * 0.9, "despesa": avg_desp * 1.05, "resultado": avg_rec * 0.9 - avg_desp * 1.05},
                },
                "60_dias": {
                    "otimista": {"receita": avg_rec * 1.15, "despesa": avg_desp * 0.93, "resultado": avg_rec * 1.15 - avg_desp * 0.93},
                    "base": {"receita": avg_rec, "despesa": avg_desp, "resultado": avg_rec - avg_desp},
                    "pessimista": {"receita": avg_rec * 0.85, "despesa": avg_desp * 1.08, "resultado": avg_rec * 0.85 - avg_desp * 1.08},
                },
                "90_dias": {
                    "otimista": {"receita": avg_rec * 1.20, "despesa": avg_desp * 0.90, "resultado": avg_rec * 1.20 - avg_desp * 0.90},
                    "base": {"receita": avg_rec, "despesa": avg_desp, "resultado": avg_rec - avg_desp},
                    "pessimista": {"receita": avg_rec * 0.80, "despesa": avg_desp * 1.10, "resultado": avg_rec * 0.80 - avg_desp * 1.10},
                },
            },
            "alertas": ["Previsão estatística — IA indisponível."],
            "recomendacoes": [],
            "confianca": 0.5,
            "narrativa": "Previsão gerada com base estatística simples (fallback).",
            "monthly_data": monthly,
            "lancamentos_processados": len(lancamentos),
            "fallback": True,
        }
