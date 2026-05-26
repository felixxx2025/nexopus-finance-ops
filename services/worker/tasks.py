"""
Worker Celery — processamento assíncrono de documentos.

Pipeline: upload → parse → classify → generate_entries → persist → report → forecast → audit

Estados do documento (Document.status):
  uploaded        — arquivo recebido, aguardando processamento
  processing      — worker em execução
  processed       — concluído com sucesso
  failed          — erro irrecuperável após retries
  needs_review    — processado com alertas de compliance / baixa confiança
"""
from __future__ import annotations

import logging
import os
import tempfile
from datetime import date, timedelta

from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")

BROKER_URL = os.getenv("BROKER_URL", "amqp://nexopus:rabbit_dev_pass@localhost:5672//")
BACKEND_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

_ASYNC_DB_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://ledger:ledger_dev_pass@localhost:5432/ledger_ai")
SYNC_DATABASE_URL = _ASYNC_DB_URL.replace("postgresql+asyncpg://", "postgresql://")

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "http://localhost:9000")
S3_ACCESS_KEY = os.getenv("S3_ACCESS_KEY", "nexopus_minio")
S3_SECRET_KEY = os.getenv("S3_SECRET_KEY", "minio_dev_pass")
S3_BUCKET = os.getenv("S3_BUCKET", "ledger-docs")

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
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "services.worker.tasks.process_document": {"queue": "ai"},
        "services.worker.tasks.run_forecast_task": {"queue": "ai"},
        "services.worker.tasks.run_audit_task": {"queue": "ai"},
        "services.worker.tasks.generate_report": {"queue": "reports"},
        "services.worker.tasks.generate_daily_reports": {"queue": "reports"},
        "services.worker.tasks.cleanup_temp_files": {"queue": "default"},
    },
    # ── Tarefas agendadas (Celery Beat) ─────────────────────────────────────
    beat_schedule={
        "daily-dre-report": {
            "task": "services.worker.tasks.generate_daily_reports",
            "schedule": crontab(hour=6, minute=0),
            "kwargs": {"report_type": "dre"},
        },
        "daily-forecast": {
            "task": "services.worker.tasks.run_forecast_all_companies",
            "schedule": crontab(hour=6, minute=30),
        },
        "weekly-audit": {
            "task": "services.worker.tasks.run_audit_all_companies",
            "schedule": crontab(hour=2, minute=0, day_of_week=0),  # Domingo 2h
        },
        "hourly-cleanup": {
            "task": "services.worker.tasks.cleanup_temp_files",
            "schedule": crontab(minute=0),  # A cada hora
        },
    },
)


