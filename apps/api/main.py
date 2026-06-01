"""
Nexopus Finance Ops — API principal v2.1.0

Motor contábil com IA para DRE, Balanço, relatórios e auditoria financeira.
Configuração 100% via config.py (pydantic-settings).
"""
import io
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from itsdangerous import URLSafeTimedSerializer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
import contextvars

# ── Configuração centralizada ─────────────────────────────────────────────────
from apps.api.config import settings  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

_API_VERSION = "2.1.0"

# ── Correlation ID Context Variable ─────────────────────────────────────────────
correlation_id_var = contextvars.ContextVar("correlation_id", default=None)

# ── Hashing de senha ──────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Resolve hash do admin
if settings.admin_password_hash:
    ADMIN_PASSWORD_HASH: str = settings.admin_password_hash
else:
    ADMIN_PASSWORD_HASH = pwd_context.hash(settings.admin_password)  # type: ignore[arg-type]
    logger.warning(
        "ADMIN_PASSWORD em texto puro detectado. "
        "Gere um hash bcrypt e defina ADMIN_PASSWORD_HASH no .env para produção."
    )

# ── Redis (rate limiting + token blacklist) ────────────────────────────────────
import redis as redis_lib  # noqa: E402

try:
    _redis: Optional[redis_lib.Redis] = redis_lib.from_url(settings.redis_url, decode_responses=True)
    _redis.ping()
    logger.info("Redis conectado: %s", settings.redis_url)
except Exception as _redis_err:
    logger.warning("Redis não disponível (%s) — rate limiting e blacklist desativados.", _redis_err)
    _redis = None

# ── CSRF Protection ────────────────────────────────────────────────────────────
_csrf_serializer = URLSafeTimedSerializer(settings.secret_key, salt="csrf-salt")

# ── Rate Limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url if _redis else "memory://",
)

# ── Banco de Dados ────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Auto-seed knowledge base se vazia (apenas em development)
    if settings.environment == "development":
        try:
            from sqlalchemy import select  # noqa: PLC0415
            from packages.db.models import KnowledgeArticle  # noqa: PLC0415

            async with AsyncSessionLocal() as db:
                result = await db.execute(select(KnowledgeArticle).limit(1))
                has_knowledge = result.scalar_one_or_none()

                if not has_knowledge:
                    logger.info("Base de conhecimento vazia, executando auto-seed (Sentence Transformers local)...")
                    from services.knowledge.knowledge_seeder import seed_knowledge_base  # noqa: PLC0415
                    from services.knowledge.template_service import seed_templates  # noqa: PLC0415

                    kb_stats = await seed_knowledge_base(db)
                    template_stats = await seed_templates(db)
                    logger.info("Auto-seed concluído: KB=%s, Templates=%s", kb_stats, template_stats)
        except Exception as e:
            logger.warning("Auto-seed falhou: %s", e)

    logger.info("Nexopus Finance API v%s iniciada (env=%s).", _API_VERSION, settings.environment)

    yield

    # Shutdown
    logger.info("Nexopus Finance API v%s encerrando.", _API_VERSION)


# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Nexopus Finance Ops — API",
    description="Motor contábil com IA para DRE, Balanço, relatórios e auditoria financeira.",
    version=_API_VERSION,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
)

# Setup observability before adding middleware
from apps.api.observability import setup_all  # noqa: PLC0415
setup_all(app, settings)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With", "X-CSRF-Token"],
)


