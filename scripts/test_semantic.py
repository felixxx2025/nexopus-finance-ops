#!/usr/bin/env python3
"""
Script de teste para busca semântica com pgvector.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from services.knowledge.embedding_service import generate_embedding

async def test_semantic():
    """Testa busca semântica direta."""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:7432/nexopus_test"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    query = "EBITDA"
    
    # Gerar embedding para a query
    print(f"🔍 Gerando embedding para: {query}")
    embedding = generate_embedding(query)
    print(f"📊 Embedding dimension: {len(embedding)}")
    print(f"📊 Primeiros 5 valores: {embedding[:5]}")
    
    # Converter para string pgvector
    embedding_str = f"[{','.join(map(str, embedding))}]"
    print(f"📊 Embedding string (primeiros 100 chars): {embedding_str[:100]}")
    
    async with AsyncSessionLocal() as db:
        print(f"\n🔍 Testando busca semântica no PostgreSQL\n")
        
        query_sql = f"""
            SELECT 
                ka.id,
                ka.title,
                ka.content,
                ka.category,
                (1 - (ke.embedding <=> '{embedding_str}'::vector)) as similarity
            FROM knowledge_embeddings ke
            JOIN knowledge_articles ka ON ke.article_id = ka.id
            ORDER BY ke.embedding <=> '{embedding_str}'::vector
            LIMIT 3
        """

        try:
            result = await db.execute(text(query_sql))
            rows = result.fetchall()
            
            print(f"📊 Resultados: {len(rows)}\n")
            
            for row in rows:
                print(f"ID: {row[0]}")
                print(f"Título: {row[1]}")
                print(f"Similaridade: {row[4]}")
                print("-" * 60)
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_semantic())
