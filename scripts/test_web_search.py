#!/usr/bin/env python3
"""
Script de teste para web search service.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.knowledge.web_search_service import search_web, search_official_docs

async def test_web_search():
    """Testa busca na web."""
    queries = [
        "NBC TG 26 atualizada",
        "taxa Selic hoje",
        "Lei 6.404/76 alterações recentes",
    ]
    
    print("🔍 Testando Web Search Service\n")
    print("=" * 60)
    
    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
        try:
            results = await search_web(query, max_results=3)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"\n  Resultado {i}:")
                    print(f"    Título: {result['title']}")
                    print(f"    URL: {result['url']}")
                    print(f"    Snippet: {result['snippet'][:200]}...")
                    print(f"    Source: {result['source']}")
            else:
                print("  ❌ Nenhum resultado encontrado")
                
        except Exception as e:
            print(f"  ❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Teste Web Search concluído")

async def test_official_docs():
    """Testa busca em documentos oficiais."""
    query = "NBC TG 26 apresentação"
    
    print(f"\n🔍 Testando Busca em Documentos Oficiais: {query}")
    print("-" * 60)
    
    try:
        results = await search_official_docs(query)
        
        if results:
            for i, result in enumerate(results, 1):
                print(f"\n  Resultado {i}:")
                print(f"    Título: {result['title']}")
                print(f"    URL: {result['url']}")
                print(f"    Fonte oficial: {result['official_source']}")
                print(f"    Snippet: {result['snippet'][:150]}...")
        else:
            print("  ❌ Nenhum resultado encontrado")
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_web_search())
    asyncio.run(test_official_docs())
