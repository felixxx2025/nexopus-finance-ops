#!/usr/bin/env python3
"""
Script para popular a base de conhecimento contábil.

Uso:
    python scripts/seed_knowledge.py

Requisitos:
    - sentence-transformers instalado (pip install sentence-transformers)
    - Banco de dados PostgreSQL rodando
    - Migration 003 executada

Observação:
    - Usa Sentence Transformers (HuggingFace) - 100% local e gratuito
    - Modelo: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions)
    - Baixa modelo automaticamente na primeira execução (~120MB)
"""
import asyncio
import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from apps.api.config import settings
from services.knowledge.knowledge_seeder import seed_knowledge_base
from services.knowledge.template_service import seed_templates


async def main():
    """Executa o seed da base de conhecimento."""
    print("🌱 Iniciando seed da base de conhecimento contábil...")
    print("📊 Database: {settings.database_url}")
    print("🤖 Modelo: Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)")
    print("   - 100% local e gratuito")
    print("   - Modelo baixado automaticamente na primeira execução (~120MB)")

    # Criar engine e sessão
    engine = create_async_engine(settings.database_url, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with AsyncSessionLocal() as db:
        try:
            # Seed knowledge base
            print("\n📚 Populando artigos de conhecimento...")
            kb_stats = await seed_knowledge_base(db)
            print(f"✅ Knowledge base: {kb_stats}")

            # Seed templates
            print("\n📋 Populando templates...")
            template_stats = await seed_templates(db)
            print(f"✅ Templates: {template_stats}")

            print("\n🎉 Seed concluído com sucesso!")
            print("\n📊 Resumo:")
            print(f"   - Normas: {kb_stats['normas']}")
            print(f"   - Conceitos: {kb_stats['conceitos']}")
            print(f"   - Glossário: {kb_stats['glossario']}")
            print(f"   - Casos de uso: {kb_stats['use_cases']}")
            print(f"   - Embeddings: {kb_stats['embeddings']}")
            print(f"   - Templates de relatórios: {template_stats['report_templates']}")
            print(f"   - Planos de contas: {template_stats['account_templates']}")

        except Exception as e:
            print(f"\n❌ Erro durante o seed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
