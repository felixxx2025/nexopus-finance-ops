"""
RAG Service — Retrieval-Augmented Generation para conhecimento contábil.

Combina busca semântica (pgvector) com busca lexical (tsvector) para máxima precisão.
Cache inteligente no Redis para performance.
Integração com web search para complementar base local.
"""
from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import KnowledgeArticle, KnowledgeEmbedding
from services.knowledge.embedding_service import (
    cosine_similarity,
    generate_embedding,
    get_cached_embedding,
)
from services.knowledge.web_search_service import search_web, search_official_docs

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=1)


async def _generate_embedding_async(text: str) -> list[float]:
    """Wrapper assíncrono para generate_embedding (Sentence Transformers)."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, generate_embedding, text)


async def search_knowledge(
    db: AsyncSession,
    query: str,
    category: str | None = None,
    limit: int = 5,
    min_similarity: float = 0.7,
    enable_web_search: bool = True,
) -> list[dict[str, Any]]:
    """
    Busca conhecimento usando RAG (busca semântica + lexical + web search).

    Args:
        db: Sessão do banco de dados.
        query: Query do usuário.
        category: Filtrar por categoria (opcional).
        limit: Número máximo de resultados.
        min_similarity: Similaridade mínima (0-1).
        enable_web_search: Se True, busca na internet se resultados locais forem insuficientes.

    Returns:
        Lista de artigos relevantes com scores.
    """
    # 1. Gerar embedding da query
    cache_key = f"rag_query:{hash(query)}"
    query_embedding = await get_cached_embedding(cache_key)

    if not query_embedding:
        query_embedding = await _generate_embedding_async(query)
        if query_embedding:
            from services.knowledge.embedding_service import cache_embedding
            await cache_embedding(cache_key, query_embedding, ttl=1800)  # 30 min

    if not query_embedding or all(v == 0.0 for v in query_embedding):
        logger.warning("Embedding inválido, usando busca lexical apenas.")
        return await _search_lexical(db, query, category, limit)

    # 2. Busca semântica com pgvector (HNSW index)
    # Converter embedding para string para pgvector (formato: '[0.1,0.2,...]')
    embedding_str = f"[{','.join(map(str, query_embedding))}]"
    logger.debug("Embedding string (primeiros 100 chars): %s", embedding_str[:100])
    semantic_results = await _search_semantic(db, embedding_str, category, limit * 2)

    # 3. Busca lexical como fallback/boost
    lexical_results = await _search_lexical(db, query, category, limit * 2)

    # 4. Combinar e rerank
    combined = _combine_results(semantic_results, lexical_results)

    # 5. Filtrar por similaridade mínima e limitar
    filtered = [r for r in combined if r["similarity"] >= min_similarity]
    
    # 6. Web search fallback se resultados locais insuficientes
    if enable_web_search and len(filtered) < limit:
        logger.info("Resultados locais insuficientes (%d/%d), ativando web search", len(filtered), limit)
        
        # Busca na web
        web_results = await search_web(query, max_results=limit - len(filtered))
        
        # Filtra resultados irrelevantes (palavras-chave contábeis)
        accounting_keywords = ["contábil", "contabilidade", "financeiro", "tributário", "fiscal", "balanço", "dre", "lucro", "imposto", "norma", "lei", "cfc", "receita", "cpc", "sped", "irpj", "csll", "empresa", "econômico"]
        
        # Excluir termos que causam falsos positivos
        exclude_keywords = ["notícia", "política", "eleição", "campanha", "garden", "podolatria"]
        
        for web_result in web_results:
            # Verifica se o resultado é relevante para contabilidade
            title_lower = web_result["title"].lower()
            snippet_lower = web_result["snippet"].lower()
            
            # Excluir resultados com termos não relevantes
            if any(excl in title_lower or excl in snippet_lower for excl in exclude_keywords):
                continue
            
            # Verifica relevância com palavras-chave completas (não substrings)
            # NBC específico para contabilidade (NBC TG, não NBC News)
            is_relevant = any(f" {kw} " in f" {title_lower} " or f" {kw} " in f" {snippet_lower} " for kw in accounting_keywords)
            
            # Caso especial: NBC TG é relevante, NBC News não
            if "nbc" in title_lower and "tg" not in title_lower:
                is_relevant = False
            
            # Se não for relevante, só adiciona se não tiver resultados locais suficientes
            if is_relevant or len(filtered) == 0:
                filtered.append({
                    "id": f"web_{hash(web_result['url'])}",
                    "title": web_result["title"],
                    "content": web_result["snippet"],
                    "category": "web",
                    "subcategory": None,
                    "tags": [],
                    "source": web_result.get("source", "web"),
                    "source_url": web_result["url"],
                    "similarity": 0.5 if is_relevant else 0.3,  # Score menor para não relevante
                    "method": "web_search",
                })
    
    return filtered[:limit]


async def _search_semantic(
    db: AsyncSession,
    embedding: str,  # String formatada para pgvector: '[0.1,0.2,...]'
    category: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Busca semântica usando pgvector com índice HNSW.

    Usa operador <=> (cosine distance) do pgvector.
    """
    try:
        # Query SQL direta para usar operador vector
        # Usar string interpolation para embedding (pgvector requer formato específico)
        query_sql = f"""
            SELECT 
                ka.id,
                ka.title,
                ka.content,
                ka.category,
                ka.subcategory,
                ka.tags,
                ka.source,
                ka.source_url,
                (1 - (ke.embedding <=> '{embedding}'::vector)) as similarity
            FROM knowledge_embeddings ke
            JOIN knowledge_articles ka ON ke.article_id = ka.id
            WHERE 1=1
        """

        if category:
            query_sql += f" AND ka.category = '{category}'"

        query_sql += f" ORDER BY ke.embedding <=> '{embedding}'::vector LIMIT {limit}"

        result = await db.execute(text(query_sql))
        rows = result.fetchall()

        return [
            {
                "id": str(row.id),
                "title": row.title,
                "content": row.content,
                "category": row.category,
                "subcategory": row.subcategory,
                "tags": row.tags or [],
                "source": row.source,
                "source_url": row.source_url,
                "similarity": float(row.similarity),
                "method": "semantic",
            }
            for row in rows
        ]

    except Exception as e:
        logger.error("Erro na busca semântica: %s", e)
        return []


