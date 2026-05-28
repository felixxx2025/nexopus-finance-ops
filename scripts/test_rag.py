#!/usr/bin/env python3
"""
Script de teste para RAG - Retrieval-Augmented Generation.

Testa busca semântica e lexical na base de conhecimento contábil.
"""
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from services.knowledge.rag_service import search_knowledge


async def test_rag():
    """Testa o serviço RAG com diferentes queries."""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:7432/nexopus_test"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    queries = [
        "O que é EBITDA?",
        "Como calcular o lucro líquido?",
        "O que diz a NBC TG 26?",
        "Explique a partida dobrada",
        "Quais são os componentes do Balanço Patrimonial?",
    ]

    async with AsyncSessionLocal() as db:
        print("🧪 Testando RAG - Retrieval-Augmented Generation\n")
        print("=" * 60)
        
        for i, query in enumerate(queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 60)
            
            try:
                # Testar busca lexical primeiro (sem embeddings)
                from services.knowledge.rag_service import _search_lexical
                try:
                    lexical = await _search_lexical(db, query, None, 3)
                    print(f"  🔍 Busca lexical: {len(lexical)} resultados")
                    if lexical:
                        for r in lexical[:2]:
                            print(f"    - {r['title'][:50]}... (score: {r['similarity']:.4f})")
                except Exception as e:
                    print(f"  ❌ Erro na busca lexical: {e}")

                # Testar busca semântica
                try:
                    results = await search_knowledge(db, query, limit=3, min_similarity=0.3, enable_web_search=True)
                    
                    if results:
                        for j, result in enumerate(results, 1):
                            print(f"\n  ✅ Resultado {j}:")
                            print(f"    Título: {result['title']}")
                            print(f"    Categoria: {result['category']}")
                            print(f"    Similaridade: {result['similarity']:.4f}")
                            print(f"    Método: {result.get('method', 'unknown')}")
                            if result.get('source_url'):
                                print(f"    URL: {result['source_url']}")
                            print(f"    Conteúdo: {result['content'][:200]}...")
                    else:
                        print("  ❌ Nenhum resultado encontrado (RAG)")
                except Exception as e:
                    print(f"  ❌ Erro na busca RAG: {e}")
                    
            except Exception as e:
                print(f"  ❌ Erro: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("✅ Teste RAG concluído")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(test_rag())
