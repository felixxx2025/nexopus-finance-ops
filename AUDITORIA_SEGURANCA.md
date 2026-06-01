# AUDITORIA DE SEGURANÇA - Nexopus Finance Ops
**Data:** 30 de Maio de 2026  
**Versão:** 1.0

---

## SCORE SEGURANÇA: 65/100 (🟡 MÉDIO)

---

## 1. OWASP TOP 10 - ANÁLISE DETALHADA

### A01: Broken Access Control
**Score**: 3/10 (🔴 CRÍTICO)

#### Vulnerabilidades
1. **WebSocket sem autenticação**
   - **Localização**: `/ws/{u}` em main.py
   - **Risco**: Qualquer um pode conectar ao WebSocket se souber o username
   - **Severidade**: Alta
   - **Mitigação**: Adicionar validação de JWT token na conexão WebSocket

2. **Endpoints de infra públicos**
   - **Localização**: `/health`, `/ready`, `/metrics`
   - **Risco**: Exposição de informações sensíveis, DoS
   - **Severidade**: Média
   - **Mitigação**: Adicionar autenticação básica ou IP whitelist

3. **CORS muito permissivo**
   - **Localização**: next.config.js (Access-Control-Allow-Origin: *)
   - **Risco**: CSRF, data exfiltration
   - **Severidade**: Alta
   - **Mitigação**: Restringir a origens específicas

4. **Docs expostos em produção**
   - **Localização**: `/docs`, `/redoc` ativos
   - **Risco**: Exposição de API internals
   - **Severidade**: Média
   - **Mitigação**: Desativar em produção

#### Código Vulnerável
```python
# main.py - WebSocket sem autenticação
@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await websocket.accept()
    # ❌ Sem validação de token
```

```javascript
// next.config.js - CORS permissivo
headers: [
  { key: "Access-Control-Allow-Origin", value: "*" }, // ❌ Perigoso
]
```

---

### A02: Cryptographic Failures
**Score**: 4/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Secrets em .env**
   - **Localização**: .env, .env.example
   - **Risco**: Exposição se .env for commitado
   - **Severidade**: Alta
   - **Mitigação**: Implementar secrets manager (AWS Secrets, Vault)

2. **JWT secret pode ser fraco**
   - **Localização**: config.py (min_length=32)
   - **Risco**: Brute force se secret for fraco
   - **Severidade**: Média
   - **Mitigação**: Exigir mínimo 64 chars, usar secrets manager

3. **Database credentials em texto puro**
   - **Localização**: docker-compose.yml, .env
   - **Risco**: Exposição em logs, memory dumps
   - **Severidade**: Alta
   - **Mitigação**: Usar secrets manager, encryption at rest

4. **Redis password em texto puro**
   - **Localização**: docker-compose.yml
   - **Risco**: Exposição
   - **Severidade**: Média
   - **Mitigação**: Secrets manager

5. **S3 credentials em texto puro**
   - **Localização**: docker-compose.yml
   - **Risco**: Exposição
   - **Severidade**: Alta
   - **Mitigação**: Secrets manager, IAM roles

#### Código Vulnerável
```python
# config.py - Secret mínimo 32 chars
secret_key: str = Field(..., min_length=32)  # ❌ Deveria ser 64+
```

```yaml
# docker-compose.yml - Credentials em texto puro
environment:
  POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}  # ❌ Sem encryption
  REDIS_PASSWORD: ${REDIS_PASSWORD}        # ❌ Sem encryption
```

---

### A03: Injection
**Score**: 7/10 (🟢 BOM)

#### Vulnerabilidades
1. **SQL Injection**
   - **Status**: MITIGADO (SQLAlchemy ORM)
   - **Análise**: SQLAlchemy usa parameterized queries
   - **Risco**: Baixo

2. **NoSQL Injection**
   - **Status**: N/A (PostgreSQL apenas)

3. **Command Injection**
   - **Status**: MITIGADO (sem execução de comandos)
   - **Análise**: Sem subprocess.run com input do usuário
   - **Risco**: Baixo

4. **XPath Injection**
   - **Status**: N/A

5. **LDAP Injection**
   - **Status**: N/A

#### Magic Bytes Validation
```python
# main.py - Validação insuficiente
ALLOWED_MIME_TYPES = ["application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]
# ❌ Valida apenas MIME type, não magic bytes reais
```

**Mitigação**: Implementar validação de magic bytes com python-magic

---

