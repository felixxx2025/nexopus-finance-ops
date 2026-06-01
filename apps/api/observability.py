"""
Observabilidade — logs estruturados, OpenTelemetry, Prometheus e Sentry.

Uso no startup:
    from apps.api.observability import setup_all
    setup_all(app, settings)
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)


class _JsonFormatter(logging.Formatter):
    """Formata logs como JSON para ingestão no Loki/Grafana."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "func": record.funcName,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        # Campos extras (structlog-style)
        for key in ("doc_id", "company_id", "username", "action", "request_id"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        return json.dumps(payload, ensure_ascii=False)


def setup_structured_logging(json_logs: bool = False, level: str = "INFO") -> None:
    """
    Configura logging global.
    - json_logs=True  → JSON por linha (para Loki/Promtail)
    - json_logs=False → formato legível para desenvolvimento
    """
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler()
    if json_logs:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s — %(message)s")
        )
    root.addHandler(handler)


def setup_sentry(dsn: Optional[str], environment: str = "development") -> None:
    """Configura Sentry SDK para captura de erros em produção."""
    if not dsn:
        logger.info("Sentry DSN não configurado — monitoramento de erros desativado.")
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.celery import CeleryIntegration
        from sentry_sdk.integrations.redis import RedisIntegration

        sentry_sdk.init(
            dsn=dsn,
            environment=environment,
            integrations=[
                FastApiIntegration(transaction_style="endpoint"),
                SqlalchemyIntegration(),
                CeleryIntegration(),
                RedisIntegration(),
            ],
            traces_sample_rate=0.2 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 0.0,
            send_default_pii=False,
        )
        logger.info("Sentry configurado para environment='%s'", environment)
    except ImportError:
        logger.warning("sentry-sdk não instalado — ignorando configuração do Sentry.")


def setup_otlp(endpoint: Optional[str], service_name: str = "nexopus-finance-api") -> None:
    """Configura OpenTelemetry com exportação OTLP (Jaeger/Grafana Tempo)."""
    if not endpoint:
        logger.info("OTLP endpoint não configurado — tracing distribuído desativado.")
        return
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        FastAPIInstrumentor().instrument()
        SQLAlchemyInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry configurado → endpoint=%s", endpoint)
    except ImportError as e:
        logger.warning("Dependências OTel não encontradas (%s) — tracing desativado.", e)


def setup_prometheus(app, environment: str = "development") -> None:
    """Adiciona endpoint /metrics com métricas Prometheus ao app FastAPI."""
    if getattr(app.state, "prometheus_configured", False):
        logger.info("Prometheus já configurado para este app — ignorando nova inicialização.")
        return
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_instrument_requests_inprogress=False,
            excluded_handlers=["/health", "/ready", "/metrics"],
        )
        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics", include_in_schema=False)
        app.state.prometheus_configured = True

        logger.info("Prometheus /metrics exposto.")
    except Exception as e:
        logger.warning("Erro ao configurar Prometheus /metrics: %s", e)


def setup_all(app, settings) -> None:
    """
    Ponto único de inicialização de observabilidade.
    Chamado no startup do FastAPI.
    """
    json_logs = getattr(settings, "environment", "development") == "production"
    setup_structured_logging(
        json_logs=json_logs,
        level=getattr(settings, "log_level", "INFO"),
    )
    setup_sentry(
        dsn=getattr(settings, "sentry_dsn", None),
        environment=getattr(settings, "environment", "development"),
    )
    setup_otlp(
        endpoint=getattr(settings, "otlp_endpoint", None),
    )
    setup_prometheus(app, environment=getattr(settings, "environment", "development"))
    logger.info("Observabilidade inicializada (json_logs=%s).", json_logs)
