"""
Agent Assistant Local — Chat generativo 100% local usando RAG + Templates.

Usa RAG para buscar conhecimento relevante e templates para gerar respostas
sem dependência de APIs externas ou modelos LLM pesados.
"""
from __future__ import annotations

import logging
from typing import Any, AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from services.knowledge.rag_service import search_knowledge

logger = logging.getLogger(__name__)


async def stream_answer_local(
    question: str,
    context: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    Gera resposta usando RAG + templates locais.
    
    Args:
        question: Pergunta do usuário.
        context: Dados financeiros da empresa.
        history: Histórico de mensagens anteriores.
        db: Sessão do banco para busca RAG.
    
    Yields:
        Chunks de texto da resposta.
    """
    try:
        # Buscar contexto RAG se db fornecido
        rag_results = None
        if db:
            rag_results = await search_knowledge(db, question, limit=3, min_similarity=0.3, enable_web_search=True)
        
        # Gerar resposta baseada em RAG
        response = _generate_response(question, context, rag_results, history)
        
        # Yield em chunks
        chunk_size = 50
        for i in range(0, len(response), chunk_size):
            yield response[i:i + chunk_size]
        
    except Exception as e:
        logger.error("Agent Assistant local falhou: %s", e)
        yield f"\n\n[Erro ao gerar resposta: {e}]"


def _generate_response(
    question: str,
    context: dict[str, Any],
    rag_results: list[dict[str, Any]] | None = None,
    history: Optional[list[dict[str, str]]] = None,
) -> str:
    """Gera resposta baseada em RAG e templates."""
    
    response_parts = []
    
    # Saudação
    response_parts.append("Com base na análise do conhecimento disponível:\n\n")
    
    # Adicionar resultados RAG
    if rag_results and len(rag_results) > 0:
        response_parts.append("Encontrei as seguintes informações relevantes:\n")
        
        for i, result in enumerate(rag_results[:3], 1):
            response_parts.append(f"\n{i}. **{result['title']}**\n")
            response_parts.append(f"   {result['content'][:300]}...\n")
            
            if result.get('source_url'):
                response_parts.append(f"   Fonte: {result['source_url']}\n")
    else:
        response_parts.append("Não encontrei informações específicas na base de conhecimento sobre este tema.\n")
        response_parts.append("No entanto, posso ajudar com conceitos gerais de contabilidade e finanças.\n")
    
    # Adicionar contexto financeiro se disponível
    if context:
        response_parts.append("\n\n---\n\n")
        response_parts.append("Contexto Financeiro Disponível:\n")
        
        if context.get("empresa"):
            response_parts.append(f"- Empresa: {context['empresa']}\n")
        if context.get("dre"):
            response_parts.append(f"- DRE disponível\n")
        if context.get("balanco"):
            response_parts.append(f"- Balanço disponível\n")
    
    # Adicionar sugestão de ação
    response_parts.append("\n\n---\n\n")
    response_parts.append("Posso ajudar com:\n")
    response_parts.append("- Análise financeira detalhada\n")
    response_parts.append("- Cálculos de impostos\n")
    response_parts.append("- Geração de relatórios\n")
    response_parts.append("- Previsões de fluxo de caixa\n")
    
    return "".join(response_parts)