### A04: Insecure Design
**Score**: 5/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Rate limiting com fallback memory**
   - **Localização**: main.py (storage_uri="memory://" se Redis indisponível)
   - **Risco**: Rate limiting não funciona em multi-instance
   - **Severidade**: Média
   - **Mitigação**: Exigir Redis, não usar fallback

2. **Sem retry limit em login**
   - **Localização**: auth endpoints
   - **Risco**: Brute force
   - **Severidade**: Alta
   - **Mitigação**: Implementar lockout após 5 tentativas falhas

3. **Sem CAPTCHA em signup**
   - **Localização**: signup não implementado
   - **Risco**: Bot accounts
   - **Severidade**: Média
   - **Mitigação**: Adicionar reCAPTCHA

4. **Sem 2FA**
   - **Status**: Não implementado
   - **Risco**: Account takeover
   - **Severidade**: Alta
   - **Mitigação**: Implementar TOTP (Google Authenticator)

#### Código Vulnerável
```python
# main.py - Rate limiting fallback inseguro
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=settings.redis_url if _redis else "memory://",  # ❌ Inseguro
)
```

---

### A05: Security Misconfiguration
**Score**: 4/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Debug ports expostos**
   - **Localização**: docker-compose.yml (MinIO 9001, RabbitMQ 15672)
   - **Risco**: Acesso não autorizado em produção
   - **Severidade**: Alta
   - **Mitigação**: Remover ports em docker-compose.prod.yml

2. **Cookie secure=False**
   - **Localização**: config.py
   - **Risco**: Cookie interceptado em HTTP
   - **Severidade**: Alta
   - **Mitigação**: Setar True em produção

3. **Docs expostos em produção**
   - **Localização**: config.py (docs_enabled=True)
   - **Risco**: Exposição de API internals
   - **Severidade**: Média
   - **Mitigação**: Setar False em produção

4. **SQLAlchemy echo=False**
   - **Localização**: main.py
   - **Risco**: Dificulta debug em produção
   - **Severidade**: Baixa
   - **Mitigação**: Setar True apenas em development

5. **HSTS não implementado**
   - **Status**: Não implementado
   - **Risco**: Downgrade attacks
   - **Severidade**: Média
   - **Mitigação**: Adicionar header Strict-Transport-Security

#### Código Vulnerável
```python
# config.py - Cookie insecure
cookie_secure: bool = False  # ❌ Deveria ser True em produção
```

```python
# config.py - Docs expostos
docs_enabled: bool = True  # ❌ Deveria ser False em produção
```

---

### A06: Vulnerable Components
**Score**: 6/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Dependências não auditadas regularmente**
   - **Status**: pip-audit configurado mas não automatizado
   - **Risco**: CVEs em dependências
   - **Severidade**: Alta
   - **Mitigação**: Automatizar SCA no CI/CD

2. **Dependências desatualizadas**
   - **Status**: Não auditado
   - **Risco**: CVEs conhecidos
   - **Severidade**: Média
   - **Mitigação**: Dependabot, Renovate

3. **Node modules vulneráveis**
   - **Status**: Não auditado
   - **Risco**: CVEs em frontend
   - **Severidade**: Média
   - **Mitigação**: npm audit, Snyk

#### Dependências Críticas
- **bcrypt==4.0.1**: Versão fixa (pode ter CVEs)
- **sentence-transformers**: Versão dinâmica
- **next-pwa**: Desabilitado mas ainda instalado

---

### A07: Authentication Failures
**Score**: 5/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Sem rate limiting em login**
   - **Localização**: POST /auth/token
   - **Risco**: Brute force
   - **Severidade**: Alta
   - **Mitigação**: Implementar rate limiting específico

2. **Sem lockout após tentativas falhas**
   - **Status**: Não implementado
   - **Risco**: Brute force
   - **Severidade**: Alta
   - **Mitigação**: Implementar lockout temporário

3. **JWT sem refresh token**
   - **Status**: Apenas access token (60min)
   - **Risco**: Usuário precisa logar novamente
   - **Severidade**: Baixa
   - **Mitigação**: Implementar refresh token com rotação

4. **JWT sem revogação imediata**
   - **Status**: Redis blacklist implementado
   - **Risco**: Token pode ser usado até expirar
   - **Severidade**: Baixa
   - **Mitigação**: Implementar short-lived access tokens (5min)

5. **Sem 2FA**
   - **Status**: Não implementado
   - **Risco**: Account takeover
   - **Severidade**: Alta
   - **Mitigação**: Implementar TOTP

#### Código Vulnerável
```python
# main.py - Login sem lockout
@app.post("/auth/token")
@limiter.limit("10/minute")  # ❌ Rate limit global, não específico
async def login(...):
    # ❌ Sem lockout após tentativas falhas
```

