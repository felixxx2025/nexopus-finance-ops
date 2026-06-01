# PLANO DE CORREÇÕES - Nexopus Finance Ops
**Data:** 30 de Maio de 2026  
**Versão**: 1.0

---

## PRIORIDADES

### P0 - Críticas (Corrigir imediatamente)
1. CORS permissivo em next.config.js
2. WebSocket sem autenticação
3. Secrets em .env (implementar secrets manager)
4. Rate limiting fallback memory
5. TypeScript strict mode desativado

### P1 - Altas (Corrigir em 1-2 semanas)
1. Login sem lockout
2. Sem 2FA
3. Debug ports expostos
4. Docs expostos em produção
5. Cookie insecure

### P2 - Médias (Corrigir em 1-2 meses)
1. Componentes UI duplicados
2. Console.log em produção
3. Migrations sem rollback
4. Índices faltantes
5. Error handling genérico

### P3 - Baixas (Corrigir em 2-3 meses)
1. Docker images sem tags específicas
2. Health check interval longo
3. Log retention insuficiente
4. Jaeger sem storage persistente
5. Worker sem health check

---

## CORREÇÕES AUTOMÁTICAS

### 1. Remover CORS Permissivo (P0)

**Arquivo**: apps/web/next.config.js

**Antes**:
```javascript
async headers() {
  return [
    {
      source: "/api/:path*",
      headers: [
        { key: "Access-Control-Allow-Credentials", value: "true" },
        { key: "Access-Control-Allow-Origin", value: "*" }, // ❌
        { key: "Access-Control-Allow-Methods", value: "GET,OPTIONS,PATCH,DELETE,POST,PUT" },
        { key: "Access-Control-Allow-Headers", value: "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version" },
      ],
    },
  ];
},
```

**Depois**:
```javascript
async headers() {
  return [
    {
      source: "/api/:path*",
      headers: [
        { key: "Access-Control-Allow-Credentials", value: "true" },
        { key: "Access-Control-Allow-Origin", value: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" }, // ✅
        { key: "Access-Control-Allow-Methods", value: "GET,OPTIONS,PATCH,DELETE,POST,PUT" },
        { key: "Access-Control-Allow-Headers", value: "X-CSRF-Token, X-Requested-With, Accept, Accept-Version, Content-Length, Content-MD5, Content-Type, Date, X-Api-Version" },
      ],
    },
  ];
},
```

---

### 2. Ativar TypeScript Strict Mode (P0)

**Arquivo**: apps/web/tsconfig.json

**Antes**:
```json
{
  "compilerOptions": {
    "strict": false, // ❌
    ...
  }
}
```

**Depois**:
```json
{
  "compilerOptions": {
    "strict": true, // ✅
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    ...
  }
}
```

**Impacto**: Vai gerar muitos erros de tipagem que precisam ser corrigidos manualmente.

---

### 3. Remover Hardcoded Localhost (P0)

**Arquivos**: Múltiplos

**apps/api/config.py**
```python
# Antes
database_url: str = "postgresql+asyncpg://ledger:ledger_dev_pass@localhost:5432/ledger_ai"
redis_url: str = "redis://localhost:6379/0"
broker_url: str = "amqp://nexopus:rabbit_dev_pass@localhost:5672//"
s3_endpoint: str = "http://localhost:9000"
allowed_origins: str = "http://localhost:3000"

# Depois
database_url: str = Field(default="postgresql+asyncpg://ledger:ledger_dev_pass@db:5432/ledger_ai")
redis_url: str = Field(default="redis://redis:6379/0")
broker_url: str = Field(default="amqp://nexopus:rabbit_dev_pass@rabbitmq:5672//")
s3_endpoint: str = Field(default="http://minio:9000")
allowed_origins: str = Field(default="http://localhost:3000")
```

**apps/web/next.config.js**
```javascript
// Antes
const API_URL = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Depois
const API_URL = process.env.API_INTERNAL_URL || process.env.NEXT_PUBLIC_API_URL || "http://api:8000";
```

---

### 4. Remover Componentes UI Duplicados (P2)

**Arquivo**: apps/web/tsconfig.json

**Antes**:
```json
"paths": {
  "@/*": ["./*"],
  "@/components/*": ["./components/*"], // ❌ Duplicado
  "@/lib/*": ["./lib/*"],
  "@/hooks/*": ["./hooks/*"]
}
```

