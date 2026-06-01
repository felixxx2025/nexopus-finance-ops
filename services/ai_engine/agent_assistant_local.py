"""
Agent Assistant — Chat generativo 100% local usando RAG + Ollama (Qwen3:8b).

Usa RAG para buscar conhecimento relevante e Ollama com Qwen3:8b para gerar respostas
naturais e contextuais sem dependência de APIs externas.
"""
from __future__ import annotations

import logging
import os
from typing import Any, AsyncGenerator, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from services.knowledge.rag_service import search_knowledge

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3:8b")


async def stream_answer_local(
    question: str,
    context: dict[str, Any],
    history: Optional[list[dict[str, str]]] = None,
    db: Optional[AsyncSession] = None,
) -> AsyncGenerator[str, None]:
    """
    Gera resposta usando RAG + Ollama (Qwen3:8b) 100% local.
    
    Args:
        question: Pergunta do usuário.
        context: Dados financeiros da empresa.
        history: Histórico de mensagens anteriores.
        db: Sessão do banco para busca RAG.
    
    Yields:
        Chunks de texto da resposta em streaming.
    """
    try:
        # Buscar contexto RAG se db fornecido (RAG Avançado)
        rag_context = ""
        if db:
            rag_results = await search_knowledge(db, question, limit=5, min_similarity=0.2, enable_web_search=True)
            
            if rag_results:
                rag_context = "\n\n=== CONTEXTO RELEVANTE DA BASE DE CONHECIMENTO ===\n"
                for i, result in enumerate(rag_results[:5], 1):
                    rag_context += f"\n--- Documento {i}: {result['title']} ---\n"
                    rag_context += f"{result['content'][:800]}...\n"
                    if result.get('source_url'):
                        rag_context += f"Fonte: {result['source_url']}\n"
                    rag_context += f"Similaridade: {result.get('score', 'N/A')}\n"
        
        # Construir prompt para Ollama com Few-Shot Learning
        system_prompt = """Você é um assistente financeiro especializado em contabilidade brasileira.

=== EXEMPLOS DE RESPOSTAS ESPERADAS (FEW-SHOT) ===

Exemplo 1:
Q: Como calcular o IRPJ pelo lucro real?
A: O IRPJ pelo lucro real é calculado sobre o lucro contábil ajustado:

**Passo a passo:**
1. Partir do lucro líquido contábil
2. Adicionar adições (despesas não dedutíveis):
   - Multas fiscais
   - Despesas não comprovadas
   - Provisões não dedutíveis
3. Subtrair exclusões (receitas não tributáveis):
   - Dividendos recebidos
   - Lucros no exterior
4. Aplicar alíquotas:
   - 15% sobre o lucro real
   - 10% adicional sobre o excedente de R$ 20.000/mês

**Fórmula:** IRPJ = (Lucro Real × 15%) + (Excedente × 10%)

Exemplo 2:
Q: O que é a equação patrimonial?
A: A equação patrimonial é o princípio fundamental da contabilidade:

**Equação:** ATIVO = PASSIVO + PATRIMÔNIO LÍQUIDO

**Componentes:**
- **Ativo:** Bens e direitos da empresa (caixa, contas a receber, estoques)
- **Passivo:** Obrigações com terceiros (fornecedores, empréstimos, impostos)
- **Patrimônio Líquido:** Recursos dos proprietários (capital social, reservas, lucros)

Esta equação deve sempre se equilibrar, refletindo a origem e aplicação dos recursos.

Exemplo 3:
Q: Como estruturar uma DRE?
A: A DRE (Demonstração do Resultado do Exercício) deve seguir a estrutura da NBC TG 26:

**Estrutura Vertical:**
1. **Receita Bruta** (vendas + serviços)
2. **(-) Deduções** (impostos, devoluções, descontos)
3. **= Receita Líquida**
4. **(-) Custo dos Bens/Serviços** (CMV/CSP)
5. **= Lucro Bruto**
6. **(-) Despesas Operacionais** (vendas, administrativas, financeiras)
7. **= Resultado Operacional (EBIT)**
8. **(+/-) Resultado Não Operacional**
9. **= Lucro Antes do IR/CSLL**
10. **(-) IRPJ e CSLL**
11. **= Lucro Líquido do Exercício**

Conforme Lei 6.404/1976 Art. 187.

=== INSTRUÇÕES ===

Use estes exemplos como referência de:
- Profundidade técnica
- Estrutura clara com tópicos
- Exemplos práticos quando possível
- Citações de normas (NBC TG, Lei 6.404)

Seu objetivo é responder perguntas sobre:
- DRE (Demonstração do Resultado)
- Balanço Patrimonial
- Lei 6.404/1976 (Lei das S.A.)
- NBC TG (Normas Brasileiras de Contabilidade)
- Partida Dobrada
- Plano de Contas
- IRPJ e CSLL
- Equação Patrimonial

Use o contexto fornecido da base de conhecimento para fundamentar suas respostas.
Se não houver contexto relevante, responda com base em seu conhecimento geral.
Seja claro, objetivo, use exemplos práticos e responda em português."""

        # Adicionar contexto financeiro se disponível
        context_info = ""
        if context:
            context_info = "\n\n=== CONTEXTO FINANCEIRO ===\n"
            if context.get("empresa"):
                context_info += f"- Empresa: {context['empresa']}\n"
            if context.get("periodo"):
                context_info += f"- Período: {context['periodo']}\n"
            if context.get("dre"):
                context_info += f"- DRE disponível para análise\n"
            if context.get("balanco"):
                context_info += f"- Balanço Patrimonial disponível para análise\n"
        
        # Adicionar contexto de documentos enviados se disponível
        documents_context = ""
        if context and context.get("document_ids") and db:
            from sqlalchemy import select
            from packages.db.models import Document
            
            document_ids = context["document_ids"]
            if isinstance(document_ids, str):
                document_ids = [document_ids]
            
            documents_context = "\n\n=== CONTEXTO DE DOCUMENTOS ENVIADOS ===\n"
            for doc_id in document_ids[:3]:  # Limitar a 3 documentos
                try:
                    result = await db.execute(
                        select(Document).where(Document.id == doc_id)
                    )
                    doc = result.scalar_one_or_none()
                    if doc and doc.parsed:
                        documents_context += f"\n--- Documento: {doc.original_filename or doc.type} ---\n"
                        documents_context += f"Tipo: {doc.type}\n"
                        documents_context += f"Status: {doc.status}\n"
                        # Nota: Conteúdo do documento precisaria ser extraído do storage
                        # Por enquanto, apenas metadados
                except Exception as e:
                    logger.warning("Erro ao buscar documento %s: %s", doc_id, e)
                    continue
        
        # Construir mensagens para Ollama
        messages = [
            {"role": "system", "content": system_prompt},
        ]
        
        # Adicionar histórico
        if history:
            messages.extend(history[-5:])  # Últimas 5 mensagens
        
        # Adicionar contexto e pergunta atual
        user_message = f"{rag_context}{context_info}{documents_context}\n\nPergunta: {question}"
        messages.append({"role": "user", "content": user_message})
        
        # Chamar Ollama com streaming
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "num_ctx": 4096,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    }
                },
                timeout=120.0
            )
            
            if response.status_code != 200:
                logger.error("Ollama retornou status %d: %s", response.status_code, response.text)
                yield f"\n\n[Erro ao conectar com Ollama: HTTP {response.status_code}]"
                return
            
            # Processar streaming
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    import json
                    data = json.loads(line)
                    if "message" in data and "content" in data["message"]:
                        content = data["message"]["content"]
                        if content:
                            yield content
                    if "done" in data and data["done"]:
                        break
                except json.JSONDecodeError:
                    continue
        
    except Exception as e:
        logger.error("Agent Assistant com Ollama falhou: %s", e)
        yield f"\n\n[Erro ao gerar resposta: {e}]\n\nVerifique se o Ollama está rodando e o modelo Qwen3:8b está baixado."