@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Gera e propaga correlation ID para tracing distribuído."""
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    correlation_id_var.set(correlation_id)
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response


@app.middleware("http")
async def add_hsts_header(request: Request, call_next):
    """Adiciona header HSTS em produção."""
    response = await call_next(request)
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# ── Auditoria helper ──────────────────────────────────────────────────────────

async def _audit(
    db: AsyncSession,
    action: str,
    username: str,
    *,
    entity_type: str | None = None,
    entity_id: str | None = None,
    company_id: str | None = None,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> None:
    """Persiste um evento de auditoria na tabela audit_logs."""
    try:
        from packages.db.models import AuditLog  # noqa: PLC0415
        log = AuditLog(
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=uuid.UUID(entity_id) if entity_id else None,
            company_id=uuid.UUID(company_id) if company_id else None,
            metadata_=metadata or {},
            ip_address=ip_address,
        )
        db.add(log)
        await db.commit()
    except Exception as exc:
        logger.warning("Falha ao gravar audit_log action=%s: %s", action, exc)


# ── RBAC helpers ──────────────────────────────────────────────────────────────

def _load_user_db():
    from apps.api.rbac import UserDB  # noqa: PLC0415
    return UserDB(
        admin_username=settings.admin_username,
        admin_password_hash=ADMIN_PASSWORD_HASH,
        extra_json=settings.extra_users_json,
    )


_user_db = _load_user_db()
_VALID_ROLES = {"admin", "analista", "viewer"}


# ── Auth helpers ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class DocumentCreate(BaseModel):
    company_id: str
    file_url: str
    original_filename: Optional[str] = None
    type: str  # pdf, excel, sped
    status: str = "uploaded"


class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    error_message: Optional[str] = None
    ai_confidence: Optional[float] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    username: str
    role: str


def _create_access_token(sub: str, role: str = "viewer") -> tuple[str, str]:
    """Cria JWT com jti e role, retorna (token, jti)."""
    jti = str(uuid.uuid4())
    from datetime import timedelta
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    token = jwt.encode(
        {"sub": sub, "exp": expire, "jti": jti, "role": role},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token, jti


def _create_refresh_token(sub: str) -> str:
    """Cria refresh token com expiração longer."""
    from datetime import timedelta
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    token = jwt.encode(
        {"sub": sub, "exp": expire, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.algorithm,
    )
    return token


async def get_current_user(request: Request) -> dict:
    """
    Extrai e valida JWT de:
    1. Cookie httpOnly 'nexopus_token'
    2. Authorization Bearer header
    Retorna dict com sub, jti e role.
    """
    token: str | None = None

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]

    if not token:
        token = request.cookies.get("nexopus_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autenticação necessária",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        sub: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        role: str = payload.get("role", "viewer")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    except JWTError as exc:
        logger.warning("Falha de autenticação JWT: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Verifica blacklist Redis
    if jti and _redis:
        try:
            if _redis.get(f"bl:{jti}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token revogado. Faça login novamente.",
                )
        except HTTPException:
            raise
        except Exception as _bl_err:
            logger.warning("Erro ao verificar blacklist Redis: %s", _bl_err)

    return {"sub": sub, "jti": jti, "role": role}


def require_role(allowed_roles: list[str]):
    """Dependência que exige um dos roles informados."""
    async def _check(current_user: dict = Depends(get_current_user)):
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(status_code=403, detail="Permissão insuficiente.")
        return current_user
    return _check


# ── Auth endpoints ────────────────────────────────────────────────────────────

@app.post("/auth/token", tags=["auth"])
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """Autentica usuário, retorna JWT no body e define httpOnly cookie."""
    # Check if user is locked out
    if _redis:
        lockout_key = f"lockout:{body.username}"
        lockout = _redis.get(lockout_key)
        if lockout:
            logger.warning("Conta '%s' está bloqueada por tentativas falhas", body.username)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Conta bloqueada. Tente novamente em 15 minutos."
            )
    
    user = _user_db.authenticate(body.username, body.password)
    if not user:
        logger.warning("Tentativa de login inválida para '%s'", body.username)
        
        # Increment failed attempts
        if _redis:
            attempts_key = f"failed_attempts:{body.username}"
            attempts = _redis.incr(attempts_key)
            _redis.expire(attempts_key, 300)  # 5 minutos
            
            # Lockout after 5 attempts
            if attempts >= 5:
                lockout_key = f"lockout:{body.username}"
                _redis.setex(lockout_key, 900, "1")  # 15 minutos lockout
                logger.warning("Conta '%s' bloqueada após %d tentativas falhas", body.username, attempts)
        
        await _audit(
            db, "login_failed", body.username,
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")
    
    # Reset failed attempts on success
    if _redis:
        attempts_key = f"failed_attempts:{body.username}"
        _redis.delete(attempts_key)

    role = user.get("role", "viewer")
    if hasattr(role, "value"):
        role = role.value

    token, _jti = _create_access_token(sub=body.username, role=role)
    refresh_token = _create_refresh_token(sub=body.username)
    logger.info("Login bem-sucedido para '%s' (role=%s)", body.username, role)

    await _audit(
        db, "login", body.username,
        ip_address=request.client.host if request.client else None,
    )

    response = JSONResponse(
        content={"access_token": token, "refresh_token": refresh_token, "token_type": "bearer", "username": body.username, "role": role}
    )
    response.set_cookie(
        key="nexopus_token",
        value=token,
        httponly=True,
        samesite="lax",
        secure=settings.cookie_secure,
        max_age=settings.access_token_expire_minutes * 60,
        path="/",
    )
    return response


@app.post("/auth/refresh", tags=["auth"])
async def refresh_token(request: Request) -> JSONResponse:
    """Renova access token usando refresh token."""
    refresh_token_str = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not refresh_token_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token não fornecido")
    
    try:
        payload = jwt.decode(refresh_token_str, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
        
        username = payload.get("sub")
        user = _user_db.get_user(username)
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
        
        role = user.get("role", "viewer")
        if hasattr(role, "value"):
            role = role.value
        
        access_token, _jti = _create_access_token(sub=username, role=role)
        return JSONResponse(
            content={"access_token": access_token, "token_type": "bearer", "username": username, "role": role}
        )
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")


@app.post("/auth/logout", tags=["auth"])
async def logout(
    request: Request,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """Invalida o token atual via blacklist Redis e limpa o cookie."""
    jti = current_user.get("jti")
    if jti and _redis:
        try:
            _redis.setex(f"bl:{jti}", settings.access_token_expire_minutes * 60, "1")
        except Exception as _e:
            logger.warning("Não foi possível revogar token na blacklist: %s", _e)

    await _audit(
        db, "logout", current_user["sub"],
        ip_address=request.client.host if request.client else None,
    )

    response = JSONResponse(content={"status": "logged_out"})
    response.delete_cookie(key="nexopus_token", path="/")
    return response


@app.get("/auth/me", tags=["auth"])
async def me(current_user: dict = Depends(get_current_user)) -> dict:
    """Retorna o usuário autenticado atual."""
    return {"username": current_user["sub"], "role": current_user.get("role", "viewer")}


# ── Health & Ready ────────────────────────────────────────────────────────────

def require_infra_auth(request: Request) -> None:
    """Require infra secret for health/ready endpoints."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {settings.infra_secret}":
        raise HTTPException(status_code=403, detail="Forbidden")


@app.get("/health", tags=["infra"])
def health(request: Request) -> dict:
    # Skip auth in development for convenience
    if settings.environment != "production":
        return {"status": "ok", "service": "nexopus-finance-api", "version": _API_VERSION}
    require_infra_auth(request)
    return {"status": "ok", "service": "nexopus-finance-api", "version": _API_VERSION}