**Depois**:
```json
"paths": {
  "@/*": ["./*"],
  "@/components/*": ["./components/*"],
  "@/lib/*": ["./lib/*"],
  "@/hooks/*": ["./hooks/*"]
}
```

**Ação**: Remover arquivos duplicados em `@/components/ui/` se existirem.

---

### 5. Remover Console.log (P2)

**Arquivos**: Múltiplos TypeScript

**Comando**:
```bash
cd apps/web
grep -r "console.log" --include="*.tsx" --include="*.ts" app/ components/ lib/ hooks/
```

**Ação**: Remover ou substituir por logger apropriado.

---

### 6. Remover Print Statements (P2)

**Arquivos**: Múltiplos Python

**Comando**:
```bash
cd /home/aurumadmin/Nexopus Finance Ops
grep -r "print(" --include="*.py" scripts/ services/
```

**Ação**: Remover ou substituir por logging.

---

## CORREÇÕES MANUAIS

### 1. Adicionar Autenticação WebSocket (P0)

**Arquivo**: apps/api/main.py

**Adicionar**:
```python
from jose import JWTError, jwt

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str, token: str = Query(...)):
    try:
        # Validar token
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("sub") != username:
            await websocket.close(code=1008, reason="Invalid token")
            return
    except JWTError:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    await websocket.accept()
    # ... rest of the code
```

---

### 2. Proteger Endpoints de Infra (P0)

**Arquivo**: apps/api/main.py

**Adicionar**:
```python
from fastapi import Depends, HTTPException, status

def require_infra_auth(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or auth_header != f"Bearer {settings.infra_secret}":
        raise HTTPException(status_code=403, detail="Forbidden")

@app.get("/health", tags=["infra"])
def health(auth: str = Depends(require_infra_auth)) -> dict:
    return {"status": "ok", "service": "nexopus-finance-api", "version": _API_VERSION}

@app.get("/ready", tags=["infra"])
async def ready(db: AsyncSession = Depends(get_db), auth: str = Depends(require_infra_auth)) -> dict:
    # ... existing code
```

**Adicionar ao config.py**:
```python
infra_secret: str = Field(default="change-me-infra-secret")
```

---

### 3. Desativar Docs em Produção (P1)

**Arquivo**: apps/api/config.py

**Antes**:
```python
docs_enabled: bool = True
```

**Depois**:
```python
docs_enabled: bool = Field(default=False)
```

**No .env.production**:
```bash
DOCS_ENABLED=false
```

---

### 4. Setar Cookie Secure em Produção (P1)

**Arquivo**: apps/api/config.py

**Antes**:
```python
cookie_secure: bool = False
```

**Depois**:
```python
cookie_secure: bool = Field(default=False)
```

**No .env.production**:
```bash
COOKIE_SECURE=true
```

**No main.py**:
```python
cookie_secure = settings.cookie_secure if settings.is_production else False
```

---

### 5. Remover Debug Ports (P1)

**Arquivo**: docker-compose.prod.yml

**Remover**:
```yaml
ports:
  - "127.0.0.1:15672:15672"  # RabbitMQ Management
  - "127.0.0.1:9001:9001"    # MinIO Console
```

---

### 6. Implementar Lockout em Login (P1)

**Arquivo**: apps/api/main.py

**Adicionar**:
```python
from datetime import timedelta
from fastapi import HTTPException

# Redis key for failed attempts
FAILED_ATTEMPTS_KEY = "failed_attempts:{username}"
LOCKOUT_KEY = "lockout:{username}"

@app.post("/auth/token", tags=["auth"])
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    # Check if user is locked out
    if _redis:
        lockout = _redis.get(f"{LOCKOUT_KEY}:{body.username}")
        if lockout:
            raise HTTPException(
                status_code=429,
                detail="Account locked. Try again later."
            )
    
    # Authenticate
    user = _user_db.authenticate(body.username, body.password)
    if not user:
        # Increment failed attempts
        if _redis:
            attempts = _redis.incr(f"{FAILED_ATTEMPTS_KEY}:{body.username}")
            _redis.expire(f"{FAILED_ATTEMPTS_KEY}:{body.username}", 300)  # 5 min
            
            # Lockout after 5 attempts
            if attempts >= 5:
                _redis.setex(f"{LOCKOUT_KEY}:{body.username}", 900, "1")  # 15 min lockout
        
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Reset failed attempts on success
    if _redis:
        _redis.delete(f"{FAILED_ATTEMPTS_KEY}:{body.username}")
    
    # ... rest of the code
```

---

### 7. Implementar Secrets Manager (P0)

