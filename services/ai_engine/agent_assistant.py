"""
Agent Assistant — Assistente financeiro conversacional com streaming SSE e RAG.

Modelo: gpt-5.2 (Copilot endpoint)
RAG: PostgreSQL + pgvector para busca semântica em conhecimento contábil

Responsabilidade:
  Responder perguntas em linguagem natural sobre os dados financeiros da empresa,
  como DRE, Balanço, fluxo de caixa, lançamentos, tendências e compliance.
  Suporta streaming via Server-Sent Events (SSE).
  Integra RAG para contexto enriquecido com normas e conceitos contábeis.
"""
from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_engine.github_ai_client import COPILOT_CHAT_URL, MODELS, _get_token
from services.knowledge.rag_service import search_knowledge

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """\
Você é o Assistente Financeiro do Nexopus Finance Ops — um sistema de IA para
contabilidade e finanças empresariais no Brasil.

Você tem acesso ao contexto financeiro da empresa fornecido pelo usuário e deve:
- Responder perguntas sobre DRE, Balanço Patrimonial, fluxo de caixa e lançamentos.
- Explicar conceitos contábeis de forma clara (NBC TG, CPC, Lei 6.404/76).
- Apontar riscos, oportunidades e tendências financeiras.
- Sugerir ações concretas para melhorar a saúde financeira.
- Citar normas brasileiras quando relevante (NBC TG, IFRS, RFB, SPED).

Regras:
- Responda sempre em português brasileiro formal mas acessível.
- Seja conciso mas completo. Use listas e formatação quando clareza exigir.
- Se não tiver dados suficientes, peça ao usuário que forneça.
- NUNCA invente dados financeiros — baseie-se APENAS no contexto fornecido.
- Não execute cálculos financeiros que não consegue verificar com os dados disponíveis.
"""

_TIMEOUT = 120.0


def _build_context_message(context: dict[str, Any], rag_results: list[dict[str, Any]] | None = None) -> str:
    """Formata o contexto financeiro como mensagem de sistema enriquecida com RAG."""
    parts = []
    if context.get("empresa"):
        parts.append(f"EMPRESA: {context['empresa']}")
    if context.get("periodo"):
        parts.append(f"PERÍODO: {context['periodo']}")
    if context.get("dre"):
        parts.append(f"DRE RESUMO:\n{json.dumps(context['dre'], ensure_ascii=False, indent=2, default=str)}")
    if context.get("balanco"):
        parts.append(f"BALANÇO RESUMO:\n{json.dumps(context['balanco'], ensure_ascii=False, indent=2, default=str)}")
    if context.get("forecast"):
        parts.append(f"PREVISÃO (90 dias):\n{json.dumps(context['forecast'], ensure_ascii=False, indent=2, default=str)}")
    if context.get("audit"):
        parts.append(f"AUDITORIA:\n{json.dumps(context['audit'], ensure_ascii=False, indent=2, default=str)}")
    if context.get("lancamentos_recentes"):
        parts.append(f"ÚLTIMOS LANÇAMENTOS:\n{json.dumps(context['lancamentos_recentes'][:10], ensure_ascii=False, default=str)}")

    # Adiciona contexto RAG se disponível
    if rag_results:
        rag_parts = ["CONHECIMENTO CONTÁBIL RELEVANTE (RAG):"]
        for i, result in enumerate(rag_results[:3], 1):  # Top 3 resultados
            rag_parts.append(f"\n--- Fonte {i} ({result.get('source', 'N/A')}) ---")
            rag_parts.append(f"Título: {result['title']}")
            rag_parts.append(f"Conteúdo: {result['content'][:500]}...")
            if result.get("tags"):
                rag_parts.append(f"Tags: {', '.join(result['tags'])}")
        parts.append("\n".join(rag_parts))

    return "\n\n".join(parts) if parts else "Nenhum contexto financeiro disponível."


async def stream_answer(
    question: str,
    context: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    Gera resposta em streaming (SSE) para a pergunta do usuário com RAG.

    Args:
        question: pergunta em linguagem natural.
        context: dados financeiros da empresa (DRE, Balanço, forecast, etc.).
        history: histórico de mensagens anteriores do chat.
        db: sessão do banco para busca RAG (opcional).

    Yields:
        Chunks de texto da resposta.
    """
    # Busca RAG se db fornecido
    rag_results = None
    if db:
        try:
            rag_results = await search_knowledge(db, question, limit=3)
            if rag_results:
                logger.info("RAG: %d resultados encontrados para query: %s", len(rag_results), question[:50])
        except Exception as e:
            logger.warning("RAG falhou, continuando sem contexto enriquecido: %s", e)

    context_msg = _build_context_message(context, rag_results)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "system", "content": f"CONTEXTO FINANCEIRO ATUAL:\n{context_msg}"},
    ]

    if history:
        messages.extend(history[-10:])  # últimas 10 mensagens do histórico

    messages.append({"role": "user", "content": question})

    token = _get_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Copilot-Integration-Id": "nexopus-finance-ops",
        "editor-version": "vscode/1.95.0",
    }

    payload = {
        "model": MODELS["generator"],  # gpt-5.2
        "messages": messages,
        "temperature": 0.4,
        "max_tokens": 1500,
        "stream": True,
    }

    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            async with client.stream(
                "POST",
                COPILOT_CHAT_URL,
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data: "):
                        continue
                    data = line[6:]
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        delta = chunk["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
    except Exception as e:
        logger.error("Agent Assistant streaming falhou: %s", e)
        yield f"\n\n[Erro ao conectar com o assistente: {e}]"


async def answer(
    question: str,
    context: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
    db: Optional[AsyncSession] = None,
) -> str:
    """
    Versão não-streaming do assistente (coleta toda a resposta).
    Útil para integrações que não suportam SSE.
    """
    chunks = []
    async for chunk in stream_answer(question, context, history, db):
        chunks.append(chunk)
    return "".join(chunks)