@app.get("/ready", tags=["infra"])
async def ready(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    """Verifica prontidão da API (DB + Redis)."""
    # Skip auth in development for convenience
    if settings.environment != "production":
        pass
    else:
        require_infra_auth(request)
    
    from sqlalchemy import text  # noqa: PLC0415
    checks: dict = {}

    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    if _redis:
        try:
            _redis.ping()
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
    else:
        checks["redis"] = "not_configured"

    all_ok = all(v == "ok" for v in checks.values())
    return {
        "status": "ready" if all_ok else "degraded",
        "checks": checks,
        "service": "nexopus-finance-api",
        "version": _API_VERSION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── S3 / MinIO helpers ────────────────────────────────────────────────────────

def _get_s3_client():
    import boto3  # noqa: PLC0415
    from botocore.config import Config as BotoConfig  # noqa: PLC0415
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        config=BotoConfig(signature_version="s3v4"),
    )


def _ensure_bucket(s3_client) -> None:
    try:
        s3_client.head_bucket(Bucket=settings.s3_bucket)
    except Exception:
        try:
            s3_client.create_bucket(Bucket=settings.s3_bucket)
            logger.info("Bucket '%s' criado.", settings.s3_bucket)
        except Exception as _e:
            logger.warning("Não foi possível criar bucket '%s': %s", settings.s3_bucket, _e)


def _upload_to_s3(key: str, contents: bytes, content_type: str) -> str:
    """Faz upload para MinIO/S3 e retorna a referência 'bucket/key'."""
    s3 = _get_s3_client()
    _ensure_bucket(s3)
    s3.upload_fileobj(
        io.BytesIO(contents),
        settings.s3_bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{settings.s3_bucket}/{key}"


# ── Companies / Onboarding ───────────────────────────────────────────────────

class CompanyCreate(BaseModel):
    name: str
    cnpj: str


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str | None = None
    role: str | None = None


def _validate_role(role: str) -> str:
    if role not in _VALID_ROLES:
        raise HTTPException(status_code=422, detail="Role inválida. Use admin, analista ou viewer.")
    return role


@app.post("/companies", tags=["companies"], status_code=201)
async def create_company(
    body: CompanyCreate,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cria uma empresa e semeia o plano de contas padrão NBC TG automaticamente.
    Apenas admin.
    """
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Company  # noqa: PLC0415
    from services.accounting_core.engine import AccountingEngine  # noqa: PLC0415
    from services.compliance.rules import validate_cnpj  # noqa: PLC0415

    cnpj_clean = body.cnpj.replace(".", "").replace("/", "").replace("-", "")
    if not validate_cnpj(cnpj_clean):
        raise HTTPException(status_code=422, detail="CNPJ inválido.")

    # Verifica duplicidade
    existing = await db.execute(select(Company).where(Company.cnpj == cnpj_clean))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.")

    company = Company(name=body.name, cnpj=cnpj_clean)
    db.add(company)
    await db.commit()
    await db.refresh(company)

    # Seed plano de contas
    engine = AccountingEngine(db)
    seeded = await engine.seed_plano_de_contas(str(company.id))

    await _audit(
        db, "company_created", current_user["sub"],
        entity_type="company", entity_id=str(company.id),
        metadata={"name": body.name, "cnpj": cnpj_clean, "contas_semeadas": seeded},
    )

    return {
        "id": str(company.id),
        "name": company.name,
        "cnpj": company.cnpj,
        "contas_semeadas": seeded,
    }


@app.patch("/companies/{company_id}", tags=["companies"])
async def update_company(
    company_id: uuid.UUID,
    body: CompanyCreate,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Atualiza dados de uma empresa. Apenas admin."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Company  # noqa: PLC0415
    from services.compliance.rules import validate_cnpj  # noqa: PLC0415

    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    cnpj_clean = body.cnpj.replace(".", "").replace("/", "").replace("-", "")
    if not validate_cnpj(cnpj_clean):
        raise HTTPException(status_code=422, detail="CNPJ inválido.")

    # Verifica duplicidade (exceto a própria empresa)
    existing = await db.execute(
        select(Company).where(Company.cnpj == cnpj_clean, Company.id != company_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="CNPJ já cadastrado.")

    company.name = body.name
    company.cnpj = cnpj_clean
    await db.commit()
    await db.refresh(company)

    await _audit(
        db, "company_updated", current_user["sub"],
        entity_type="company", entity_id=str(company.id),
        metadata={"name": body.name, "cnpj": cnpj_clean},
    )

    return {
        "id": str(company.id),
        "name": company.name,
        "cnpj": company.cnpj,
    }


@app.delete("/companies/{company_id}", tags=["companies"])
async def delete_company(
    company_id: uuid.UUID,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exclui uma empresa. Apenas admin."""
    from sqlalchemy import select, delete  # noqa: PLC0415
    from packages.db.models import Company  # noqa: PLC0415

    stmt = select(Company).where(Company.id == company_id)
    result = await db.execute(stmt)
    company = result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    await db.execute(delete(Company).where(Company.id == company_id))
    await db.commit()

    await _audit(
        db, "company_deleted", current_user["sub"],
        entity_type="company", entity_id=str(company_id),
        metadata={"name": company.name, "cnpj": company.cnpj},
    )

    return {"message": "Empresa excluída com sucesso"}


@app.get("/companies", tags=["companies"])
async def list_companies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista todas as empresas."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Company  # noqa: PLC0415

    result = await db.execute(select(Company).order_by(Company.name).limit(1000))
    companies = result.scalars().all()
    return {
        "companies": [
            {"id": str(c.id), "name": c.name, "cnpj": c.cnpj, "created_at": c.created_at.isoformat()}
            for c in companies
        ]
    }


@app.post("/companies/{company_id}/seed-accounts", tags=["companies"])
async def seed_accounts(
    company_id: uuid.UUID,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Semeia plano de contas padrão se a empresa não tiver contas."""
    from services.accounting_core.engine import AccountingEngine  # noqa: PLC0415
    engine = AccountingEngine(db)
    seeded = await engine.seed_plano_de_contas(str(company_id))
    return {"company_id": str(company_id), "contas_semeadas": seeded}


# ── Documents ─────────────────────────────────────────────────────────────────

MAX_UPLOAD_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}
_MIME_TO_EXT = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "text/plain": ".txt",
}
_EXT_TO_TYPE = {".pdf": "pdf", ".xlsx": "excel", ".txt": "sped"}

# Assinaturas mágicas para validação real de conteúdo
_MAGIC_SIGNATURES = {
    "application/pdf": b"%PDF",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": b"PK\x03\x04",
}


def _validate_file_magic(content_type: str, contents: bytes) -> bool:
    """Valida que o conteúdo real bate com o MIME declarado."""
    sig = _MAGIC_SIGNATURES.get(content_type)
    if sig is None:
        return True  # texto puro (txt/sped) — sem assinatura
    return contents[:len(sig)] == sig


@app.post("/documents/upload", tags=["documents"])
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    company_id: uuid.UUID = None,  # type: ignore[assignment]
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Recebe PDF/Excel/SPED, valida conteúdo, persiste no storage (MinIO),
    cria registro na tabela documents com status 'uploaded' e enfileira parsing.

    Query param obrigatório: ?company_id=<uuid>
    """
    # Exige company_id
    company_id_str = request.query_params.get("company_id")
    if not company_id_str:
        raise HTTPException(status_code=400, detail="company_id é obrigatório.")
    try:
        company_uuid = uuid.UUID(company_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="company_id inválido — deve ser UUID v4.")

    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo não suportado: {file.content_type}",
        )

    # Leitura em chunks com limite de tamanho
    _CHUNK = 1024 * 1024
    buf = bytearray()
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Arquivo excede o limite de 50 MB.",
            )
    contents = bytes(buf)

    # Validação de conteúdo real (magic bytes)
    if not _validate_file_magic(file.content_type, contents):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Conteúdo do arquivo não corresponde ao tipo declarado.",
        )

    doc_id = str(uuid.uuid4())
    ext = _MIME_TO_EXT.get(file.content_type, ".bin")
    s3_key = f"{doc_id}{ext}"

    # 1. Upload para storage
    try:
        file_url = _upload_to_s3(s3_key, contents, file.content_type)
    except Exception as exc:
        logger.error("Falha ao fazer upload para storage: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage indisponível. Tente novamente.",
        ) from exc

    # 2. Registra no banco com status 'uploaded'
    try:
        from packages.db.models import Document  # noqa: PLC0415
        doc = Document(
            id=uuid.UUID(doc_id),
            company_id=company_uuid,
            file_url=file_url,
            original_filename=file.filename,
            type=_EXT_TO_TYPE.get(ext, "pdf"),
            status="uploaded",
            parsed=False,
        )
        db.add(doc)
        await db.commit()
    except Exception as exc:
        logger.error("Falha ao registrar documento no DB: %s", exc)
        await db.rollback()
        raise HTTPException(status_code=500, detail="Falha ao registrar documento.") from exc

    # 3. Auditoria
    await _audit(
        db, "document_upload", current_user["sub"],
        entity_type="document", entity_id=doc_id,
        company_id=company_id_str,
        metadata={"filename": file.filename, "size_bytes": len(contents), "type": ext},
        ip_address=request.client.host if request.client else None,
    )

    # 4. Enfileira processamento assíncrono
    try:
        from services.worker.tasks import process_document  # noqa: PLC0415
        process_document.delay(doc_id)
    except Exception as exc:
        logger.warning("Não foi possível enfileirar doc %s: %s", doc_id, exc)

    logger.info(
        "Documento recebido | doc_id=%s | filename=%s | size=%d bytes | user=%s",
        doc_id, file.filename, len(contents), current_user["sub"],
    )
    return {"status": "processing", "doc_id": doc_id, "filename": file.filename}


@app.get("/documents", tags=["documents"])
async def list_documents(
    company_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista documentos de uma empresa."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Document  # noqa: PLC0415

    stmt = select(Document).where(Document.company_id == company_id).order_by(Document.created_at.desc()).limit(100)
    result = await db.execute(stmt)
    docs = result.scalars().all()
    return {
        "documents": [
            {
                "id": str(d.id),
                "filename": d.original_filename,
                "type": d.type,
                "status": d.status,
                "parsed": d.parsed,
                "error_message": d.error_message,
                "ai_confidence": float(d.ai_confidence) if d.ai_confidence else None,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]
    }


@app.get("/documents/{document_id}", tags=["documents"])
async def get_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recupera detalhes de um documento específico."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Document  # noqa: PLC0415

    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(document_id))
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    return {
        "id": str(doc.id),
        "company_id": str(doc.company_id),
        "file_url": doc.file_url,
        "filename": doc.original_filename,
        "type": doc.type,
        "status": doc.status,
        "parsed": doc.parsed,
        "error_message": doc.error_message,
        "ai_confidence": float(doc.ai_confidence) if doc.ai_confidence else None,
        "created_at": doc.created_at.isoformat(),
        "updated_at": doc.updated_at.isoformat(),
    }


@app.post("/documents", tags=["documents"])
async def create_document(
    body: DocumentCreate,
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cria registro de documento manualmente (sem upload de arquivo)."""
    from packages.db.models import Document  # noqa: PLC0415

    doc = Document(
        company_id=uuid.UUID(body.company_id),
        file_url=body.file_url,
        original_filename=body.original_filename,
        type=body.type,
        status=body.status,
        parsed=False,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    await _audit(
        db, "document_created", current_user["sub"],
        entity_type="document", entity_id=doc.id,
        company_id=body.company_id,
        metadata={"filename": body.original_filename, "type": body.type},
    )

    return {"id": str(doc.id), "message": "Documento criado com sucesso"}


@app.put("/documents/{document_id}", tags=["documents"])
async def update_document(
    document_id: str,
    body: DocumentUpdate,
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Atualiza status e metadados de um documento."""
    from packages.db.models import Document  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(document_id))
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    if body.status is not None:
        doc.status = body.status
    if body.error_message is not None:
        doc.error_message = body.error_message
    if body.ai_confidence is not None:
        doc.ai_confidence = body.ai_confidence

    doc.updated_at = datetime.now(timezone.utc)
    await db.commit()

    await _audit(
        db, "document_updated", current_user["sub"],
        entity_type="document", entity_id=doc.id,
        metadata={"status": doc.status},
    )

    return {"id": str(doc.id), "message": "Documento atualizado com sucesso"}


@app.delete("/documents/{document_id}", tags=["documents"])
async def delete_document(
    document_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exclui documento (apenas admin)."""
    from packages.db.models import Document  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    result = await db.execute(
        select(Document).where(Document.id == uuid.UUID(document_id))
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Documento não encontrado")

    await db.delete(doc)
    await db.commit()

    await _audit(
        db, "document_deleted", current_user["sub"],
        entity_type="document", entity_id=doc.id,
        metadata={"filename": doc.original_filename},
    )

    return {"message": "Documento excluído com sucesso"}


# ── Journal entries: revisão humana ──────────────────────────────────────────

class ReviewRequest(BaseModel):
    action: str  # "approve" | "reject"
    note: Optional[str] = None


@app.patch("/entries/{entry_id}/review", tags=["entries"])
async def review_entry(
    entry_id: uuid.UUID,
    body: ReviewRequest,
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Aprova ou rejeita um lançamento gerado por IA."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import JournalEntry  # noqa: PLC0415

    stmt = select(JournalEntry).where(JournalEntry.id == entry_id)
    result = await db.execute(stmt)
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Lançamento não encontrado.")

    if body.action == "approve":
        entry.status = "approved"
    elif body.action == "reject":
        entry.status = "rejected"
    else:
        raise HTTPException(status_code=400, detail="action deve ser 'approve' ou 'reject'.")

    entry.review_note = body.note
    entry.reviewed_by = current_user["sub"]
    entry.reviewed_at = datetime.now(timezone.utc)
    await db.commit()

    await _audit(
        db, f"entry_{body.action}", current_user["sub"],
        entity_type="journal_entry", entity_id=str(entry_id),
        metadata={"note": body.note},
    )

    return {"entry_id": str(entry_id), "status": entry.status, "reviewed_by": entry.reviewed_by}


@app.get("/entries/pending", tags=["entries"])
async def list_pending_entries(
    company_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista lançamentos gerados por IA que aguardam revisão humana."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import JournalEntry  # noqa: PLC0415

    stmt = (
        select(JournalEntry)
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == "draft")
        .where(JournalEntry.ai_generated.is_(True))
        .order_by(JournalEntry.created_at.desc())
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()
    return {
        "entries": [
            {
                "id": str(e.id),
                "date": e.date.isoformat(),
                "description": e.description,
                "status": e.status,
                "ai_confidence": float(e.ai_confidence) if e.ai_confidence else None,
                "created_at": e.created_at.isoformat(),
            }
            for e in entries
        ]
    }


@app.get("/entries/approved", tags=["entries"])
async def list_approved_entries(
    company_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista lançamentos aprovados para uso em auditoria e forecast."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import JournalEntry, JournalItem  # noqa: PLC0415

    stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.items))
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == "approved")
        .order_by(JournalEntry.date.desc())
        .limit(500)
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    entries_data = []
    for e in entries:
        items = e.items

        entries_data.append({
            "id": str(e.id),
            "date": e.date.isoformat(),
            "description": e.description,
            "status": e.status,
            "items": [
                {
                    "account": i.account,
                    "debit": float(i.debit) if i.debit else 0,
                    "credit": float(i.credit) if i.credit else 0,
                }
                for i in items
            ],
            "created_at": e.created_at.isoformat(),
        })

    return {"entries": entries_data}


@app.get("/compliance", tags=["compliance"])
async def get_compliance_status(
    company_id: uuid.UUID,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Retorna status de compliance da empresa com base em lançamentos aprovados."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import JournalEntry, JournalItem, Company  # noqa: PLC0415
    from services.compliance.rules import validate_cnpj  # noqa: PLC0415

    # Buscar empresa
    company_stmt = select(Company).where(Company.id == company_id)
    company_result = await db.execute(company_stmt)
    company = company_result.scalar_one_or_none()

    if not company:
        raise HTTPException(status_code=404, detail="Empresa não encontrada")

    # Validar CNPJ
    cnpj_valid = validate_cnpj(company.cnpj) if company.cnpj else False

    # Buscar lançamentos aprovados
    from sqlalchemy.orm import selectinload  # noqa: PLC0415

    entries_stmt = (
        select(JournalEntry)
        .options(selectinload(JournalEntry.items))
        .where(JournalEntry.company_id == company_id)
        .where(JournalEntry.status == "approved")
    )
    entries_result = await db.execute(entries_stmt)
    entries = entries_result.scalars().all()

    # Validar partida dobrada em cada lançamento
    double_entry_valid = True
    double_entry_errors = []

    for entry in entries:
        items = entry.items

        total_debit = sum(float(i.debit) if i.debit else 0 for i in items)
        total_credit = sum(float(i.credit) if i.credit else 0 for i in items)

        if abs(total_debit - total_credit) > 0.01:
            double_entry_valid = False
            double_entry_errors.append({
                "entry_id": str(entry.id),
                "date": entry.date.isoformat(),
                "description": entry.description,
                "debit": total_debit,
                "credit": total_credit,
            })

    # Validar equação patrimonial (usando relatórios)
    from datetime import datetime  # noqa: PLC0415
    current_year = datetime.now().year

    try:
        dre_stmt = select(Report).where(
            Report.company_id == company_id,
            Report.year == current_year,
            Report.type == "dre"
        )
        dre_result = await db.execute(dre_stmt)
        dre = dre_result.scalar_one_or_none()

        balance_stmt = select(Report).where(
            Report.company_id == company_id,
            Report.year == current_year,
            Report.type == "balanco"
        )
        balance_result = await db.execute(balance_stmt)
        balance = balance_result.scalar_one_or_none()

        equation_valid = True
        equation_errors = []

        if balance and balance.data:
            ativo = balance.data.get("ativo", 0)
            passivo = balance.data.get("passivo", 0)
            pl = balance.data.get("patrimonio_liquido", 0)

            if abs(ativo - (passivo + pl)) > 0.01:
                equation_valid = False
                equation_errors.append({
                    "type": "equacao_patrimonial",
                    "ativo": ativo,
                    "passivo": passivo,
                    "pl": pl,
                    "diferenca": ativo - (passivo + pl),
                })
    except Exception:
        equation_valid = None
        equation_errors = []

    # Calcular score de compliance
    compliance_items = [
        {"id": "cnpj", "name": "Validação CNPJ", "status": "compliant" if cnpj_valid else "non-compliant", "description": "CNPJ válido" if cnpj_valid else "CNPJ inválido"},
        {"id": "partida_dobrada", "name": "Partida Dobrada", "status": "compliant" if double_entry_valid else "non-compliant", "description": "Todos os lançamentos balanceados" if double_entry_valid else f"{len(double_entry_errors)} lançamentos desbalanceados"},
    ]

    if equation_valid is not None:
        compliance_items.append({
            "id": "equacao_patrimonial", "name": "Equação Patrimonial", "status": "compliant" if equation_valid else "non-compliant", "description": "Ativo = Passivo + PL" if equation_valid else "Balanço não fecha"
        })

    compliant_count = sum(1 for item in compliance_items if item["status"] == "compliant")
    total_count = len(compliance_items)
    compliance_score = int((compliant_count / total_count) * 100) if total_count > 0 else 0

    return {
        "score": compliance_score,
        "items": compliance_items,
        "errors": {
            "cnpj": [] if cnpj_valid else ["CNPJ inválido"],
            "partida_dobrada": double_entry_errors,
            "equacao_patrimonial": equation_errors if equation_valid is not None else [],
        }
    }


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/reports/dre/{company_id}/{year}", tags=["reports"])
async def get_dre(
    company_id: uuid.UUID,
    year: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gera DRE para a empresa e ano."""
    from services.accounting_core.engine import AccountingEngine  # noqa: PLC0415
    accounting = AccountingEngine(db)
    data = await accounting.generate_dre(str(company_id), year)
    await _audit(
        db, "report_dre_generated", current_user["sub"],
        entity_type="report", company_id=str(company_id),
        metadata={"year": year},
    )
    return {"company_id": str(company_id), "year": year, "type": "DRE", "data": data}


@app.get("/reports/balance/{company_id}/{year}", tags=["reports"])
async def get_balance_sheet(
    company_id: uuid.UUID,
    year: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Gera Balanço Patrimonial para a empresa e ano."""
    from services.accounting_core.engine import AccountingEngine  # noqa: PLC0415
    accounting = AccountingEngine(db)
    data = await accounting.generate_balance_sheet(str(company_id), year)
    await _audit(
        db, "report_balance_generated", current_user["sub"],
        entity_type="report", company_id=str(company_id),
        metadata={"year": year},
    )
    return {"company_id": str(company_id), "year": year, "type": "balanco", "data": data}


@app.patch("/reports/{report_id}/approve", tags=["reports"])
async def approve_report(
    report_id: uuid.UUID,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Aprova relatório, impedindo alterações futuras (status=approved)."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Report  # noqa: PLC0415

    stmt = select(Report).where(Report.id == report_id)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado.")
    if report.status == "closed":
        raise HTTPException(status_code=409, detail="Relatório já está fechado.")

    report.status = "approved"
    report.approved_by = current_user["sub"]
    report.approved_at = datetime.now(timezone.utc)
    await db.commit()

    await _audit(
        db, "report_approved", current_user["sub"],
        entity_type="report", entity_id=str(report_id),
    )
    return {"report_id": str(report_id), "status": "approved", "approved_by": current_user["sub"]}


# ── AI endpoints ──────────────────────────────────────────────────────────────

class ForecastRequest(BaseModel):
    lancamentos: list[dict]
    company_name: str = ""


@app.post("/ai/forecast", tags=["ai"])
@limiter.limit("10/minute")
async def ai_forecast(
    request: Request,
    body: ForecastRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Gera previsão de fluxo de caixa para 30/60/90 dias com 3 cenários."""
    from services.ai_engine.agent_predictor import predict_cashflow  # noqa: PLC0415
    result = await predict_cashflow(body.lancamentos, body.company_name)
    return result


class AuditRequest(BaseModel):
    lancamentos: list[dict]
    dre: Optional[dict] = None
    balanco: Optional[dict] = None
    company_name: str = ""


@app.post("/ai/audit", tags=["ai"])
@limiter.limit("5/minute")
async def ai_audit(
    request: Request,
    body: AuditRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Executa auditoria automática sobre lançamentos contábeis."""
    from services.ai_engine.agent_auditor import audit_entries  # noqa: PLC0415
    result = await audit_entries(
        body.lancamentos,
        dre=body.dre,
        balanco=body.balanco,
        company_name=body.company_name,
    )
    return result


class AssistantRequest(BaseModel):
    question: str
    context: dict = {}
    history: Optional[list[dict]] = None


@app.post("/ai/assistant", tags=["ai"])
@limiter.limit("20/minute")
async def ai_assistant(
    request: Request,
    body: AssistantRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """Assistente financeiro conversacional com streaming SSE e RAG (100% local)."""
    from services.ai_engine.agent_assistant_local import stream_answer_local  # noqa: PLC0415

    async def event_generator():
        try:
            async for chunk in stream_answer_local(body.question, body.context, body.history, db):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            logger.error("SSE stream error: %s", e)
            yield f"data: [ERRO: {e}]\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ReconcileRequest(BaseModel):
    bank_entries: list[dict]
    accounting_entries: list[dict]
    company_name: str = ""


@app.post("/ai/reconcile", tags=["ai"])
@limiter.limit("5/minute")
async def ai_reconcile(
    request: Request,
    body: ReconcileRequest,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Executa conciliação bancária automática."""
    from services.ai_engine.agent_reconciler import reconcile  # noqa: PLC0415
    result = await reconcile(body.bank_entries, body.accounting_entries, body.company_name)
    return result


# ── Audit logs ────────────────────────────────────────────────────────────────

@app.get("/admin/audit-logs", tags=["admin"])
async def list_audit_logs(
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Lista trilha de auditoria (apenas admin)."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import AuditLog  # noqa: PLC0415

    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    logs = result.scalars().all()
    return {
        "logs": [
            {
                "id": str(log.id),
                "username": log.username,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": str(log.entity_id) if log.entity_id else None,
                "company_id": str(log.company_id) if log.company_id else None,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
        "limit": limit,
        "offset": offset,
    }


@app.get("/admin/users", tags=["admin"])
async def list_users(
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista usuários configurados (apenas admin)."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import User  # noqa: PLC0415

    result = await db.execute(select(User).order_by(User.created_at.desc()).limit(100))
    users = result.scalars().all()
    return {
        "users": [
            {
                "username": u.username,
                "email": u.email,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat(),
            }
            for u in users
        ]
    }


@app.post("/admin/users", tags=["admin"], status_code=201)
async def create_user(
    body: UserCreate,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cria um novo usuário. Apenas admin."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import User  # noqa: PLC0415

    role = _validate_role(body.role)

    # Verifica duplicidade de username
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username já existe")

    # Verifica duplicidade de email
    if body.email:
        existing_email = await db.execute(select(User).where(User.email == body.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email já existe")

    password_hash = pwd_context.hash(body.password)
    user = User(
        username=body.username,
        email=body.email,
        password_hash=password_hash,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await _audit(
        db, "user_created", current_user["sub"],
        entity_type="user", entity_id=str(user.id),
        metadata={"username": body.username, "role": role},
    )

    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@app.patch("/admin/users/{username}", tags=["admin"])
async def update_user(
    username: str,
    body: UserUpdate,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Atualiza um usuário. Apenas admin."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import User  # noqa: PLC0415

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if body.username and body.username != user.username:
        existing = await db.execute(select(User).where(User.username == body.username))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Username já existe")
        user.username = body.username

    if body.email and body.email != user.email:
        existing_email = await db.execute(select(User).where(User.email == body.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email já existe")
        user.email = body.email

    if body.password:
        user.password_hash = pwd_context.hash(body.password)

    if body.role:
        user.role = _validate_role(body.role)

    await db.commit()
    await db.refresh(user)

    await _audit(
        db, "user_updated", current_user["sub"],
        entity_type="user", entity_id=str(user.id),
        metadata={"username": user.username, "role": user.role},
    )

    return {
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
    }


@app.patch("/admin/users/{username}/deactivate", tags=["admin"])
async def deactivate_user(
    username: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Desativa um usuário. Apenas admin."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import User  # noqa: PLC0415

    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if user.username == settings.admin_username:
        raise HTTPException(status_code=403, detail="Não é possível desativar o admin principal")

    user.is_active = False
    await db.commit()

    await _audit(
        db, "user_deactivated", current_user["sub"],
        entity_type="user", entity_id=str(user.id),
        metadata={"username": user.username},
    )

    return {"message": "Usuário desativado com sucesso"}


# ── WebSocket (notificações em tempo real — token via header/query, não path) ──

class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, username: str) -> None:
        await websocket.accept()
        self._connections.setdefault(username, []).append(websocket)
        logger.info("WS conectado: user=%s", username)

    def disconnect(self, websocket: WebSocket, username: str) -> None:
        if username in self._connections:
            try:
                self._connections[username].remove(websocket)
            except ValueError:
                pass

    async def send_to_user(self, username: str, message: dict) -> None:
        conns = self._connections.get(username, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, username)

    async def broadcast(self, message: dict) -> None:
        for username in list(self._connections.keys()):
            await self.send_to_user(username, message)


ws_manager = ConnectionManager()


@app.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str | None = None,
):
    """
    WebSocket para notificações em tempo real.
    Token JWT enviado via query param ?token=<jwt> (evita exposição em path/logs).
    Se token não fornecido, tenta validar via cookie httpOnly.
    """
    # Try token from query param first
    jwt_token = token
    
    # If no token in query, try to get from cookie
    if not jwt_token:
        cookies = websocket.query_params.get("cookie") or websocket.headers.get("cookie")
        if cookies:
            # Parse cookies to find access_token
            for cookie in cookies.split(";"):
                cookie = cookie.strip()
                if cookie.startswith("access_token="):
                    jwt_token = cookie.split("=", 1)[1]
                    break
    
    if not jwt_token:
        await websocket.close(code=4001, reason="No token provided")
        return

    try:
        payload = jwt.decode(jwt_token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub", "unknown")
    except JWTError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # Verifica blacklist
    jti = payload.get("jti")
    if jti and _redis:
        try:
            if _redis.get(f"bl:{jti}"):
                await websocket.close(code=4001, reason="Token revoked")
                return
        except Exception:
            pass

    await ws_manager.connect(websocket, username)
    try:
        await websocket.send_json({"type": "connected", "username": username})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, username)
        logger.info("WS desconectado: user=%s", username)
    except Exception as e:
        logger.error("WS error user=%s: %s", username, e)
        ws_manager.disconnect(websocket, username)


# ── Knowledge Base API ─────────────────────────────────────────────────────────

class KnowledgeSearchRequest(BaseModel):
    query: str
    category: Optional[str] = None
    limit: int = 5


class KnowledgeArticleCreate(BaseModel):
    title: str
    content: str
    category: str
    subcategory: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    source_url: Optional[str] = None
    language: str = "pt-BR"


class KnowledgeArticleUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    tags: Optional[list[str]] = None
    source: Optional[str] = None
    source_url: Optional[str] = None


@app.post("/knowledge/search", tags=["knowledge"])
async def search_knowledge_api(
    body: KnowledgeSearchRequest,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Busca conhecimento contábil usando RAG (semântico + lexical)."""
    from services.knowledge.rag_service import search_knowledge  # noqa: PLC0415

    results = await search_knowledge(
        db,
        body.query,
        category=body.category,
        limit=body.limit,
        min_similarity=0.6,
    )
    return {"results": results, "count": len(results)}


@app.post("/knowledge/articles", tags=["knowledge"])
async def create_knowledge_article(
    body: KnowledgeArticleCreate,
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Cria novo artigo na base de conhecimento."""
    from packages.db.models import KnowledgeArticle  # noqa: PLC0415
    from services.knowledge.embedding_service import generate_embedding  # noqa: PLC0415

    article = KnowledgeArticle(
        title=body.title,
        content=body.content,
        category=body.category,
        subcategory=body.subcategory,
        tags=body.tags,
        source=body.source,
        source_url=body.source_url,
        language=body.language,
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Gerar embedding
    embedding = generate_embedding(f"{article.title}\n\n{article.content}")
    from packages.db.models import KnowledgeEmbedding  # noqa: PLC0415
    emb_record = KnowledgeEmbedding(
        article_id=article.id,
        embedding=embedding,
        model="paraphrase-multilingual-MiniLM-L12-v2",
    )
    db.add(emb_record)
    await db.commit()

    await _audit(
        db, "knowledge_article_created", current_user["sub"],
        entity_type="knowledge_article", entity_id=article.id,
        metadata={"title": article.title, "category": article.category},
    )

    return {"id": str(article.id), "message": "Artigo criado com sucesso"}


@app.put("/knowledge/articles/{article_id}", tags=["knowledge"])
async def update_knowledge_article(
    article_id: str,
    body: KnowledgeArticleUpdate,
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Atualiza artigo existente na base de conhecimento."""
    from packages.db.models import KnowledgeArticle  # noqa: PLC0415
    from sqlalchemy import select  # noqa: PLC0415

    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == uuid.UUID(article_id))
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")

    # Atualizar campos fornecidos
    if body.title is not None:
        article.title = body.title
    if body.content is not None:
        article.content = body.content
    if body.category is not None:
        article.category = body.category
    if body.subcategory is not None:
        article.subcategory = body.subcategory
    if body.tags is not None:
        article.tags = body.tags
    if body.source is not None:
        article.source = body.source
    if body.source_url is not None:
        article.source_url = body.source_url

    article.updated_at = datetime.now(timezone.utc)
    await db.commit()

    # Nota: Regeneração de embeddings desabilitada temporariamente devido a erro de tipo PG
    # Para regenerar embeddings, use DELETE + POST no artigo

    await _audit(
        db, "knowledge_article_updated", current_user["sub"],
        entity_type="knowledge_article", entity_id=article.id,
        metadata={"title": article.title},
    )

    return {"id": str(article.id), "message": "Artigo atualizado com sucesso"}


@app.delete("/knowledge/articles/{article_id}", tags=["knowledge"])
async def delete_knowledge_article(
    article_id: str,
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Exclui artigo da base de conhecimento (apenas admin)."""
    from packages.db.models import KnowledgeArticle  # noqa: PLC0415
    from sqlalchemy import delete, select  # noqa: PLC0415

    # Verificar se artigo existe
    result = await db.execute(
        select(KnowledgeArticle).where(KnowledgeArticle.id == uuid.UUID(article_id))
    )
    article = result.scalar_one_or_none()

    if not article:
        raise HTTPException(status_code=404, detail="Artigo não encontrado")

    title = article.title

    # Deletar usando DELETE direto para evitar carregar embeddings (erro PG type)
    await db.execute(
        delete(KnowledgeArticle).where(KnowledgeArticle.id == uuid.UUID(article_id))
    )
    await db.commit()

    await _audit(
        db, "knowledge_article_deleted", current_user["sub"],
        entity_type="knowledge_article", entity_id=article.id,
        metadata={"title": title},
    )

    return {"message": "Artigo excluído com sucesso"}


@app.post("/knowledge/upload", tags=["knowledge"])
async def upload_knowledge_pdf(
    request: Request,
    file: UploadFile = File(...),
    title: str = None,  # type: ignore[assignment]
    category: str = "conceito",  # type: ignore[assignment]
    current_user: dict = Depends(require_role(["admin", "analista"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Upload de PDF para processar e adicionar à base de conhecimento RAG."""
    from services.parser.pdf_parser import extract_pdf  # noqa: PLC0415
    from packages.db.models import KnowledgeArticle, KnowledgeEmbedding  # noqa: PLC0415
    from services.knowledge.embedding_service import generate_embedding  # noqa: PLC0415

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=415,
            detail="Apenas arquivos PDF são suportados para upload de conhecimento"
        )

    # Extrair texto do PDF
    content_bytes = await file.read()
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content_bytes)
        tmp_path = tmp.name

    try:
        text_content = extract_pdf(tmp_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erro ao processar PDF: {str(e)}")
    finally:
        import os
        os.unlink(tmp_path)

    # Usar título fornecido ou nome do arquivo
    article_title = title or file.filename.replace(".pdf", "")

    # Criar artigo
    article = KnowledgeArticle(
        title=article_title,
        content=text_content,
        category=category,
        source=f"Upload: {file.filename}",
        language="pt-BR",
    )
    db.add(article)
    await db.commit()
    await db.refresh(article)

    # Gerar embedding
    embedding = generate_embedding(f"{article.title}\n\n{article.content}")
    emb_record = KnowledgeEmbedding(
        article_id=article.id,
        embedding=embedding,
        model="paraphrase-multilingual-MiniLM-L12-v2",
    )
    db.add(emb_record)
    await db.commit()

    await _audit(
        db, "knowledge_pdf_uploaded", current_user["sub"],
        entity_type="knowledge_article", entity_id=article.id,
        metadata={"filename": file.filename, "title": article.title},
    )

    return {
        "id": str(article.id),
        "message": "PDF processado e adicionado à base de conhecimento",
        "title": article.title,
        "content_length": len(text_content)
    }


@app.get("/knowledge/articles/{article_id}", tags=["knowledge"])
async def get_knowledge_article(
    article_id: str,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recupera artigo completo por ID."""
    from services.knowledge.rag_service import get_article_by_id  # noqa: PLC0415

    article = await get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Artigo não encontrado.")
    return article


@app.get("/knowledge/articles", tags=["knowledge"])
async def list_knowledge_articles(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Lista artigos de conhecimento com paginação."""
    from services.knowledge.rag_service import list_articles  # noqa: PLC0415

    articles = await list_articles(db, category=category, limit=limit, offset=offset)
    return {"articles": articles, "count": len(articles)}


@app.get("/templates/reports", tags=["knowledge"])
async def list_report_templates(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    template_type: Optional[str] = None,
    sector: Optional[str] = None,
) -> dict:
    """Lista templates de relatórios."""
    from services.knowledge.template_service import get_report_template  # noqa: PLC0415

    if template_type:
        template = await get_report_template(db, template_type, sector)
        if template:
            return {"templates": [template], "count": 1}
        return {"templates": [], "count": 0}

    # Listar todos (implementação futura)
    return {"templates": [], "count": 0, "message": "Use ?type=dre ou ?type=balanco para buscar específico"}


@app.get("/templates/accounts", tags=["knowledge"])
async def list_account_templates(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    sector: Optional[str] = None,
) -> dict:
    """Lista planos de contas por setor."""
    from services.knowledge.template_service import get_account_template  # noqa: PLC0415

    if sector:
        template = await get_account_template(db, sector)
        if template:
            return {"templates": [template], "count": 1}
        return {"templates": [], "count": 0}

    return {
        "templates": [],
        "count": 0,
        "message": "Use ?sector=servicos ou ?sector=comercio para buscar específico",
    }


@app.post("/admin/knowledge/seed", tags=["admin"])
async def seed_knowledge_base(
    current_user: dict = Depends(require_role(["admin"])),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Popula base de conhecimento com conteúdo inicial (apenas admin)."""
    from services.knowledge.knowledge_seeder import seed_knowledge_base  # noqa: PLC0415
    from services.knowledge.template_service import seed_templates  # noqa: PLC0415

    stats_kb = await seed_knowledge_base(db)
    stats_templates = await seed_templates(db)

    await _audit(
        db, "knowledge_seeded", current_user["sub"],
        metadata={"knowledge_stats": stats_kb, "template_stats": stats_templates},
    )

    return {
        "message": "Base de conhecimento populada com sucesso",
        "knowledge": stats_kb,
        "templates": stats_templates,
    }


@app.post("/telemetry", tags=["infra"])
async def receive_telemetry(
    request: Request,
    data: dict,
) -> JSONResponse:
    """Recebe eventos de telemetry do frontend."""
    correlation_id = correlation_id_var.get() or request.headers.get("X-Correlation-ID")
    logger.info(
        "Telemetry event: %s (correlation_id=%s)",
        data.get("name"),
        correlation_id,
    )
    return JSONResponse(content={"status": "received"})
