#!/usr/bin/env python3
"""
Script de teste simples para busca lexical.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text

async def test_lexical():
    """Testa busca lexical direta."""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:7432/nexopus_test"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    query = "EBITDA"

    async with AsyncSessionLocal() as db:
        print(f"🔍 Testando busca lexical para: {query}\n")
        
        query_sql = """
            SELECT 
                id,
                title,
                content,
                category,
                ts_rank(to_tsvector('portuguese', title || ' ' || content), plainto_tsquery('portuguese', $1)) as similarity
            FROM knowledge_articles
            WHERE to_tsvector('portuguese', title || ' ' || content) @@ plainto_tsquery('portuguese', $1)
            LIMIT 3
        """

        result = await db.execute(text(query_sql), [query])
        rows = result.fetchall()
        
        print(f"📊 Resultados: {len(rows)}\n")
        
        for row in rows:
            print(f"ID: {row[0]}")
            print(f"Título: {row[1]}")
            print(f"Similaridade: {row[4]}")
            print("-" * 60)
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_lexical())
