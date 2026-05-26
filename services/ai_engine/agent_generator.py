"""
Agent Generator — gera lançamentos contábeis e narrativa em linguagem natural.

Modelo: gpt-5.2 (Copilot endpoint — HTTP 200 confirmado)
Endpoint: https://api.githubcopilot.com/chat/completions

Responsabilidade:
  1. Converter lançamentos classificados em pares de débito/crédito (Partida Dobrada).
  2. Gerar narrativa do relatório em português via LLM.

Princípio da Partida Dobrada: todo débito tem um crédito correspondente de igual valor.
"""
from __future__ import annotations

import json
import logging
import re
import uuid
from decimal import Decimal, InvalidOperation
from typing import Any

from services.ai_engine.github_ai_client import (
    COPILOT_CHAT_URL,
    MODELS,
    chat_completion,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um contador sênior especialista em normas brasileiras (NBC TG, Lei 6.404/76, RFB).
Sua tarefa é gerar uma narrativa executiva clara sobre os dados financeiros fornecidos.

A narrativa deve:
- Estar em português brasileiro formal, mas acessível.
- Incluir: receita total, despesas totais, resultado (lucro/prejuízo), principais riscos observados.
- Mencionar alertas de compliance se desequilíbrios forem detectados.
- Ter entre 3 e 6 parágrafos.
- NÃÃO incluir markdown, apenas texto puro.
"""


# ── Determinação Débito/Crédito ────────────────────────────────────────────────

_DEVEDORAS = {"ativo", "despesa"}
_CREDORAS = {"passivo", "receita", "pl"}

_CONTRAPARTIDA: dict[str, str] = {
    "receita": "Caixa / Bancos",
    "despesa": "Caixa / Bancos",
    "ativo": "Capital Social",
    "passivo": "Ativo Circulante",
    "pl": "Resultado do Exercício",
}


def _determine_dc(tipo_conta: str) -> tuple[str, str]:
    """
    Retorna (lado_principal, contrapartida) conforme natureza da conta.
    Contas devedoras (ativo, despesa): débito na conta principal.
    Contas credoras (passivo, receita, pl): crédito na conta principal.
    """
    tc = tipo_conta.lower()
    if tc in _DEVEDORAS:
        return ("debit", "credit")
    return ("credit", "debit")


def _contrapartida(tipo_conta: str) -> str:
    return _CONTRAPARTIDA.get(tipo_conta.lower(), "Conta de Contrapartida")


# ── Construção de journal entries ────────────────────────────────────────────

def _build_entry(item: dict[str, Any], period_start: str | None) -> dict[str, Any]:
    """Constrói um journal_entry com dois journal_items (débito e crédito)."""
    try:
        valor = abs(Decimal(str(item.get("valor", 0))))
    except InvalidOperation:
        valor = Decimal("0")

    tipo_conta = str(item.get("tipo_conta", "despesa")).lower()
    conta = str(item.get("conta_sugerida") or item.get("conta") or "Conta desconhecida")
    descricao = str(item.get("descricao") or item.get("descrição") or "")
    data = item.get("data") or period_start or ""

    lado_principal, lado_contra = _determine_dc(tipo_conta)
    entry_id = str(uuid.uuid4())

    return {
        "journal_entry": {
            "id": entry_id,
            "date": data,
            "description": descricao,
            "tipo_conta": tipo_conta,
            "codigo_conta": item.get("codigo_conta", ""),
            "grupo_dre": item.get("grupo_dre", "nao_aplicavel"),
        },
        "items": [
            {
                "id": str(uuid.uuid4()),
                "entry_id": entry_id,
                "account": conta,
                "account_id": str(uuid.uuid4()),
                "type": lado_principal,
                "amount": float(valor),
            },
            {
                "id": str(uuid.uuid4()),
                "entry_id": entry_id,
                "account": _contrapartida(tipo_conta),
                "account_id": str(uuid.uuid4()),
                "type": lado_contra,
                "amount": float(valor),
            },
        ],
    }


# ── Narrativa via LLM ────────────────────────────────────────────────────────

def _build_summary(data: dict[str, Any], entries: list[dict[str, Any]]) -> dict[str, Any]:
    """Calcula KPIs agregados para envio ao LLM."""
    lancamentos = data.get("lancamentos", [])
    receita = sum(
        float(l.get("valor", 0)) for l in lancamentos
        if l.get("tipo") == "receita" or l.get("tipo_conta") == "receita"
    )
    despesa = sum(
        float(l.get("valor", 0)) for l in lancamentos
        if l.get("tipo") == "despesa" or l.get("tipo_conta") == "despesa"
    )
    return {
        "empresa": data.get("empresa", {}),
        "periodo": data.get("periodo", {}),
        "kpis": {
            "receita_total": receita,
            "despesa_total": despesa,
            "resultado": receita - despesa,
            "total_lancamentos": len(lancamentos),
        },
        "grupos_dre": {
            l.get("grupo_dre", "nao_aplicavel"): l.get("valor", 0)
            for l in lancamentos
            if l.get("grupo_dre")
        },
    }


def _generate_narrative(summary: dict[str, Any]) -> str:
    """Invoca GPT-5.2 para gerar narrativa executiva em português."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Gere a narrativa executiva para os seguintes dados financeiros:\n\n"
                + json.dumps(summary, ensure_ascii=False, indent=2)
            ),
        },
    ]
    try:
        return chat_completion(
            messages,
            model=MODELS["generator"],
            max_tokens=1024,
            temperature=0.3,
            endpoint=COPILOT_CHAT_URL,
        )
    except Exception as exc:
        logger.warning("Falha ao gerar narrativa via LLM: %s", exc)
        kpis = summary.get("kpis", {})
        resultado = kpis.get("resultado", 0)
        sinal = "lucro" if resultado >= 0 else "prejuízo"
        return (
            f"Período analisado: {summary.get('periodo', {})}. "
            f"Receita total: R$ {kpis.get('receita_total', 0):,.2f}. "
            f"Despesas totais: R$ {kpis.get('despesa_total', 0):,.2f}. "
            f"Resultado: {sinal} de R$ {abs(resultado):,.2f}."
        )


