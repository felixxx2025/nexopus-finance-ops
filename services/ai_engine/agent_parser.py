"""
Agent Parser — extração estruturada de dados de documentos financeiros.

Modelo: Meta-Llama-3.1-405B-Instruct (Azure Inference — HTTP 200 confirmado)
Endpoint: https://models.inference.ai.azure.com/chat/completions

Responsabilidade:
  Receber texto bruto de um PDF financeiro (extrato bancário, nota fiscal,
  SPED, DRE, balanço, etc.) e retornar um dicionário estruturado com:
    - empresa (nome, cnpj)
    - periodo (data_inicio, data_fim)
    - lancamentos (lista com conta, descricao, valor, tipo, data)
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any

from services.ai_engine.github_ai_client import (
    AZURE_CHAT_URL,
    MODELS,
    chat_completion,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é um especialista em contabilidade brasileira e análise de documentos financeiros.
Sua tarefa é extrair dados estruturados de documentos financeiros em texto puro.

Retorne EXCLUSIVAMENTE um objeto JSON válido no seguinte schema — sem explicações, sem markdown:

{
  "empresa": {
    "nome": "string",
    "cnpj": "string (somente dígitos, 14 chars ou vazio)"
  },
  "periodo": {
    "data_inicio": "YYYY-MM-DD ou null",
    "data_fim": "YYYY-MM-DD ou null"
  },
  "lancamentos": [
    {
      "data": "YYYY-MM-DD ou null",
      "descricao": "string",
      "valor": number,
      "tipo": "receita | despesa | neutro",
      "conta_sugerida": "string (ex: Receita de Serviços, Fornecedores, etc.)"
    }
  ],
  "moeda": "BRL",
  "confianca": number
}

Regras:
- "valor" sempre positivo (o campo "tipo" indica a natureza).
- "confianca" entre 0.0 e 1.0 indicando sua certeza na extração.
- Se não encontrar dado, use null ou string vazia — nunca invente valores.
- Datas sempre ISO 8601 (YYYY-MM-DD).
"""

_MAX_TEXT_CHARS = 12_000


def _truncate(text: str) -> str:
    if len(text) <= _MAX_TEXT_CHARS:
        return text
    logger.warning(
        "Texto truncado de %d para %d chars para caber no contexto do modelo",
        len(text), _MAX_TEXT_CHARS,
    )
    return text[:_MAX_TEXT_CHARS] + "\n[... TEXTO TRUNCADO ...]"


def _extract_json(raw: str) -> dict[str, Any]:
    """
    Extrai JSON da resposta do modelo, tolerando markdown code fences.

    Raises:
        ValueError: Se nenhum JSON válido for encontrado.
    """
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise ValueError(
            f"JSON inválido na resposta do modelo (primeiros 300 chars): {raw[:300]}"
        )


def _validate_structure(data: dict[str, Any]) -> dict[str, Any]:
    """Valida e normaliza a estrutura de saída garantindo tipos corretos."""
    if not isinstance(data.get("empresa"), dict):
        data["empresa"] = {"nome": "", "cnpj": ""}
    if not isinstance(data.get("periodo"), dict):
        data["periodo"] = {"data_inicio": None, "data_fim": None}
    if not isinstance(data.get("lancamentos"), list):
        data["lancamentos"] = []

    normalized = []
    for item in data["lancamentos"]:
        if not isinstance(item, dict):
            continue
        try:
            valor = float(item.get("valor", 0))
        except (TypeError, ValueError):
            valor = 0.0
        tipo = item.get("tipo", "neutro")
        if tipo not in ("receita", "despesa", "neutro"):
            tipo = "neutro"
        normalized.append({
            "data": item.get("data"),
            "descricao": str(item.get("descricao", "")),
            "valor": abs(valor),
            "tipo": tipo,
            "conta_sugerida": str(item.get("conta_sugerida", "")),
        })

    data["lancamentos"] = normalized
    data.setdefault("moeda", "BRL")
    data.setdefault("confianca", 0.0)
    return data


def _extract_text(file_path: str) -> str:
    """Despacha para o parser correto baseado na extensão."""
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        from services.parser.pdf_parser import extract_pdf  # type: ignore
        return extract_pdf(file_path)
    if ext in ("xlsx", "xls"):
        raise NotImplementedError("Parser Excel ainda não implementado")
    if ext == "txt":
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()
    raise ValueError(f"Tipo de arquivo não suportado: {ext}")


def parse_document(file_path: str) -> dict[str, Any]:
    """
    Extrai texto do documento e usa o LLaMA 405B para estruturar os dados.

    Args:
        file_path: Caminho local do arquivo PDF/txt/xlsx.

    Returns:
        Dicionário estruturado com empresa, periodo e lancamentos.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o documento não contiver texto extraível ou JSON inválido.
        RuntimeError: Se a API GitHub AI falhar após retries.
    """
    raw_text = _extract_text(file_path)
    logger.info("parse_document | arquivo=%s | chars=%d", file_path, len(raw_text))

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Extraia os dados estruturados do seguinte documento financeiro:\n\n"
                + _truncate(raw_text)
            ),
        },
    ]

    raw_response = chat_completion(
        messages,
        model=MODELS["parser"],
        max_tokens=2048,
        temperature=0.0,
        endpoint=AZURE_CHAT_URL,
        response_format={"type": "json_object"},
    )

    structured = _extract_json(raw_response)
    validated = _validate_structure(structured)

    logger.info(
        "parse_document concluído | lancamentos=%d | confianca=%.2f",
        len(validated["lancamentos"]),
        validated.get("confianca", 0),
    )
    return validated