def _get_db_session():
    """Cria sessão síncrona do SQLAlchemy para uso no worker."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(SYNC_DATABASE_URL, pool_pre_ping=True)
    Session = sessionmaker(bind=engine)
    return Session()


def _download_from_storage(doc_id: str, file_url: str) -> str:
    """Faz download do arquivo do MinIO/S3 para arquivo temporário."""
    import boto3
    from botocore.config import Config

    s3 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        aws_access_key_id=S3_ACCESS_KEY,
        aws_secret_access_key=S3_SECRET_KEY,
        config=Config(signature_version="s3v4"),
    )

    key = file_url.split("/", 1)[-1] if "/" in file_url else file_url
    ext = key.rsplit(".", 1)[-1] if "." in key else "tmp"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    s3.download_fileobj(S3_BUCKET, key, tmp)
    tmp.flush()
    return tmp.name


def _persist_entries(db, company_id: str, entries: list[dict]) -> None:
    """Persiste journal_entries e journal_items no banco de dados."""
    import uuid
    from packages.db.models import JournalEntry, JournalItem  # type: ignore

    for entry_data in entries:
        je = entry_data.get("journal_entry", {})
        items = entry_data.get("items", [])

        try:
            cid = uuid.UUID(company_id)
        except ValueError:
            logger.warning("company_id '%s' não é UUID válido, pulando", company_id)
            continue

        journal_entry = JournalEntry(
            id=uuid.UUID(je.get("id", str(uuid.uuid4()))),
            company_id=cid,
            date=date.fromisoformat(je.get("date", date.today().isoformat())),
            description=je.get("description", ""),
        )
        db.add(journal_entry)

        for item in items:
            try:
                amount_val = float(item.get("amount", 0))
                if amount_val <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            journal_item = JournalItem(
                id=uuid.UUID(item.get("id", str(uuid.uuid4()))),
                entry_id=journal_entry.id,
                account_id=uuid.UUID(item.get("account_id", str(uuid.uuid4()))),
                type=item.get("type", "debit"),
                amount=amount_val,
            )
            db.add(journal_item)

    db.commit()


# ═══════════════════════════════════════════════════════════════════════════════
# TAREFAS PRINCIPAIS
# ═══════════════════════════════════════════════════════════════════════════════

@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, doc_id: str) -> dict:
    """
    Pipeline completo de processamento de documento:
    1. Buscar metadados do documento no DB
    2. Download do arquivo do storage (MinIO/S3)
    3. Extração estruturada (Agent Parser - LLaMA 3.1 405B)
    4. Classificação de contas RFB (Agent Classifier - Claude Sonnet 4.6)
    5. Geração de lançamentos em partida dobrada (Agent Generator - GPT-5.2)
    6. Validação de compliance (double-entry)
    7. Persiste journal_entries e journal_items no DB
    8. Marca documento como processado
    9. Enfileira geração de relatório + forecast
    """
    import uuid
    try:
        from packages.db.models import Document  # type: ignore
    except ModuleNotFoundError:
        from db.models import Document  # type: ignore

    try:
        from services.ai_engine.agent_classifier import classify_accounts  # type: ignore
        from services.ai_engine.agent_generator import generate_entries  # type: ignore
        from services.ai_engine.agent_parser import parse_document  # type: ignore
        from services.compliance.rules import validate_double_entry  # type: ignore
    except ModuleNotFoundError:
        from ai_engine.agent_classifier import classify_accounts  # type: ignore
        from ai_engine.agent_generator import generate_entries  # type: ignore
        from ai_engine.agent_parser import parse_document  # type: ignore
        from compliance.rules import validate_double_entry  # type: ignore

    logger.info("[process_document] Iniciando doc_id=%s", doc_id)
    db = _get_db_session()
    tmp_path: str | None = None

    try:
        # 1. Buscar documento no DB
        doc = db.query(Document).filter(Document.id == uuid.UUID(doc_id)).first()
        if not doc:
            logger.error("[process_document] Documento %s não encontrado", doc_id)
            return {"doc_id": doc_id, "status": "not_found"}

        if doc.parsed:
            logger.info("[process_document] Documento %s já processado", doc_id)
            return {"doc_id": doc_id, "status": "already_processed"}

        # Marca como 'processing'
        doc.status = "processing"
        db.commit()

        # 2. Download do storage
        tmp_path = _download_from_storage(doc_id, doc.file_url)
        logger.info("[process_document] Arquivo baixado: %s", tmp_path)

        # 3. Extração via Agent Parser
        structured_data = parse_document(tmp_path)
        lancamentos = structured_data.get("lancamentos", [])
        ai_confidence = structured_data.get("confianca", 0.0)
        logger.info("[process_document] %d lançamentos extraídos (confiança=%.2f)", len(lancamentos), ai_confidence)

        # 4. Classificação via Agent Classifier
        classified_data = classify_accounts(structured_data)

        # 5. Geração de partidas via Agent Generator
        entries = generate_entries(classified_data)
        logger.info("[process_document] %d entries geradas", len(entries))

        # 6. Validação de compliance
        compliance_errors = 0
        for entry in entries:
            try:
                validate_double_entry(entry.get("items", []))
            except Exception as ce:
                compliance_errors += 1
                logger.warning("[process_document] Compliance warning: %s", ce)

        # 7. Persiste no banco usando company_id do documento
        company_id = str(doc.company_id)
        _persist_entries(db, company_id, entries)

        # 8. Marca status final
        final_status = "needs_review" if (compliance_errors > 0 or ai_confidence < 0.6) else "processed"
        doc.status = final_status
        doc.parsed = True
        doc.ai_confidence = ai_confidence
        db.commit()

        # 9. Enfileira tarefas downstream
        current_year = date.today().year
        generate_report.delay(company_id, current_year, "dre")
        generate_report.delay(company_id, current_year, "balanco")

        logger.info(
            "[process_document] Concluído doc_id=%s entries=%d compliance_errors=%d status=%s",
            doc_id, len(entries), compliance_errors, final_status,
        )
        return {
            "doc_id": doc_id,
            "status": final_status,
            "entries": len(entries),
            "compliance_errors": compliance_errors,
            "ai_confidence": ai_confidence,
        }

    except Exception as exc:
        db.rollback()
        logger.error("[process_document] Falha doc_id=%s: %s", doc_id, exc, exc_info=True)
        # Marca como failed se esgotou retries
        if self.request.retries >= self.max_retries - 1:
            try:
                doc_fail = db.query(__import__('packages.db.models', fromlist=['Document']).Document).filter_by(id=uuid.UUID(doc_id)).first()
                if doc_fail:
                    doc_fail.status = "failed"
                    doc_fail.error_message = str(exc)[:1000]
                    db.commit()
            except Exception:
                pass
        raise self.retry(exc=exc)

    finally:
        db.close()
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@celery.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_report(self, company_id: str, year: int, report_type: str) -> dict:
    """
    Gera relatório (DRE ou Balanço) de forma assíncrona e persiste na tabela reports.
    """
    import asyncio
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    logger.info("[generate_report] type=%s company=%s year=%s", report_type, company_id, year)

    async_url = SYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

    async def _run():
        try:
            from services.accounting_core.engine import AccountingEngine  # type: ignore
        except ModuleNotFoundError:
            from accounting_core.engine import AccountingEngine  # type: ignore

        engine_db = create_async_engine(async_url, pool_pre_ping=True)
        factory = async_sessionmaker(engine_db, expire_on_commit=False, class_=AsyncSession)
        async with factory() as session:
            accounting = AccountingEngine(session)
            if report_type == "dre":
                return await accounting.generate_dre(company_id, year)
            return await accounting.generate_balance_sheet(company_id, year)

    try:
        data = asyncio.run(_run())
    except Exception as exc:
        logger.error("[generate_report] Falha: %s", exc)
        raise self.retry(exc=exc)

    logger.info("[generate_report] Concluído type=%s", report_type)
    return {"company_id": company_id, "year": year, "type": report_type, "status": "completed", "data": data}


@celery.task(bind=True, max_retries=2)
def run_forecast_task(self, company_id: str, lancamentos: list) -> dict:
    """Executa Agent Predictor para uma empresa."""
    try:
        from services.ai_engine.agent_predictor import predict_cashflow  # type: ignore
    except ModuleNotFoundError:
        from ai_engine.agent_predictor import predict_cashflow  # type: ignore

    logger.info("[run_forecast_task] company=%s lancamentos=%d", company_id, len(lancamentos))
    try:
        result = predict_cashflow(lancamentos, company_name=company_id)
        return {"company_id": company_id, "status": "completed", "forecast": result}
    except Exception as exc:
        logger.error("[run_forecast_task] Falha: %s", exc)
        raise self.retry(exc=exc)


@celery.task(bind=True, max_retries=2)
def run_audit_task(self, company_id: str, lancamentos: list) -> dict:
    """Executa Agent Auditor para uma empresa."""
    try:
        from services.ai_engine.agent_auditor import audit_entries  # type: ignore
    except ModuleNotFoundError:
        from ai_engine.agent_auditor import audit_entries  # type: ignore

    logger.info("[run_audit_task] company=%s lancamentos=%d", company_id, len(lancamentos))
    try:
        result = audit_entries(lancamentos, company_name=company_id)
        return {"company_id": company_id, "status": "completed", "audit": result}
    except Exception as exc:
        logger.error("[run_audit_task] Falha: %s", exc)
        raise self.retry(exc=exc)


# ═══════════════════════════════════════════════════════════════════════════════
# TAREFAS AGENDADAS (BEAT)
# ═══════════════════════════════════════════════════════════════════════════════

@celery.task
def generate_daily_reports(report_type: str = "dre") -> dict:
    """Job diário: gera relatórios para todas as empresas do ano corrente."""
    try:
        from packages.db.models import Company  # type: ignore
    except ModuleNotFoundError:
        from db.models import Company  # type: ignore

    db = _get_db_session()
    year = date.today().year
    count = 0
    try:
        companies = db.query(Company).all()
        for company in companies:
            generate_report.delay(str(company.id), year, report_type)
            count += 1
        logger.info("[generate_daily_reports] Enfileiradas %d empresas tipo=%s", count, report_type)
    finally:
        db.close()
    return {"queued": count, "year": year, "type": report_type}


@celery.task
def run_forecast_all_companies() -> dict:
    """Job diário: atualiza forecast para todas as empresas."""
    try:
        from packages.db.models import Company, JournalEntry, JournalItem  # type: ignore
    except ModuleNotFoundError:
        from db.models import Company, JournalEntry, JournalItem  # type: ignore

    db = _get_db_session()
    count = 0
    try:
        companies = db.query(Company).all()
        for company in companies:
            # Busca lançamentos dos últimos 12 meses
            from datetime import datetime
            from sqlalchemy import text
            cutoff = date.today() - timedelta(days=365)
            entries = (
                db.query(JournalEntry)
                .filter(
                    JournalEntry.company_id == company.id,
                    JournalEntry.date >= cutoff,
                )
                .all()
            )
            lancamentos = [
                {"data": str(e.date), "descricao": e.description or "", "valor": 0}
                for e in entries
            ]
            if lancamentos:
                run_forecast_task.delay(str(company.id), lancamentos)
                count += 1
    finally:
        db.close()
    logger.info("[run_forecast_all_companies] Enfileiradas %d empresas", count)
    return {"queued": count}


@celery.task
def run_audit_all_companies() -> dict:
    """Job semanal: executa auditoria para todas as empresas."""
    try:
        from packages.db.models import Company, JournalEntry  # type: ignore
    except ModuleNotFoundError:
        from db.models import Company, JournalEntry  # type: ignore

    db = _get_db_session()
    count = 0
    try:
        companies = db.query(Company).all()
        for company in companies:
            cutoff = date.today() - timedelta(days=90)
            entries = (
                db.query(JournalEntry)
                .filter(
                    JournalEntry.company_id == company.id,
                    JournalEntry.date >= cutoff,
                )
                .all()
            )
            lancamentos = [
                {"data": str(e.date), "descricao": e.description or "", "valor": 0}
                for e in entries
            ]
            if lancamentos:
                run_audit_task.delay(str(company.id), lancamentos)
                count += 1
    finally:
        db.close()
    logger.info("[run_audit_all_companies] Enfileiradas %d empresas", count)
    return {"queued": count}


@celery.task
def cleanup_temp_files() -> dict:
    """Job horário: remove arquivos temporários órfãos."""
    import glob
    import time

    tmp_dir = tempfile.gettempdir()
    patterns = ["*.pdf", "*.xlsx", "*.txt", "*.tmp"]
    removed = 0
    now = time.time()

    for pattern in patterns:
        for filepath in glob.glob(os.path.join(tmp_dir, pattern)):
            try:
                if now - os.path.getmtime(filepath) > 3600:  # > 1 hora
                    os.unlink(filepath)
                    removed += 1
            except OSError:
                pass

    logger.info("[cleanup_temp_files] Removidos %d arquivos temporários", removed)
    return {"removed": removed}
