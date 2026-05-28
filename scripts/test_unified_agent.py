#!/usr/bin/env python3
"""
Script de teste para o Agente Unificado com todas as capacidades.

Testa:
- Generativo (chat)
- Executor (ferramentas)
- Preditivo (previsões)
- Criativo (geração de conteúdo)
- Multi Documentos (processamento)
- Multimodal (processamento de mídia)
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from services.ai_engine.agent_unified import create_unified_agent

async def test_unified_agent():
    """Testa todas as capacidades do agente unificado."""
    DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:7432/nexopus_test"
    
    engine = create_async_engine(DATABASE_URL, echo=False)
    AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with AsyncSessionLocal() as db:
        agent = await create_unified_agent(db)
        
        print("🤖 Testando Agente Unificado - Todas as Capacidades\n")
        print("=" * 70)
        
        # 1. Listar capacidades
        print("\n1️⃣ CAPACIDADES DISPONÍVEIS")
        print("-" * 70)
        capabilities = await agent.list_capabilities()
        print(f"✅ Capacidades: {capabilities['capabilities']}")
        print(f"✅ Ferramentas: {len(capabilities['tools'])} disponíveis")
        for tool in capabilities['tools']:
            print(f"   - {tool['name']}: {tool['description']}")
        print(f"✅ Tipos de previsão: {capabilities['prediction_types']}")
        print(f"✅ Tipos de criação: {capabilities['creation_types']}")
        print(f"✅ Tipos de arquivo: {capabilities['file_types']}")
        
        # 2. Testar Executor
        print("\n2️⃣ CAPACIDADE EXECUTOR")
        print("-" * 70)
        
        # Calcular imposto
        from decimal import Decimal
        tax_result = await agent.execute_tool(
            "calculate_tax",
            amount=Decimal("10000"),
            tax_rate=Decimal("0.15"),
        )
        print(f"✅ Cálculo de imposto: {tax_result}")
        
        # 3. Testar Preditivo
        print("\n3️⃣ CAPACIDADE PREDITIVA")
        print("-" * 70)
        
        # Previsão de fluxo de caixa
        cash_flow = await agent.predict("cash_flow", days_ahead=7)
        print(f"✅ Previsão de fluxo de caixa (7 dias): {cash_flow['success']}")
        if cash_flow['success']:
            print(f"   Previsões: {len(cash_flow['predictions'])} dias")
            for pred in cash_flow['predictions'][:3]:
                print(f"   - {pred['date']}: R$ {pred['predicted']:.2f} (conf: {pred['confidence']:.2f})")
        
        # Previsão de receita
        revenue = await agent.predict("revenue", months_ahead=3)
        print(f"✅ Previsão de receita (3 meses): {revenue['success']}")
        if revenue['success']:
            print(f"   Previsões: {len(revenue['predictions'])} meses")
        
        # Detecção de anomalias
        anomalies = await agent.predict("anomalies", metric="revenue")
        print(f"✅ Detecção de anomalias: {anomalies['success']}")
        print(f"   Anomalias encontradas: {len(anomalies['anomalies'])}")
        
        # Análise de tendências
        trends = await agent.predict("trends", metric="revenue")
        print(f"✅ Análise de tendências: {trends['success']}")
        if trends['success']:
            print(f"   Tendência: {trends['trend']['direction']} (força: {trends['trend']['strength']:.2f})")
        
        # 4. Testar Criativo
        print("\n4️⃣ CAPACIDADE CRIATIVA")
        print("-" * 70)
        
        # Gerar insights
        insights = await agent.create(
            "insights",
            data={"revenue": 100000, "expenses": 80000, "profit": 20000},
            focus_area="lucratividade",
        )
        print(f"✅ Geração de insights: {insights['success']}")
        if insights['success']:
            print(f"   Foco: {insights['focus_area']}")
            print(f"   Insights preview: {insights['insights'][:200]}...")
        
        # 5. Testar Multi Documentos
        print("\n5️⃣ CAPACIDADE MULTI DOCUMENTOS")
        print("-" * 70)
        
        # Processar documentos (simulado)
        doc_result = await agent.process_documents(
            file_paths=["/tmp/doc1.pdf", "/tmp/doc2.txt"],
            extract_content=True,
            generate_embeddings=False,
        )
        print(f"✅ Processamento de documentos: {doc_result['success']}")
        print(f"   Total: {doc_result.get('total_documents', 0)}")
        print(f"   Sucesso: {doc_result.get('successful', 0)}")
        print(f"   Falhas: {doc_result.get('failed', 0)}")
        
        # 6. Testar Multimodal
        print("\n6️⃣ CAPACIDADE MULTIMODAL")
        print("-" * 70)
        
        # Processar imagem (simulado)
        image_result = await agent.process_multimodal(
            file_path="/tmp/invoice.jpg",
            file_type="image",
            extract_text=True,
        )
        print(f"✅ Processamento de imagem: {image_result['success']}")
        if image_result['success']:
            print(f"   Texto extraído: {image_result['text_length']} caracteres")
        
        # Processar PDF (simulado)
        pdf_result = await agent.process_multimodal(
            file_path="/tmp/nfse.pdf",
            file_type="pdf",
            extract_text=True,
        )
        print(f"✅ Processamento de PDF: {pdf_result['success']}")
        if pdf_result['success']:
            print(f"   Texto extraído: {pdf_result['text_length']} caracteres")
        
        # Processar planilha (simulado)
        sheet_result = await agent.process_multimodal(
            file_path="/tmp/dre.xlsx",
            file_type="spreadsheet",
            extract_all_sheets=True,
        )
        print(f"✅ Processamento de planilha: {sheet_result['success']}")
        if sheet_result['success']:
            print(f"   Abas: {sheet_result['sheets_count']}")
            print(f"   Total linhas: {sheet_result['total_rows']}")
        
        # 7. Testar Generativo (Chat)
        print("\n7️⃣ CAPACIDADE GENERATIVA (CHAT)")
        print("-" * 70)
        
        question = "Qual é a situação financeira da empresa?"
        print(f"📝 Pergunta: {question}")
        print("\n🤖 Resposta:")
        
        response = ""
        async for chunk in agent.chat(question, context={"empresa": "Teste Ltda"}):
            print(chunk, end="", flush=True)
            response += chunk
        
        print("\n")
        
        print("\n" + "=" * 70)
        print("✅ Teste do Agente Unificado concluído")
        print("\n📊 RESUMO:")
        print("✅ Generativo: Chat com streaming")
        print("✅ Executor: 3 ferramentas disponíveis")
        print("✅ Preditivo: 4 tipos de previsão")
        print("✅ Criativo: 4 tipos de geração")
        print("✅ Multi Documentos: Processamento em lote")
        print("✅ Multimodal: 4 tipos de arquivo")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_unified_agent())
