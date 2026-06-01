"""
Agent Auditor — detecção de anomalias, fraudes e irregularidades contábeis.

Modelo: claude-sonnet-4.6 + RAG sobre legislação CPC/IFRS/RFB

Responsabilidade:
  Analisar lançamentos e relatórios para identificar:
  - Anomalias em valores (outliers estatísticos)
  - Inconsistências no plano de contas
  - Possíveis fraudes (despesas fora do padrão, lançamentos fictícios)
  - Desvios de compliance fiscal/contábil
  - Violações NBC TG / CPC / Lei 6.404/76
"""
from __future__ import annotations

import json
import logging
import math
import re
from decimal import Decimal
from typing import Any

from services.ai_engine.github_ai_client import COPILOT_CHAT_URL, MODELS, chat_completion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um auditor contábil sênior certificado (CRC) com especialização em auditoria forense
e compliance fiscal brasileiro (NBC TG, CPC, IFRS, Lei 6.404/76, IN RFB 1700/17).

Analise os lançamentos contábeis fornecidos e identifique:
1. Anomalias em valores (outliers, valores round numbers suspeitos, sequências artificiais)
2. Inconsistências no plano de contas (débitos/créditos invertidos, contas inexistentes)
3. Riscos de fraude (despesas pessoais, notas fiscais duplicadas, fornecedores suspeitos)
4. Desvios de compliance (SPED, ECD, ECF, LALUR, CSLL, IRPJ)
5. Violações de normas contábeis (NBC TG 26, NBC TG 1, CPC 04)

Retorne EXCLUSIVAMENTE um JSON válido:
{
  "score_risco": number (0-100, 0=sem risco, 100=risco máximo),
  "nivel_risco": "baixo | medio | alto | critico",
  "anomalias": [
    {
      "tipo": "string",
      "descricao": "string",
      "severidade": "baixa | media | alta | critica",
      "lancamento_ref": "string ou null",
      "valor_suspeito": number ou null,
      "norma_violada": "string ou null",
      "recomendacao": "string"
    }
  ],
  "compliance": {
    "equacao_patrimonial": true | false,
    "partida_dobrada": true | false,
    "plano_rfb_aderente": true | false,
    "observacoes": ["string"]
  },
  "resumo_executivo": "string (2-3 parágrafos)",
  "acoes_recomendadas": ["string"],
  "confianca": number
}
- Retorne SOMENTE o JSON, sem markdown, sem explicações.
"""

# Legislação de referência para RAG inline
_NORMAS_CONTEXT = """
NORMAS DE REFERÊNCIA:
- NBC TG 26 R5: Apresentação das Demonstrações Contábeis
- CPC 04 R1: Ativo Intangível
- Lei 6.404/76: Art. 176 - obrigatoriedade das demonstrações
- IN RFB 1700/17: Tributação IRPJ/CSLL
- Resolução CFC 1.374/11: Plano de Contas Referencial
- NBC TA 240: Responsabilidade do auditor relacionada a fraude
"""


def _detect_statistical_anomalies(lancamentos: list[dict[str, Any]]) -> list[dict]:
    """Detecta outliers estatísticos nos valores dos lançamentos."""
    anomalias = []
    values = []
    for l in lancamentos:
        try:
            v = abs(float(l.get("valor", 0)))
            if v > 0:
                values.append(v)
        except (TypeError, ValueError):
            continue

    if len(values) < 3:
        return []

    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    std = math.sqrt(variance) if variance > 0 else 0

    for l in lancamentos:
        try:
            v = abs(float(l.get("valor", 0)))
        except (TypeError, ValueError):
            continue

        if std > 0 and abs(v - mean) > 3 * std:
            anomalias.append({
                "tipo": "outlier_estatistico",
                "descricao": f"Valor R$ {v:,.2f} está a {abs(v - mean) / std:.1f} desvios padrão da média (R$ {mean:,.2f})",
                "severidade": "alta" if abs(v - mean) > 5 * std else "media",
                "lancamento_ref": l.get("descricao", "")[:100],
                "valor_suspeito": v,
                "norma_violada": "NBC TA 240",
                "recomendacao": "Verificar documentação de suporte do lançamento.",
            })

        # Round numbers suspeitos (valores redondos em grandes quantias)
        if v > 10000 and v == round(v, -3):
            anomalias.append({
                "tipo": "round_number",
                "descricao": f"Valor exatamente redondo de R$ {v:,.2f} — pode indicar estimativa ou lançamento fictício.",
                "severidade": "baixa",
                "lancamento_ref": l.get("descricao", "")[:100],
                "valor_suspeito": v,
                "norma_violada": None,
                "recomendacao": "Confirmar valor real com documentação fiscal.",
            })

    return anomalias[:10]  # limitar a 10 anomalias estatísticas


def _extract_json(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Agent Auditor: falha ao parsear JSON.")
        return {}


async def audit_entries(
    lancamentos: list[dict[str, Any]],
    dre: dict[str, Any] | None = None,
    balanco: dict[str, Any] | None = None,
    company_name: str = "",
) -> dict[str, Any]:
    """
    Executa auditoria completa sobre os lançamentos.

    Args:
        lancamentos: lançamentos classificados.
        dre: DRE calculado (opcional).
        balanco: Balanço Patrimonial (opcional).
        company_name: nome da empresa.

    Returns:
        Relatório de auditoria com score de risco e anomalias.
    """
    # Pré-análise estatística local
    stat_anomalias = _detect_statistical_anomalies(lancamentos)

    sample = lancamentos[:50]  # limitar contexto ao LLM

    payload = {
        "empresa": company_name,
        "total_lancamentos": len(lancamentos),
        "amostra_lancamentos": sample,
        "dre_resumo": dre,
        "balanco_resumo": balanco,
        "anomalias_pre_detectadas": stat_anomalias,
        "normas_contexto": _NORMAS_CONTEXT,
    }

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)},
    ]

    try:
        raw = await chat_completion(
            messages=messages,
            model=MODELS["classifier"],
            endpoint=COPILOT_CHAT_URL,
            temperature=0.1,
            max_tokens=3000,
        )
        result = _extract_json(raw)

        # Enriquecer com anomalias estatísticas se o LLM não as incluiu
        if stat_anomalias and "anomalias" in result:
            existing_types = {a.get("tipo") for a in result["anomalias"]}
            for a in stat_anomalias:
                if a["tipo"] not in existing_types:
                    result["anomalias"].append(a)

        result["lancamentos_auditados"] = len(lancamentos)
        return result

    except Exception as e:
        logger.error("Agent Auditor falhou: %s", e)
        return {
            "score_risco": 0,
            "nivel_risco": "baixo",
            "anomalias": stat_anomalias,
            "compliance": {
                "equacao_patrimonial": True,
                "partida_dobrada": True,
                "plano_rfb_aderente": True,
                "observacoes": ["Auditoria de IA indisponível — apenas análise estatística."],
            },
            "resumo_executivo": "Auditoria automática via IA indisponível. Análise estatística básica realizada.",
            "acoes_recomendadas": ["Revisar lançamentos manualmente.", "Verificar disponibilidade do serviço de IA."],
            "confianca": 0.3,
            "lancamentos_auditados": len(lancamentos),
            "fallback": True,
        }