# ── Função pública ────────────────────────────────────────────────────────────

def generate_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Converte lançamentos classificados em pares de débito/crédito (Partida Dobrada)
    e gera narrativa executiva via GPT-5.2.

    Args:
        data: Saída do agent_classifier com campo "lancamentos" classificados.

    Returns:
        Lista de dicts compatíveis com journal_entries + journal_items + narrativa.
        O último elemento (se houver lançamentos) contém a chave "narrativa".

    Raises:
        RuntimeError: Se a API GitHub AI falhar após retries (só para narrativa;
                      lançamentos são gerados deterministicamente).
    """
    lancamentos = data.get("lancamentos", [])
    period_start = data.get("periodo", {}).get("data_inicio")

    if not lancamentos:
        logger.warning("generate_entries: nenhum lançamento para processar")
        return []

    # 1. Gera journal entries deterministicamente (sem LLM)
    journal_entries: list[dict[str, Any]] = [
        _build_entry(item, period_start) for item in lancamentos
    ]

    # 2. Gera narrativa via GPT-5.2
    summary = _build_summary(data, journal_entries)
    narrativa = _generate_narrative(summary)

    # Anexa narrativa e KPIs ao primeiro entry para disponibilizar no pipeline
    if journal_entries:
        journal_entries[0]["narrativa"] = narrativa
        journal_entries[0]["kpis"] = summary.get("kpis", {})

    logger.info(
        "generate_entries concluído | %d lançamentos | narrativa=%d chars",
        len(journal_entries), len(narrativa),
    )

    return journal_entries
