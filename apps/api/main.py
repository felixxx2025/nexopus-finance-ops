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

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Configuração centralizada ─────────────────────────────────────────────────
from apps.api.config import settings  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

_API_VERSION = "2.1.0"

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


# ── FastAPI ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Nexopus Finance Ops — API",
    description="Motor contábil com IA para DRE, Balanço, relatórios e auditoria financeira.",
    version=_API_VERSION,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Requested-With"],
)


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


# ── Auth helpers ──────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


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
    user = _user_db.authenticate(body.username, body.password)
    if not user:
        logger.warning("Tentativa de login inválida para '%s'", body.username)
        await _audit(
            db, "login_failed", body.username,
            ip_address=request.client.host if request.client else None,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    role = user.get("role", "viewer")
    if hasattr(role, "value"):
        role = role.value

    token, _jti = _create_access_token(sub=body.username, role=role)
    logger.info("Login bem-sucedido para '%s' (role=%s)", body.username, role)

    await _audit(
        db, "login", body.username,
        ip_address=request.client.host if request.client else None,
    )

    response = JSONResponse(
        content={"access_token": token, "token_type": "bearer", "username": body.username, "role": role}
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

@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "service": "nexopus-finance-api", "version": _API_VERSION}


@app.get("/ready", tags=["infra"])
async def ready(db: AsyncSession = Depends(get_db)) -> dict:
    """Verifica prontidão da API (DB + Redis)."""
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


@app.get("/companies", tags=["companies"])
async def list_companies(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Lista todas as empresas."""
    from sqlalchemy import select  # noqa: PLC0415
    from packages.db.models import Company  # noqa: PLC0415

    result = await db.execute(select(Company).order_by(Company.name))
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

    stmt = select(Document).where(Document.company_id == company_id).order_by(Document.created_at.desc())
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
    result = predict_cashflow(body.lancamentos, body.company_name)
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
    result = audit_entries(
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
) -> StreamingResponse:
    """Assistente financeiro conversacional com streaming SSE."""
    from services.ai_engine.agent_assistant import stream_answer  # noqa: PLC0415

    async def event_generator():
        try:
            async for chunk in stream_answer(body.question, body.context, body.history):
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
    result = reconcile(body.bank_entries, body.accounting_entries, body.company_name)
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
async def list_users(current_user: dict = Depends(require_role(["admin"]))) -> dict:
    """Lista usuários configurados (apenas admin)."""
    return {
        "message": "Use EXTRA_USERS_JSON env var para gerenciar usuários adicionais.",
        "admin": settings.admin_username,
    }


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
async def websocket_notifications(websocket: WebSocket):
    """
    WebSocket para notificações em tempo real.
    Token JWT enviado via query param ?token=<jwt> (evita exposição em path/logs).
    """
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username = payload.get("sub", "unknown")
    except JWTError:
        await websocket.close(code=4001)
        return

    # Verifica blacklist
    jti = payload.get("jti")
    if jti and _redis:
        try:
            if _redis.get(f"bl:{jti}"):
                await websocket.close(code=4001)
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


# ── Startup ───────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    try:
        from apps.api.observability import setup_all  # noqa: PLC0415
        setup_all(app, settings)
    except Exception as e:
        logger.warning("Observabilidade parcialmente inicializada: %s", e)
    logger.info("Nexopus Finance API v%s iniciada (env=%s).", _API_VERSION, settings.environment)
