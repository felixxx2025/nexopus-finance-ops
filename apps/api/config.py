"""
Nexopus Finance Ops — Configuração centralizada via pydantic-settings.
Todas as variáveis de ambiente são validadas no boot da aplicação.
"""
from __future__ import annotations

import secrets
from typing import List, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Core ──────────────────────────────────────────────────────────────
    secret_key: str = Field(..., min_length=32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    environment: str = "development"  # development | production | testing
    docs_enabled: bool = Field(default=False)
    cookie_secure: bool = Field(default=False)
    log_level: str = "INFO"
    infra_secret: str = Field(default="change-me-infra-secret")

    # ── Admin ─────────────────────────────────────────────────────────────
    admin_username: str = Field(...)
    admin_password_hash: Optional[str] = None
    admin_password: Optional[str] = None  # apenas para geração de hash em dev

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = Field(default="postgresql+asyncpg://ledger:ledger_dev_pass@db:5432/ledger_ai")
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_url: str = Field(default="redis://redis:6379/0")

    # ── RabbitMQ / Celery ─────────────────────────────────────────────────
    broker_url: str = Field(default="amqp://nexopus:rabbit_dev_pass@rabbitmq:5672//")

    # ── S3 / MinIO ────────────────────────────────────────────────────────
    s3_endpoint: str = Field(default="http://minio:9000")
    s3_access_key: str = ""
    s3_secret_key: str = ""
    s3_bucket: str = "ledger-docs"

    # ── CORS ──────────────────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://localhost:8000"

    # ── Sentry ────────────────────────────────────────────────────────────
    sentry_dsn: Optional[str] = None

    # ── GitHub AI ─────────────────────────────────────────────────────────
    github_token: Optional[str] = None
    github_ai_timeout: int = 60
    github_ai_max_retries: int = 3

    # ── RBAC ──────────────────────────────────────────────────────────────
    # JSON list of additional users: [{"username":"u","role":"analista","password_hash":"$2b$..."}]
    extra_users_json: Optional[str] = None

    # ── Observabilidade ───────────────────────────────────────────────────
    otlp_endpoint: Optional[str] = None  # ex: http://otel-collector:4317
    prometheus_enabled: bool = True

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY deve ter no mínimo 32 caracteres.")
        return v

    @model_validator(mode="after")
    def validate_admin_password(self) -> "Settings":
        if not self.admin_password_hash and not self.admin_password:
            raise ValueError(
                "ADMIN_PASSWORD ou ADMIN_PASSWORD_HASH deve ser definido."
            )
        return self

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_secure_value(self) -> bool:
        """Return cookie_secure based on environment."""
        return self.cookie_secure if self.is_production else False

    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("postgresql+asyncpg://", "postgresql://")


# Singleton carregado uma vez
settings = Settings()  # type: ignore[call-arg]