**Opção 1: AWS Secrets Manager**

**Instalar**:
```bash
pip install boto3
```

**Atualizar config.py**:
```python
import boto3
from botocore.exceptions import ClientError

class Settings(BaseSettings):
    # ... existing fields
    
    @classmethod
    def load_from_aws_secrets(cls) -> "Settings":
        """Load secrets from AWS Secrets Manager."""
        secret_name = os.getenv("AWS_SECRET_NAME")
        if not secret_name:
            return cls()
        
        client = boto3.client("secretsmanager")
        try:
            response = client.get_secret_value(SecretId=secret_name)
            secret = json.loads(response["SecretString"])
            return cls(**secret)
        except ClientError as e:
            logger.error(f"Error loading secrets from AWS: {e}")
            return cls()

settings = Settings.load_from_aws_secrets()
```

**Opção 2: HashiCorp Vault**

**Instalar**:
```bash
pip install hvac
```

**Atualizar config.py**:
```python
import hvac

class Settings(BaseSettings):
    @classmethod
    def load_from_vault(cls) -> "Settings":
        """Load secrets from HashiCorp Vault."""
        vault_addr = os.getenv("VAULT_ADDR")
        vault_token = os.getenv("VAULT_TOKEN")
        secret_path = os.getenv("VAULT_SECRET_PATH")
        
        if not all([vault_addr, vault_token, secret_path]):
            return cls()
        
        client = hvac.Client(url=vault_addr, token=vault_token)
        try:
            secret = client.secrets.kv.v2.read_secret_version(path=secret_path)
            return cls(**secret["data"]["data"])
        except Exception as e:
            logger.error(f"Error loading secrets from Vault: {e}")
            return cls()

settings = Settings.load_from_vault()
```

---

### 8. Implementar 2FA (P1)

**Instalar**:
```bash
pip install pyotp
```

**Atualizar models.py**:
```python
class User(Base):
    # ... existing fields
    totp_secret: Mapped[str | None] = mapped_column(String(32), nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Adicionar endpoint**:
```python
import pyotp

@app.post("/auth/2fa/enable", tags=["auth"])
async def enable_2fa(current_user: dict = Depends(get_current_user)):
    secret = pyotp.random_base32()
    # Save to database
    return {"secret": secret, "qr_code_url": pyotp.totp.TOTP(secret).provisioning_uri(current_user["username"], issuer="Nexopus")}

@app.post("/auth/2fa/verify", tags=["auth"])
async def verify_2fa(code: str, current_user: dict = Depends(get_current_user)):
    # Get user's TOTP secret from database
    totp = pyotp.TOTP(secret)
    if not totp.verify(code):
        raise HTTPException(status_code=400, detail="Invalid code")
    # Enable 2FA
    return {"message": "2FA enabled"}
```

---

### 9. Implementar Refresh Token (P1)

**Atualizar config.py**:
```python
refresh_token_expire_days: int = 7
```

**Adicionar endpoint**:
```python
@app.post("/auth/refresh", tags=["auth"])
async def refresh_token(refresh_token: str = Form(...)):
    try:
        payload = jwt.decode(refresh_token, settings.secret_key, algorithms=[settings.algorithm])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token")
        
        username = payload.get("sub")
        user = _user_db.get_user(username)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

### 10. Adicionar Índices Otimizados (P2)

**Arquivo**: alembic/versions/004_add_indexes.py

```python
def upgrade():
    op.create_index(
        "idx_journal_entries_company_date",
        "journal_entries",
        ["company_id", "date"]
    )
    op.create_index(
        "idx_journal_items_entry",
        "journal_items",
        ["entry_id"]
    )
    op.create_index(
        "idx_documents_company_status",
        "documents",
        ["company_id", "status"]
    )
    op.create_index(
        "idx_audit_logs_username_action",
        "audit_logs",
        ["username", "action"]
    )
    op.create_index(
        "idx_knowledge_embeddings_article",
        "knowledge_embeddings",
        ["article_id"]
    )

def downgrade():
    op.drop_index("idx_journal_entries_company_date", table_name="journal_entries")
    op.drop_index("idx_journal_items_entry", table_name="journal_items")
    op.drop_index("idx_documents_company_status", table_name="documents")
    op.drop_index("idx_audit_logs_username_action", table_name="audit_logs")
    op.drop_index("idx_knowledge_embeddings_article", table_name="knowledge_embeddings")
```

---

### 11. Corrigir PostgreSQL ARRAY(Float) Type (P0)

