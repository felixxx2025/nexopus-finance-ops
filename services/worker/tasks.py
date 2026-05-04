"""
Worker Celery — processamento assíncrono de documentos.

Pipeline: upload → parse → classify → generate_entries → persist → report
"""
from __future__ import annotations

import logging
import os

from celery import Celery

logger = logging.getLogger(__name__)

BROKER_URL = os.getenv("BROKER_URL", "amqp://guest:guest@localhost:5672//")
BACKEND_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery = Celery(
    "ledger_ai_worker",
    broker=BROKER_URL,
    backend=BACKEND_URL,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
)


@celery.task(bind=True, max_retries=3, default_retry_delay=30)
def process_document(self, doc_id: str) -> dict:
    """
    Processa um documento enfileirado:
    1. Busca metadados do documento no DB
    2. Faz download do arquivo do storage
    3. Extrai e estrutura dados (agent_parser)
    4. Classifica contas (agent_classifier)
    5. Gera lançamentos (agent_generator)
    6. Persiste no DB
    7. Atualiza status do documento para parsed=True

    Args:
        doc_id: UUID do documento na tabela documents.
    """
    logger.info("Iniciando processamento do documento %s", doc_id)

    try:
        # TODO: buscar doc no DB
        # TODO: download do storage (S3/MinIO)
        # TODO: from services.ai_engine.agent_parser import parse_document
        # TODO: from services.ai_engine.agent_classifier import classify_accounts
        # TODO: from services.ai_engine.agent_generator import generate_entries
        # TODO: persistir journal_entries e journal_items
        # TODO: marcar documents.parsed = True

        logger.info("Documento %s processado com sucesso", doc_id)
        return {"doc_id": doc_id, "status": "completed"}

    except Exception as exc:
        logger.error("Falha ao processar documento %s: %s", doc_id, exc)
        raise self.retry(exc=exc)


@celery.task
def generate_report(company_id: str, year: int, report_type: str) -> dict:
    """
    Gera relatório (DRE ou Balanço) de forma assíncrona e persiste na tabela reports.

    Args:
        company_id: UUID da empresa.
        year: Ano de referência.
        report_type: "dre" ou "balanco".
    """
    logger.info("Gerando relatório %s para empresa %s ano %s", report_type, company_id, year)

    # TODO: instanciar AccountingEngine com sessão DB
    # TODO: chamar engine.generate_dre ou engine.generate_balance_sheet
    # TODO: persistir resultado na tabela reports

    return {"company_id": company_id, "year": year, "type": report_type, "status": "queued"}