---

### A08: Software/Data Integrity Failures
**Score**: 6/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Sem verificação de integridade de uploads**
   - **Localização**: upload_document
   - **Risco**: Arquivos corrompidos ou maliciosos
   - **Severidade**: Média
   - **Mitigação**: Adicionar SHA256 verification

2. **Sem checksum em downloads**
   - **Localização**: download endpoints
   - **Risco**: Arquivos corrompidos
   - **Severidade**: Baixa
   - **Mitigação**: Adicionar ETag ou checksum

3. **Sem assinatura digital em relatórios**
   - **Status**: Não implementado
   - **Risco**: Relatórios podem ser alterados
   - **Severidade**: Alta (para compliance)
   - **Mitigação**: Implementar assinatura digital

---

### A09: Security Logging Failures
**Score**: 5/10 (🟡 MÉDIO)

#### Vulnerabilidades
1. **Logs estruturados incompletos**
   - **Status**: Parcialmente implementado (observability.py)
   - **Risco**: Dificuldade de análise
   - **Severidade**: Baixa
   - **Mitigação**: Completar logging estruturado

2. **Sem alert de security events**
   - **Status**: Não implementado
   - **Risco**: Incidentes não detectados
   - **Severidade**: Alta
   - **Mitigação**: Implementar alertas (Sentry, PagerDuty)

3. **Sem SIEM integration**
   - **Status**: Não implementado
   - **Risco**: Logs centralizados não analisados
   - **Severidade**: Média
   - **Mitigação**: Integrar com SIEM (Splunk, ELK)

4. **Log retention insuficiente**
   - **Status**: 30 dias
   - **Risco**: Não compliance (LGPD exige 7 anos)
   - **Severidade**: Alta
   - **Mitigação**: Aumentar para 7 anos

---

### A10: Server-Side Request Forgery (SSRF)
**Score**: 7/10 (🟢 BOM)

#### Vulnerabilidades
1. **Web search sem validação**
   - **Localização**: web_search_service.py (Wikipedia API)
   - **Risco**: SSRF se URL maliciosa
   - **Severidade**: Média
   - **Mitigação**: Implementar URL whitelist

2. **Upload de URLs sem whitelist**
   - **Status**: Não implementado
   - **Risco**: SSRF
   - **Severidade**: Alta
   - **Mitigação**: Implementar URL whitelist

#### Código Vulnerável
```python
# web_search_service.py - URL não validada
url = f"https://pt.wikipedia.org/api/rest_v1/page/summary/{query}"
# ❌ Sem validação de query (pode ter injection)
```

---

## 2. CIS BENCHMARKS

### CIS Docker Benchmark
**Score**: 6/10 (🟡 MÉDIO)

#### Compliant
- ✅ User não-root em API container
- ✅ Health checks implementados
- ✅ Read-only root filesystem (parcial)

#### Non-Compliant
- ❌ Root user em web container
- ❌ Sem security options (no-new-privileges)
- ❌ Sem resource limits (exceto Ollama)
- ❌ Sem apparmor profile
- ❌ Sem seccomp profile

#### Recomendações
```dockerfile
# Adicionar ao Dockerfile.api
USER app
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

```yaml
# Adicionar ao docker-compose.yml
security_opt:
  - no-new-privileges:true
  - seccomp:./seccomp-profile.json
read_only: true
tmpfs:
  - /tmp
```

---

### CIS PostgreSQL Benchmark
**Score**: N/A (não auditado)

#### Recomendações
- Implementar autenticação cert-based
- Desativar conexões não-SSL
- Implementar row-level security
- Configurar log_min_duration_statement
- Implementar pgAudit extension

---

### CIS Redis Benchmark
**Score**: N/A (não auditado)

#### Recomendações
- Implementar AUTH obrigatório
- Desativar comandos perigosos (FLUSHDB, CONFIG)
- Implementar TLS
- Implementar ACLs

---

## 3. VULNERABILIDADES ESPECÍFICAS

### Hardcoded Secrets
**Ocorrências**: 15+ arquivos

#### Lista de Arquivos
1. config.py - localhost hardcoded
2. docker-compose.yml - localhost hardcoded
3. .env.example - localhost hardcoded
4. scripts/*.py - localhost hardcoded
5. apps/api/conftest.py - localhost hardcoded
6. apps/web/next.config.js - localhost hardcoded
7. apps/web/hooks/useWebSocket.ts - localhost hardcoded
8. infra/ci-cd/ci.yml - localhost hardcoded
9. infra/monitoring/*.yml - localhost hardcoded

#### Exemplos
```python
# config.py
database_url: str = "postgresql+asyncpg://ledger:ledger_dev_pass@localhost:5432/ledger_ai"
# ❌ Hardcoded localhost
```

```yaml
# docker-compose.yml
NEXT_PUBLIC_API_URL: http://localhost:8000
# ❌ Hardcoded localhost
```

**Mitigação**: Usar variáveis de ambiente em todos os lugares

---

### CORS Issues
**Ocorrências**: 2 locais

#### next.config.js
```javascript
headers: [
  { key: "Access-Control-Allow-Origin", value: "*" }, // ❌ Perigoso
]
```

#### main.py
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,  # ✅ Melhor
    allow_credentials=True,
)
```