async def _search_lexical(
    db: AsyncSession,
    query: str,
    category: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """
    Busca lexical usando full-text search (tsvector) com GIN index.
    """
    try:
        # Usar full-text search com tsvector
        query_sql = """
            SELECT 
                id,
                title,
                content,
                category,
                subcategory,
                tags,
                source,
                source_url,
                ts_rank(to_tsvector('portuguese', title || ' ' || content), plainto_tsquery('portuguese', :query)) as similarity
            FROM knowledge_articles
            WHERE to_tsvector('portuguese', title || ' ' || content) @@ plainto_tsquery('portuguese', :query)
        """

        params = {"query": query}

        if category:
            query_sql += " AND category = :category"
            params["category"] = category

        query_sql += f" LIMIT {limit}"

        result = await db.execute(text(query_sql), params)
        rows = result.fetchall()

        results = []
        for row in rows:
            results.append({
                "id": str(row[0]),
                "title": row[1],
                "content": row[2],
                "category": row[3],
                "subcategory": row[4],
                "tags": row[5] if row[5] else [],
                "source": row[6],
                "source_url": row[7],
                "similarity": float(row[8]) if row[8] else 0.0,
                "method": "lexical",
            })
        return results

    except Exception as e:
        logger.error("Erro na busca lexical: %s", e)
        return []


def _combine_results(
    semantic: list[dict[str, Any]],
    lexical: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Combina resultados semânticos e lexicais com reranking.

    Prioriza semântico mas boosta resultados que aparecem em ambos.
    """
    if not semantic and not lexical:
        return []

    combined = {}
    seen_ids = set()

    # Adiciona resultados semânticos
    for item in semantic:
        if not isinstance(item, dict):
            continue
        article_id = item.get("id")
        if article_id:
            combined[article_id] = item
            seen_ids.add(article_id)

    # Boosta resultados lexicais que também estão no semântico
    for item in lexical:
        if not isinstance(item, dict):
            continue
        article_id = item.get("id")
        if article_id:
            if article_id in combined:
                # Boost: aumenta similaridade em 20%
                combined[article_id]["similarity"] = min(1.0, combined[article_id]["similarity"] * 1.2)
                combined[article_id]["method"] = "hybrid"
            elif article_id not in seen_ids:
                # Adiciona resultados apenas lexicais com score menor
                item["similarity"] = item["similarity"] * 0.7
                combined[article_id] = item
                seen_ids.add(article_id)

    # Ordena por similaridade
    sorted_results = sorted(combined.values(), key=lambda x: x["similarity"], reverse=True)
    return sorted_results


async def get_article_by_id(db: AsyncSession, article_id: str) -> dict[str, Any] | None:
    """
    Recupera artigo completo por ID.

    Args:
        db: Sessão do banco de dados.
        article_id: ID do artigo.

    Returns:
        Dicionário com dados do artigo ou None.
    """
    try:
        from uuid import UUID

        stmt = select(KnowledgeArticle).where(KnowledgeArticle.id == UUID(article_id))
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()

        if not article:
            return None

        return {
            "id": str(article.id),
            "title": article.title,
            "content": article.content,
            "category": article.category,
            "subcategory": article.subcategory,
            "tags": article.tags or [],
            "source": article.source,
            "source_url": article.source_url,
            "language": article.language,
            "metadata": article.metadata_,
            "created_at": article.created_at.isoformat(),
            "updated_at": article.updated_at.isoformat(),
        }

    except Exception as e:
        logger.error("Erro ao recuperar artigo: %s", e)
        return None


async def list_articles(
    db: AsyncSession,
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Lista artigos com paginação e filtros.

    Args:
        db: Sessão do banco de dados.
        category: Filtrar por categoria (opcional).
        limit: Limite de resultados.
        offset: Offset para paginação.

    Returns:
        Lista de artigos.
    """
    try:
        stmt = select(KnowledgeArticle)

        if category:
            stmt = stmt.where(KnowledgeArticle.category == category)

        stmt = stmt.order_by(KnowledgeArticle.created_at.desc()).limit(limit).offset(offset)

        result = await db.execute(stmt)
        articles = result.scalars().all()

        return [
            {
                "id": str(a.id),
                "title": a.title,
                "category": a.category,
                "subcategory": a.subcategory,
                "tags": a.tags or [],
                "source": a.source,
                "created_at": a.created_at.isoformat(),
            }
            for a in articles
        ]

    except Exception as e:
        logger.error("Erro ao listar artigos: %s", e)
        return []
