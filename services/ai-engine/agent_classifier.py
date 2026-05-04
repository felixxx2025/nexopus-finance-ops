"""
Agent Classifier — classifica automaticamente contas contábeis via IA.

Recebe dados estruturados (saída do agent_parser) e determina
o tipo de conta (ativo, passivo, receita, despesa, pl) conforme
o Plano de Contas da empresa ou sugestão do LLM.
"""
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

_client: OpenAI | None = None

ACCOUNT_TYPES = ("ativo", "passivo", "receita", "despesa", "pl")


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY não definida")
        _client = OpenAI(api_key=api_key)
    return _client


def classify_accounts(data: dict[str, Any]) -> dict[str, Any]:
    """
    Classifica as contas presentes em `data` nos tipos contábeis padrão.

    Args:
        data: Saída normalizada do agent_parser (campo "lançamentos").

    Returns:
        classified_data: Mesmo dict com campo "tipo_conta" preenchido
                         em cada lançamento.
    """
    entries = data.get("lançamentos", [])
    if not entries:
        return data

    classified = _llm_classify(entries)
    return {**data, "lançamentos": classified}


def _llm_classify(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Envia lançamentos ao LLM e recebe classificação de tipo de conta."""
    client = _get_client()
    prompt = (
        "Você é um contador especialista no Plano de Contas Referencial da RFB. "
        f"Classifique cada conta abaixo em um dos tipos: {', '.join(ACCOUNT_TYPES)}. "
        "Retorne uma lista JSON com os mesmos campos originais mais 'tipo_conta'.\n\n"
        f"{json.dumps(entries, ensure_ascii=False)[:6000]}"
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content or "{}")
    return result.get("lançamentos", entries)
