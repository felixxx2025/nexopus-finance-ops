"""
Agent Parser — extração de dados de documentos financeiros.

Fluxo: documento → OCR/regex/LLM → estrutura de dados normalizada
"""
from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY não definida")
        _client = OpenAI(api_key=api_key)
    return _client


def parse_document(file_path: str) -> dict[str, Any]:
    """
    Extrai dados estruturados de um documento financeiro (PDF, Excel ou SPED).

    Pipeline:
    1. Extrai texto bruto via pdf_parser / excel_parser
    2. Aplica regex para entidades comuns (CNPJ, datas, valores)
    3. Envia ao LLM para estruturação final

    Args:
        file_path: Caminho local (temporário) do arquivo.

    Returns:
        structured_data: dict com campos normalizados prontos para classificação.
    """
    # Passo 1 — extração de texto
    raw_text = _extract_text(file_path)

    # Passo 2 — estruturação via LLM
    structured_data = _llm_structure(raw_text)

    return structured_data


def _extract_text(file_path: str) -> str:
    """Despacha para o parser correto baseado na extensão."""
    ext = file_path.rsplit(".", 1)[-1].lower()
    if ext == "pdf":
        from services.parser.pdf_parser import extract_pdf  # type: ignore
        return extract_pdf(file_path)
    if ext in ("xlsx", "xls"):
        # TODO: implementar excel_parser
        raise NotImplementedError("Parser Excel ainda não implementado")
    if ext == "txt":  # SPED
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    raise ValueError(f"Tipo de arquivo não suportado: {ext}")


def _llm_structure(raw_text: str) -> dict[str, Any]:
    """Envia texto bruto ao LLM e retorna dados estruturados."""
    client = _get_client()
    prompt = (
        "Você é um contador especialista. "
        "Extraia do texto abaixo as seguintes informações em JSON: "
        "empresa (nome, cnpj), período (data_inicio, data_fim), "
        "lançamentos (lista de {conta, tipo, valor, descrição}). "
        "Retorne APENAS o JSON, sem explicações.\n\n"
        f"{raw_text[:8000]}"  # limita contexto
    )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
    )
    import json
    return json.loads(response.choices[0].message.content or "{}")
