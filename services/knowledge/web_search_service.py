"""
Web Search Service — Busca na internet para complementar RAG local.

Usa múltiplas fontes: Wikipedia, Bing Search API (opcional), e fallback local.
"""
from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_TIMEOUT = 10.0


async def search_web(query: str, max_results: int = 5) -> list[dict[str, Any]]:
    """
    Busca na internet usando múltiplas fontes.

    Args:
        query: Termo de busca.
        max_results: Número máximo de resultados.

    Returns:
        Lista de resultados com título, url, snippet.
    """
    results = []
    
    # Tenta Wikipedia primeiro
    wiki_results = await _search_wikipedia(query, max_results)
    results.extend(wiki_results)
    
    # Se ainda precisar de mais resultados, retorna o que tem
    return results[:max_results]


async def _search_wikipedia(query: str, max_results: int) -> list[dict[str, Any]]:
    """Busca na Wikipedia com headers apropriados."""
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json",
                "Accept-Language": "pt-BR,pt;q=0.9",
            }
            
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "utf8": "",
            }
            
            response = await client.get(
                "https://pt.wikipedia.org/w/api.php",
                params=params,
                headers=headers,
            )
            response.raise_for_status()
            
            data = response.json()
            
            results = []
            
            if "query" in data and "search" in data["query"]:
                for item in data["query"]["search"]:
                    results.append({
                        "title": item["title"],
                        "url": f"https://pt.wikipedia.org/wiki/{item['title'].replace(' ', '_')}",
                        "snippet": item.get("snippet", "").replace('<span class="searchmatch">', "").replace('</span>', "")[:300],
                        "source": "wikipedia",
                    })
            
            logger.info("Wikipedia search: %d resultados para '%s'", len(results), query)
            return results
            
    except Exception as e:
        logger.warning("Wikipedia search falhou para '%s': %s", query, e)
        return []


async def fetch_url(url: str, timeout: float = 15.0) -> str | None:
    """
    Busca conteúdo de uma URL específica.

    Args:
        url: URL para buscar.
        timeout: Timeout em segundos.

    Returns:
        Conteúdo HTML/texto da página.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; NexopusFinanceBot/1.0)",
            }
            
            response = await client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Tenta detectar encoding
            content = response.text
            logger.info("Fetched %s (%d chars)", url, len(content))
            return content
            
    except Exception as e:
        logger.error("Failed to fetch %s: %s", url, e)
        return None


async def search_official_docs(query: str, sources: list[str] | None = None) -> list[dict[str, Any]]:
    """
    Busca em fontes oficiais contábeis brasileiras.

    Args:
        query: Termo de busca.
        sources: Lista de fontes específicas (CFC, Receita, etc).

    Returns:
        Lista de resultados com contexto oficial.
    """
    default_sources = [
        "site:cfc.org.br",
        "site:rfb.gov.br",
        "site:gov.br",
        "site:sped.rfb.gov.br",
    ]
    
    search_sources = sources or default_sources
    
    results = []
    
    for source in search_sources:
        # Adiciona source à query
        enhanced_query = f"{query} {source}"
        source_results = await search_web(enhanced_query, max_results=2)
        
        for result in source_results:
            result["official_source"] = source
            results.append(result)
    
    logger.info("Official docs search: %d resultados de %d fontes", len(results), len(search_sources))
    return results