**Mitigação**: Remover CORS do next.config.js, usar apenas no backend

---

### Sensitive Data in Logs
**Ocorrências**: Possível

#### Análise
- Logs podem conter tokens, passwords, dados de clientes
- Não há sanitização de logs
- Logs são enviados para Loki (centralizados)

**Mitigação**: Implementar log sanitization (redact secrets)

---

## 4. RECOMENDAÇÕES DE SEGURANÇA

### Imediatas (1-2 semanas)
1. **Remover CORS permissivo** do next.config.js
2. **Adicionar autenticação WebSocket** com JWT
3. **Proteger endpoints de infra** (/health, /metrics)
4. **Desativar docs em produção**
5. **Setar cookie_secure=True** em produção
6. **Remover debug ports** do docker-compose.prod.yml

### Curtas (1-2 meses)
1. **Implementar secrets manager** (AWS Secrets, Vault)
2. **Implementar rate locking** em login
3. **Implementar 2FA** (TOTP)
4. **Implementar refresh token JWT**
5. **Automatizar SCA** (pip-audit, npm audit)
6. **Aumentar log retention** para 7 anos

### Médias (2-3 meses)
1. **Implementar HSTS**
2. **Implementar SIEM integration**
3. **Implementar alertas de security events**
4. **Implementar URL whitelist** (SSRF prevention)
5. **Implementar CIS Docker benchmarks**
6. **Implementar log sanitization**

### Longas (3-6 meses)
1. **Implementar CIS PostgreSQL benchmarks**
2. **Implementar CIS Redis benchmarks**
3. **Implementar assinatura digital** em relatórios
4. **Implementar row-level security** no PostgreSQL
5. **Implementar pgAudit extension**
6. **Implementar TLS** em todas as conexões

---

## 5. MATRIZ DE RISCOS

| Vulnerabilidade | Probabilidade | Impacto | Risco | Prioridade |
|-----------------|---------------|---------|-------|------------|
| WebSocket sem auth | Alta | Alta | 🔴 Crítico | P0 |
| CORS permissivo | Alta | Alta | 🔴 Crítico | P0 |
| Secrets em .env | Média | Alta | 🟡 Alto | P0 |
| Rate limiting fallback | Média | Alta | 🟡 Alto | P1 |
| Login sem lockout | Alta | Média | 🟡 Alto | P1 |
| Sem 2FA | Baixa | Alta | 🟡 Alto | P1 |
| Debug ports expostos | Média | Média | 🟡 Médio | P1 |
| Docs expostos | Média | Média | 🟡 Médio | P2 |
| Cookie insecure | Baixa | Alta | 🟡 Médio | P2 |
| Sem refresh token | Média | Baixa | 🟢 Baixo | P2 |
| SSRF (web search) | Baixa | Média | 🟢 Baixo | P2 |
| Dependências vulneráveis | Média | Média | 🟡 Médio | P2 |
| Logs incompletos | Alta | Baixa | 🟢 Baixo | P3 |
| Log retention insuficiente | Baixa | Alta | 🟡 Médio | P3 |

---

## CONCLUSÃO DE SEGURANÇA

O sistema possui **boas práticas de segurança** (RBAC, JWT, rate limiting) mas tem **vulnerabilidades críticas** que precisam ser corrigidas imediatamente:

1. **WebSocket sem autenticação** - risco de acesso não autorizado
2. **CORS permissivo** - risco de CSRF e data exfiltration
3. **Secrets em .env** - risco de exposição de credenciais
4. **Rate limiting fallback** - risco de DoS em multi-instance

**Score Segurança: 65/100** (🟡 MÉDIO)

Com as correções prioritárias, pode atingir **85/100** em 2-3 meses.
