#!/usr/bin/env python3
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

async def check_knowledge():
    engine = create_async_engine('postgresql+asyncpg://postgres:postgres@postgres:5432/nexopus')
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as db:
        # Check knowledge articles
        result = await db.execute(text('SELECT COUNT(*) FROM knowledge_articles'))
        count = result.scalar()
        print(f'Knowledge articles: {count}')
        
        # Check knowledge embeddings
        result = await db.execute(text('SELECT COUNT(*) FROM knowledge_embeddings'))
        count = result.scalar()
        print(f'Knowledge embeddings: {count}')
        
        # Check companies
        result = await db.execute(text('SELECT COUNT(*) FROM companies'))
        count = result.scalar()
        print(f'Companies: {count}')
        
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(check_knowledge())
