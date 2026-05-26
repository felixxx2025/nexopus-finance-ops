"""
Agent Reconciler — conciliação bancária automática.

Modelo: Meta-Llama-3.1-405B-Instruct (Azure Inference)

Responsabilidade:
  Fazer o match automático entre:
  - Extrato bancário (OFX/CSV) importado
  - Lançamentos contábeis registrados no sistema

  Identifica: lançamentos casados, divergentes, duplicados e pendentes.
"""
from __future__ import annotations

import json
import logging
import re
from decimal import Decimal
from typing import Any

from services.ai_engine.github_ai_client import AZURE_CHAT_URL, MODELS, chat_completion

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um especialista em conciliação bancária contábil no Brasil.

Receberá dois conjuntos de dados:
1. "extrato_bancario": transações do extrato bancário (OFX/CSV)
2. "lancamentos_contabeis": lançamentos já registrados no sistema contábil

Sua tarefa é fazer o match (conciliação) entre os dois conjuntos:
- CONCILIADO: transação do banco tem correspondência exata ou próxima no contábil
- DIVERGENTE: existe correspondência mas com diferença de valor ou data > 3 dias
- APENAS_BANCO: transação no banco sem lançamento contábil correspondente
- APENAS_CONTABIL: lançamento contábil sem correspondência no extrato

Critérios de match:
- Valor exatamente igual + descrição similar + data próxima (±3 dias) → CONCILIADO
- Valor diferente mas descrição/data compatíveis → DIVERGENTE
- Sem correspondência → APENAS_BANCO ou APENAS_CONTABIL

Retorne EXCLUSIVAMENTE um JSON válido:
{
  "resumo": {
    "total_banco": number,
    "total_contabil": number,
    "conciliados": number,
    "divergentes": number,
    "apenas_banco": number,
    "apenas_contabil": number,
    "taxa_conciliacao": number
  },
  "matches": [
    {
      "status": "CONCILIADO | DIVERGENTE | APENAS_BANCO | APENAS_CONTABIL",
      "banco": {...} ou null,
      "contabil": {...} ou null,
      "diferenca_valor": number ou null,
      "diferenca_dias": number ou null,
      "observacao": "string"
    }
  ],
  "alertas": ["string"],
  "acoes_recomendadas": ["string"]
}
- Retorne SOMENTE o JSON, sem markdown.
"""

_BATCH_SIZE = 30


def _normalize_description(desc: str) -> str:
    """Normaliza descrição para comparação fuzzy."""
    if not desc:
        return ""
    return re.sub(r"[^a-zA-Z0-9\u00C0-\u024F\s]", "", desc.lower()).strip()


def _simple_match(
    bank_entries: list[dict[str, Any]],
    accounting_entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Match simples por valor exato + data próxima como fallback."""
    matches = []
    used_accounting = set()

    for b in bank_entries:
        try:
            b_valor = abs(float(b.get("valor", 0)))
            b_data = b.get("data", "")
        except (TypeError, ValueError):
            b_valor = 0
            b_data = ""

        best_match = None
        for i, a in enumerate(accounting_entries):
            if i in used_accounting:
                continue
            try:
                a_valor = abs(float(a.get("valor", 0)))
                a_data = a.get("data", "")
            except (TypeError, ValueError):
                continue

            if abs(b_valor - a_valor) < 0.01:
                # Calcular diferença de datas
                diff_days = 0
                if b_data and a_data and len(b_data) >= 10 and len(a_data) >= 10:
                    from datetime import date
                    try:
                        bd = date.fromisoformat(b_data[:10])
                        ad = date.fromisoformat(a_data[:10])
                        diff_days = abs((bd - ad).days)
                    except ValueError:
                        diff_days = 999

                if diff_days <= 3:
                    best_match = (i, a, diff_days)
                    break

        if best_match:
            idx, a_entry, diff_days = best_match
            used_accounting.add(idx)
            matches.append({
                "status": "CONCILIADO",
                "banco": b,
                "contabil": a_entry,
                "diferenca_valor": 0.0,
                "diferenca_dias": diff_days,
                "observacao": "Match automático por valor e data.",
            })
        else:
            matches.append({
                "status": "APENAS_BANCO",
                "banco": b,
                "contabil": None,
                "diferenca_valor": None,
                "diferenca_dias": None,
                "observacao": "Sem lançamento contábil correspondente.",
            })

    # Adicionar contábeis sem correspondência
    for i, a in enumerate(accounting_entries):
        if i not in used_accounting:
            matches.append({
                "status": "APENAS_CONTABIL",
                "banco": None,
                "contabil": a,
                "diferenca_valor": None,
                "diferenca_dias": None,
                "observacao": "Lançamento sem correspondência no extrato bancário.",
            })

    return matches


