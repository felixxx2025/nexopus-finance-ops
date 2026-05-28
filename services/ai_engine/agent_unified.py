"""
Agent Unified — Agente unificado com todas as capacidades.

Combina:
- Generativo (stream_answer do agent_assistant)
- Executor (ferramentas do agent_executor)
- Preditivo (modelos do agent_predictive)
- Criativo (geração do agent_creative)
- Multi Documentos (processamento do agent_multidoc)
- Multimodal (processamento do agent_multimodal)
"""
from __future__ import annotations

import logging
from datetime import date
from decimal import Decimal
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from services.ai_engine.agent_assistant_local import stream_answer_local
from services.ai_engine.agent_executor import ToolRegistry, create_journal_entry, calculate_tax, generate_report
from services.ai_engine.agent_predictive import predict_cash_flow, predict_revenue, detect_anomalies, analyze_trends
from services.ai_engine.agent_creative_local import (
    generate_financial_report_local,
    generate_insights_local,
    generate_narrative_local,
    generate_recommendations_local,
)
from services.ai_engine.agent_multidoc import process_multiple_documents, combine_documents, compare_documents
from services.ai_engine.agent_multimodal import process_image, process_pdf_document, process_spreadsheet, process_audio

logger = logging.getLogger(__name__)


class UnifiedAgent:
    """Agente unificado com todas as capacidades."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.capabilities = {
            "generative": True,
            "executor": True,
            "predictive": True,
            "creative": True,
            "multidoc": True,
            "multimodal": True,
        }
    
    async def chat(
        self,
        question: str,
        context: dict[str, Any] | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Chat com o agente (capacidade generativa local).
        
        Args:
            question: Pergunta do usuário.
            context: Contexto financeiro.
            history: Histórico de conversa.
        
        Yields:
            Resposta em streaming.
        """
        async for chunk in stream_answer_local(question, context or {}, history, self.db):
            yield chunk
    
    async def execute_tool(
        self,
        tool_name: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Executa uma ferramenta (capacidade executor).
        
        Args:
            tool_name: Nome da ferramenta.
            **kwargs: Parâmetros da ferramenta.
        
        Returns:
            Resultado da execução.
        """
        tool = ToolRegistry.get_tool(tool_name)
        
        if not tool:
            return {
                "success": False,
                "error": f"Tool not found: {tool_name}",
            }
        
        # Executar ferramenta passando db como primeiro argumento
        result = await tool["func"](self.db, **kwargs)
        return result
    
    async def predict(
        self,
        prediction_type: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Executa uma previsão (capacidade preditiva).
        
        Args:
            prediction_type: Tipo de previsão (cash_flow, revenue, anomalies, trends).
            **kwargs: Parâmetros da previsão.
        
        Returns:
            Resultado da previsão.
        """
        if prediction_type == "cash_flow":
            return await predict_cash_flow(self.db, **kwargs)
        elif prediction_type == "revenue":
            return await predict_revenue(self.db, **kwargs)
        elif prediction_type == "anomalies":
            return await detect_anomalies(self.db, **kwargs)
        elif prediction_type == "trends":
            return await analyze_trends(self.db, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown prediction type: {prediction_type}",
            }
    
    async def create(
        self,
        creation_type: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Cria conteúdo criativo (capacidade criativa local).
        
        Args:
            creation_type: Tipo de criação (report, insights, narrative, recommendations).
            **kwargs: Parâmetros da criação.
        
        Returns:
            Conteúdo criado.
        """
        # Usa apenas versão local (100% independente)
        if creation_type == "report":
            return await generate_financial_report_local(self.db, **kwargs)
        elif creation_type == "insights":
            return await generate_insights_local(self.db, **kwargs)
        elif creation_type == "narrative":
            return await generate_narrative_local(self.db, **kwargs)
        elif creation_type == "recommendations":
            return await generate_recommendations_local(self.db, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown creation type: {creation_type}",
            }
    
    async def process_documents(
        self,
        file_paths: list[str],
        **kwargs,
    ) -> dict[str, Any]:
        """
        Processa múltiplos documentos (capacidade multi-documentos).
        
        Args:
            file_paths: Lista de caminhos de arquivos.
            **kwargs: Parâmetros adicionais.
        
        Returns:
            Resultado do processamento.
        """
        return await process_multiple_documents(self.db, file_paths, **kwargs)
    
    async def process_multimodal(
        self,
        file_path: str,
        file_type: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Processa arquivo multimodal (capacidade multimodal).
        
        Args:
            file_path: Caminho do arquivo.
            file_type: Tipo de arquivo (image, pdf, spreadsheet, audio).
            **kwargs: Parâmetros adicionais.
        
        Returns:
            Resultado do processamento.
        """
        if file_type == "image":
            return await process_image(self.db, file_path, **kwargs)
        elif file_type == "pdf":
            return await process_pdf_document(self.db, file_path, **kwargs)
        elif file_type == "spreadsheet":
            return await process_spreadsheet(self.db, file_path, **kwargs)
        elif file_type == "audio":
            return await process_audio(self.db, file_path, **kwargs)
        else:
            return {
                "success": False,
                "error": f"Unknown file type: {file_type}",
            }
    
    async def list_capabilities(self) -> dict[str, Any]:
        """
        Lista todas as capacidades disponíveis.
        
        Returns:
            Capacidades do agente.
        """
        return {
            "capabilities": self.capabilities,
            "tools": ToolRegistry.list_tools(),
            "prediction_types": ["cash_flow", "revenue", "anomalies", "trends"],
            "creation_types": ["report", "insights", "narrative", "recommendations"],
            "file_types": ["image", "pdf", "spreadsheet", "audio"],
        }
    
    async def autonomous_task(
        self,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Executa uma tarefa autônoma usando múltiplas capacidades.
        
        Args:
            task: Descrição da tarefa.
            context: Contexto adicional.
        
        Yields:
            Progresso da tarefa.
        """
        yield f"🤖 Analisando tarefa: {task}\n"
        
        # TODO: Implementar orquestração inteligente de tarefas
        # Por enquanto, usa o chat generativo local
        async for chunk in stream_answer_local(task, context or {}, None, self.db):
            yield chunk


async def create_unified_agent(db: AsyncSession) -> UnifiedAgent:
    """Cria uma instância do agente unificado."""
    return UnifiedAgent(db)
