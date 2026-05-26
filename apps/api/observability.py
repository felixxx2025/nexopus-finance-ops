"""
Observabilidade — OpenTelemetry, Prometheus e Sentry para o Nexopus Finance Ops.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


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


def setup_prometheus(app) -> None:
    """Adiciona endpoint /metrics com métricas Prometheus ao app FastAPI."""
    try:
        from prometheus_fastapi_instrumentator import Instrumentator

        Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health", "/ready", "/metrics"],
            env_var_name="PROMETHEUS_ENABLED",
        ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

        logger.info("Prometheus /metrics exposto.")
    except ImportError:
        logger.warning("prometheus-fastapi-instrumentator não instalado — /metrics desativado.")
