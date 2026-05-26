"""
Agent Classifier — classifica contas contábeis via IA.

Modelo: claude-sonnet-4.6 (Copilot endpoint — HTTP 200 confirmado)
Endpoint: https://api.githubcopilot.com/chat/completions

Responsabilidade:
  Receber dados estruturados (saída do agent_parser) e classificar cada
  lançamento conforme o Plano de Contas Referencial da RFB, adicionando
  os campos tipo_conta, codigo_conta e grupo_dre.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from services.ai_engine.github_ai_client import (
    COPILOT_CHAT_URL,
    MODELS,
    chat_completion,
)

logger = logging.getLogger(__name__)

ACCOUNT_TYPES = ("ativo", "passivo", "receita", "despesa", "pl")

_SYSTEM_PROMPT = """\
Você é um especialista no Plano de Contas Referencial da Receita Federal do Brasil (RFB)
e nas normas NBC TG 26 (Apresentação das Demonstrações Contábeis).

Sua tarefa é classificar lançamentos contábeis.

Retorne EXCLUSIVAMENTE um objeto JSON válido com a estrutura:
{
  "lancamentos": [
    {
      ...campos originais mantidos...,
      "tipo_conta": "ativo | passivo | receita | despesa | pl",
      "codigo_conta": "string (ex: 3.1.1.01.01)",
      "grupo_dre": "receita_bruta | deducoes | receita_liquida | cmv | lucro_bruto | despesa_operacional | ebitda | depreciacao | ebit | resultado_financeiro | lair | impostos | lucro_liquido | nao_aplicavel",
      "natureza": "devedora | credora"
    }
  ]
}

Regras:
- Mantenha TODOS os campos originais de cada lançamento.
- Classifique baseado na descricao e conta_sugerida do lançamento.
- Contas de Ativo e Despesa têm natureza devedora; Passivo, Receita e PL, credora.
- Se não tiver certeza, use o tipo mais provavel com base no contexto.
- Retorne SOMENTE o JSON, sem markdown, sem explicações.
"""

_BATCH_SIZE = 20  # max lançamentos por chamada ao LLM


def _extract_json_list(raw: str, original: list) -> list[dict[str, Any]]:
    """Extrai lista de lançamentos da resposta JSON do modelo."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data.get("lancamentos", original)
        if isinstance(data, list):
            return data
    except json.JSONDecodeError:
        pass
    logger.warning("Falha ao parsear JSON do classifier — retornando originais")
    return original


def _classify_batch(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Envia um batch de lançamentos ao Claude Sonnet 4.6 para classificação."""
    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Classifique os seguintes lançamentos contábeis:\n\n"
                + json.dumps({"lancamentos": entries}, ensure_ascii=False)
            ),
        },
    ]

    raw = chat_completion(
        messages,
        model=MODELS["classifier"],
        max_tokens=4096,
        temperature=0.0,
        endpoint=COPILOT_CHAT_URL,
        response_format={"type": "json_object"},
    )

    return _extract_json_list(raw, entries)


def classify_accounts(data: dict[str, Any]) -> dict[str, Any]:
    """
    Classifica contas de todos os lançamentos usando Claude Sonnet 4.6.

    Args:
        data: Saída normalizada do agent_parser.

    Returns:
        Mesmo dict com campo tipo_conta, codigo_conta, grupo_dre e natureza
        preenchidos em cada lançamento.

    Raises:
        RuntimeError: Se a API GitHub AI falhar após retries.
    """
    entries = data.get("lancamentos", [])
    if not entries:
        logger.warning("classify_accounts: nenhum lançamento para classificar")
        return data

    classified: list[dict[str, Any]] = []

    # Processa em batches para não exceder limite de contexto
    for i in range(0, len(entries), _BATCH_SIZE):
        batch = entries[i : i + _BATCH_SIZE]
        logger.info(
            "Classificando batch %d–%d de %d lançamentos",
            i + 1, min(i + _BATCH_SIZE, len(entries)), len(entries),
        )
        classified.extend(_classify_batch(batch))

    logger.info("classify_accounts concluído | %d lançamentos classificados", len(classified))
    return {**data, "lancamentos": classified}