def _build_summary(matches: list[dict[str, Any]], bank_total: int, contabil_total: int) -> dict:
    counts = {"CONCILIADO": 0, "DIVERGENTE": 0, "APENAS_BANCO": 0, "APENAS_CONTABIL": 0}
    for m in matches:
        s = m.get("status", "")
        if s in counts:
            counts[s] += 1
    total = bank_total + contabil_total
    conciliados = counts["CONCILIADO"]
    return {
        "total_banco": bank_total,
        "total_contabil": contabil_total,
        "conciliados": conciliados,
        "divergentes": counts["DIVERGENTE"],
        "apenas_banco": counts["APENAS_BANCO"],
        "apenas_contabil": counts["APENAS_CONTABIL"],
        "taxa_conciliacao": round(conciliados / max(max(bank_total, contabil_total), 1) * 100, 2),
    }


def _extract_json(raw: str) -> dict[str, Any]:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Agent Reconciler: falha ao parsear JSON.")
        return {}


def reconcile(
    bank_entries: list[dict[str, Any]],
    accounting_entries: list[dict[str, Any]],
    company_name: str = "",
) -> dict[str, Any]:
    """
    Executa conciliação bancária entre extrato e lançamentos contábeis.

    Args:
        bank_entries: transações do extrato bancário.
        accounting_entries: lançamentos contábeis do período.
        company_name: nome da empresa.

    Returns:
        Resultado da conciliação com matches, divergências e recomendações.
    """
    # Usar amostras para enviar ao LLM (evitar limite de contexto)
    bank_sample = bank_entries[:_BATCH_SIZE]
    contabil_sample = accounting_entries[:_BATCH_SIZE]

    payload = {
        "empresa": company_name,
        "extrato_bancario": bank_sample,
        "lancamentos_contabeis": contabil_sample,
    }

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False, default=str)},
    ]

    try:
        raw = chat_completion(
            url=AZURE_CHAT_URL,
            model=MODELS["parser"],  # LLaMA 3.1 405B
            messages=messages,
            temperature=0.1,
            max_tokens=4000,
        )
        result = _extract_json(raw)
        if result:
            result["total_processado_banco"] = len(bank_entries)
            result["total_processado_contabil"] = len(accounting_entries)
            return result
        raise ValueError("JSON vazio retornado pelo LLM.")

    except Exception as e:
        logger.error("Agent Reconciler LLM falhou (%s) — usando fallback local.", e)
        # Fallback: algoritmo local
        matches = _simple_match(bank_entries, accounting_entries)
        summary = _build_summary(matches, len(bank_entries), len(accounting_entries))
        pendentes_banco = [m for m in matches if m["status"] == "APENAS_BANCO"]
        alertas = []
        if pendentes_banco:
            alertas.append(
                f"{len(pendentes_banco)} transações bancárias sem lançamento contábil correspondente."
            )
        return {
            "resumo": summary,
            "matches": matches,
            "alertas": alertas,
            "acoes_recomendadas": [
                "Registrar lançamentos contábeis para transações apenas no banco.",
                "Verificar manualmente lançamentos divergentes.",
            ],
            "total_processado_banco": len(bank_entries),
            "total_processado_contabil": len(accounting_entries),
            "fallback": True,
        }