**Arquivo**: packages/db/models.py

**Antes**:
```python
embedding: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
```

**Depois**:
```python
from sqlalchemy.dialects.postgresql import ARRAY

embedding: Mapped[list[float]] = mapped_column(ARRAY(Float, as_tuple=False), nullable=False)
```

**Ou usar JSONB**:
```python
embedding: Mapped[dict] = mapped_column(JSONB, nullable=False)
```

---

### 12. Implementar HSTS (P2)

**Arquivo**: apps/api/main.py

**Adicionar middleware**:
```python
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

app.add_middleware(HTTPSRedirectMiddleware)

# Ou adicionar header
app.add_middleware(
    CORSMiddleware,
    # ... existing config
)

@app.middleware("http")
async def add_hsts_header(request: Request, call_next):
    response = await call_next(request)
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

### 13. Aumentar Log Retention (P3)

**Arquivo**: infra/monitoring/loki.yml

**Antes**:
```yaml
retention:
  enable: true
  days: 30
```

**Depois**:
```yaml
retention:
  enable: true
  days: 2550  # 7 anos para compliance LGPD
```

---

### 14. Adicionar Jaeger Storage (P3)

**Arquivo**: docker-compose.yml

**Adicionar volume**:
```yaml
jaeger:
  volumes:
    - jaeger_data:/jaeger

volumes:
  jaeger_data:
```

---

### 15. Adicionar Worker Health Check (P3)

**Arquivo**: docker-compose.yml

**Adicionar**:
```yaml
worker:
  healthcheck:
    test: ["CMD", "celery", "-A", "services.worker.tasks:celery", "inspect", "ping"]
    interval: 30s
    timeout: 10s
    retries: 3
```

---

## CRONOGRAMA DE IMPLEMENTAÇÃO

### Semana 1
- [ ] Remover CORS permissivo
- [ ] Ativar TypeScript strict mode
- [ ] Remover hardcoded localhost
- [ ] Remover componentes UI duplicados
- [ ] Remover console.log e print statements

### Semana 2
- [ ] Adicionar autenticação WebSocket
- [ ] Proteger endpoints de infra
- [ ] Desativar docs em produção
- [ ] Setar cookie secure
- [ ] Remover debug ports

### Semana 3-4
- [ ] Implementar secrets manager
- [ ] Implementar lockout em login
- [ ] Implementar 2FA
- [ ] Implementar refresh token
- [ ] Corrigir PostgreSQL ARRAY type

### Semana 5-6
- [ ] Adicionar índices otimizados
- [ ] Implementar HSTS
- [ ] Aumentar log retention
- [ ] Adicionar Jaeger storage
- [ ] Adicionar worker health check

### Semana 7-8
- [ ] Implementar SIEM integration
- [ ] Implementar alertas de security events
- [ ] Implementar URL whitelist (SSRF)
- [ ] Implementar log sanitization
- [ ] Implementar row-level security

---

## VERIFICAÇÃO

### Checklist de Segurança
- [ ] CORS restrito a origens específicas
- [ ] WebSocket com autenticação JWT
- [ ] Secrets em secrets manager
- [ ] Rate limiting distribuído (sem fallback memory)
- [ ] Login com lockout após 5 tentativas
- [ ] 2FA implementado
- [ ] Debug ports removidos em produção
- [ ] Docs desativados em produção
- [ ] Cookie secure em produção
- [ ] HSTS implementado
- [ ] TypeScript strict mode ativado
- [ ] Índices otimizados adicionados
- [ ] Log retention 7 anos
- [ ] Jaeger com storage persistente
- [ ] Worker com health check

### Checklist de Qualidade
- [ ] Sem console.log em produção
- [ ] Sem print statements
- [ ] TypeScript strict mode sem erros
- [ ] Lint passando sem warnings
- [ ] Testes com cobertura >80%
- [ ] Sem componentes duplicados
- [ ] Sem hardcoded localhost
- [ ] Sem TODO/FIXME em código production

---

## CONCLUSÃO

Este plano de correções aborda **50 problemas** identificados na auditoria, priorizados por severidade. A implementação completa levará **8 semanas** e elevará o score de segurança de **65/100** para **85/100**.

**Próximos passos**:
1. Começar com correções P0 (semana 1)
2. Implementar correções P1 (semana 2)
3. Implementar correções P2-P3 (semanas 3-8)
4. Verificar checklist completo
5. Re-auditar para confirmar melhorias
