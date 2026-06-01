# Nexopus Finance Ops

Plataforma de contabilidade inteligente para PMEs brasileiras: geração automática de DRE, Balanço Patrimonial e relatórios financeiros com IA, RBAC, trilha de auditoria e fluxo de revisão humana.

## Stack

| Camada          | Tecnologia                                          |
| --------------- | --------------------------------------------------- |
| Frontend        | Next.js 14 + Tailwind CSS + TypeScript              |
| Backend         | FastAPI 0.115 + SQLAlchemy Async (asyncpg)          |
| Auth            | JWT Bearer + httpOnly cookie + Redis blacklist      |
| RBAC            | Roles: admin / analista / viewer                    |
| Banco           | PostgreSQL 16 + Alembic migrations                  |
| Cache           | Redis 7 (rate limiting + token blacklist)           |
| Fila            | Celery 5 + RabbitMQ                                 |
| IA              | Meta-Llama-3.1-405B via Azure Inference             |
| Storage         | MinIO (S3-compatible)                               |
| Observabilidade | Prometheus + Grafana + Loki + Sentry + OTLP         |
| Testes          | pytest + pytest-asyncio (93 testes · 100% passing)  |
| CI/CD           | GitHub Actions                                      |

## Estrutura

```
apps/
  api/          → FastAPI: auth, RBAC, upload, reports, audit, AI endpoints
  web/          → Next.js: login, dashboard, upload, reports, review, onboarding
services/
  accounting_core/  → AccountingEngine (DRE NBC TG 26, Balanço Lei 6404)
  ai_engine/        → agent_parser, classifier, generator + AIController (fallback/confiança)
  compliance/       → validate_balance, validate_double_entry, validate_cnpj
  parser/           → pdf_parser (pdfplumber)
  worker/           → Celery tasks (process_document, generate_report)
packages/
  db/           → SQLAlchemy models + schema.sql
infra/
  docker/       → Dockerfile.api, Dockerfile.web, Dockerfile.worker
  ci-cd/        → GitHub Actions CI pipeline
```

## Início rápido (Docker)

```bash
# 1. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais reais (OPENAI_API_KEY, etc.)

# 2. Subir toda a stack
docker compose up --build

# Serviços disponíveis (apenas expostos):
# → API:       http://localhost:8000/docs
# → Frontend:  http://localhost:3000
# → MinIO Console (debug): http://localhost:9001
# → RabbitMQ Management (debug): http://localhost:15672
#
# Serviços internos (sem exposição externa):
# → postgres, redis, prometheus, grafana, loki, jaeger, flower
#   acessíveis apenas via rede Docker nexopus-internal
```

## Início rápido (local)

```bash
# Backend
cd apps/api
pip install -r requirements.txt
export $(cat ../../.env | xargs)   # ou defina DATABASE_URL manualmente
uvicorn main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

## Autenticação

A API usa JWT Bearer. Obter token:

```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "<ADMIN_PASSWORD>"}'
```

Use o `access_token` retornado como `Authorization: Bearer <token>` em todas as requisições.

## Endpoints principais

### Auth
| Método  | Endpoint          | Role  | Descrição                        |
| ------- | ----------------- | ----- | -------------------------------- |
| `POST`  | `/auth/token`     | —     | Login → JWT + cookie httpOnly    |
| `POST`  | `/auth/refresh`   | —     | Renova access token via refresh token |
| `POST`  | `/auth/logout`    | any   | Invalida token (Redis blacklist) |
| `GET`   | `/auth/me`        | any   | Dados do usuário corrente        |

### Documentos
| Método  | Endpoint                     | Role              | Descrição                      |
| ------- | ---------------------------- | ----------------- | ------------------------------ |
| `POST`  | `/documents/upload`          | admin / analista  | Upload PDF/XLSX (magic bytes)  |
| `GET`   | `/documents`                 | any               | Lista documentos da empresa    |
| `GET`   | `/documents/{id}`            | any               | Detalhes de documento          |
| `POST`  | `/documents`                 | admin / analista  | Cria documento manualmente     |
| `PUT`   | `/documents/{id}`            | admin / analista  | Atualiza status/metadados      |
| `DELETE`| `/documents/{id}`            | admin             | Exclui documento               |

### Lançamentos
| Método  | Endpoint                     | Role              | Descrição                      |
| ------- | ---------------------------- | ----------------- | ------------------------------ |
| `GET`   | `/entries/pending`           | any               | Lançamentos pendentes de revisão |
| `PATCH` | `/entries/{id}/review`       | admin / analista  | Aprovar ou rejeitar lançamento |

### Relatórios
| Método  | Endpoint                             | Role   | Descrição           |
| ------- | ------------------------------------ | ------ | ------------------- |
| `GET`   | `/reports/dre/{company_id}/{year}`   | any    | DRE (NBC TG 26)     |
| `GET`   | `/reports/balance/{company_id}/{year}` | any  | Balanço (Lei 6404)  |
| `PATCH` | `/reports/{id}/approve`              | admin  | Aprovar relatório   |

### Empresas / Onboarding
| Método  | Endpoint                                | Role  | Descrição                           |
| ------- | --------------------------------------- | ----- | ----------------------------------- |
| `POST`  | `/companies`                            | admin | Cria empresa + seed plano de contas |
| `GET`   | `/companies`                            | any   | Lista empresas                      |
| `PATCH` | `/companies/{id}`                       | admin | Atualiza empresa                    |
| `DELETE`| `/companies/{id}`                       | admin | Exclui empresa                      |
| `POST`  | `/companies/{id}/seed-accounts`         | admin | Semeia plano de contas NBC TG       |

### IA / Nexopus Copilot
| Método  | Endpoint        | Role | Descrição                                     |
| ------- | --------------- | ---- | --------------------------------------------- |
| `POST`  | `/ai/assistant` | any  | Assistente financeiro com streaming SSE e RAG |
| `POST`  | `/ai/forecast`  | any  | Forecast de caixa 30/60/90 dias               |
| `POST`  | `/ai/audit`     | any  | Auditoria automática de lançamentos           |
| `POST`  | `/ai/reconcile` | any  | Conciliação bancária automática               |

### Admin
| Método  | Endpoint                       | Role  | Descrição                              |
| ------- | ------------------------------ | ----- | -------------------------------------- |
| `GET`   | `/admin/audit-logs`            | admin | Trilha completa de ações               |
| `GET`   | `/admin/users`                 | admin | Lista usuários ativos/inativos do banco |
| `POST`  | `/admin/users`                 | admin | Cria usuário com role validada         |
| `PATCH` | `/admin/users/{username}`      | admin | Atualiza usuário com role validada     |
| `PATCH` | `/admin/users/{username}/deactivate` | admin | Desativa usuário                 |

### Infra
| Método | Endpoint   | Descrição                        |
| ------ | ---------- | -------------------------------- |
| `GET`  | `/health`  | Health + versão                  |
| `GET`  | `/ready`   | Readiness (DB + Redis)           |
| `GET`  | `/metrics` | Prometheus metrics               |
| `WS`   | `/ws/{u}`  | WebSocket notificações real-time |

## Pipeline de processamento de documentos

```
POST /documents/upload?company_id=<uuid>
  → validação magic bytes (PDF/XLSX)
  → upload MinIO/S3
  → Document.status = "uploaded" → DB
  → Celery: process_document.delay(doc_id)

Celery worker:
  → Document.status = "processing"
  → download do MinIO
  → agent_parser + AIController (confiança + fallback)
  → agent_classifier → agent_generator
  → compliance: validate_double_entry
  → _persist_entries (journal_entries + journal_items)
  → Document.status = "processed" | "needs_review" | "failed"
  → generate_report.delay(company_id, year, "dre")
  → generate_report.delay(company_id, year, "balanco")
```

## RBAC

Usuários podem ser configurados via `EXTRA_USERS_JSON` e também persistidos na tabela `users`.
Os endpoints administrativos de usuários validam roles contra a matriz oficial (`admin`,
`analista`, `viewer`) e usam a dependência `get_db`, facilitando testes e troca de sessão.

| Permissão         | admin | analista | viewer |
| ----------------- | :---: | :------: | :----: |
| read              | ✓     | ✓        | ✓      |
| write / upload    | ✓     | ✓        | —      |
| ai:run            | ✓     | ✓        | —      |
| reports:generate  | ✓     | ✓        | —      |
| admin:manage      | ✓     | —        | —      |
| audit:read        | ✓     | ✓        | ✓      |

## Testes

### Backend (API)

```bash
python3 -m pip install -r apps/api/requirements.txt
python3 -m pytest apps/api/tests -v
```

Suítes:
- `test_health.py` — health / versão / Swagger
- `test_auth.py` — login, JWT, cookie, RBAC de rota
- `test_compliance.py` — CNPJ, partida dobrada, equação patrimonial
- `test_engine.py` — motor contábil (DRE, Balanço)
- `test_fase1_pipeline.py` — upload, estados, magic bytes, RBAC
- `test_fase2_security.py` — roles, logout, cookie, observabilidade
- `test_fase3_engine_ai.py` — plano de contas, AIController, fallback

### Frontend (unitários)

```bash
cd apps/web
npm run test:unit
```

### Frontend (e2e com Playwright)

Os testes e2e requerem a infraestrutura completa (API + banco + Redis + etc.):

```bash
# Inicia todos os serviços (postgres, redis, rabbitmq, minio, api, web)
docker-compose up -d

# Aguarda os serviços ficarem saudáveis
docker-compose ps

# Roda os testes e2e
cd apps/web
npm run test:e2e
```

### Última execução local registrada

```bash
# Backend
./venv/bin/python -m pytest apps/api/tests/test_fase2_security.py -q
# 23 passed, 1 warning

./venv/bin/python -m pytest apps/api/tests -q
# 148 passed, 1 warning

# Frontend unitários
npx vitest run components/__tests__ lib/__tests__
# Test Files  3 passed (3)
# Tests  8 passed (8)
```

## Variáveis de ambiente

Veja [.env.example](.env.example). Variáveis críticas:

| Variável                            | Descrição                                 |
| ----------------------------------- | ----------------------------------------- |
| `SECRET_KEY`                        | Chave JWT (mín. 32 chars)                 |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Credenciais iniciais                      |
| `DATABASE_URL`                      | PostgreSQL async URL (asyncpg)            |
| `GITHUB_TOKEN`                      | Token para Azure AI Inference (LLaMA)     |
| `REDIS_URL`                         | Redis (rate limiting + blacklist)         |
| `S3_ENDPOINT` / `S3_ACCESS_KEY`     | MinIO/S3 credentials                      |
| `SENTRY_DSN`                        | Sentry (opcional, produção)               |
| `ALLOWED_ORIGINS`                   | CORS origins (vírgula-separados)          |

## Compliance contábil

- **Partida Dobrada** (Lei nº 6.404/1976)
- **Equação Patrimonial**: Ativo = Passivo + PL
- **DRE** conforme NBC TG 26: IR/CSLL 34% sobre lucro tributável
- **Validação de CNPJ** (algoritmo RFB)
- **Plano de contas** padrão NBC TG com 5 grupos hierárquicos
- **Somente lançamentos approved** entram nos cálculos

## Nexopus Copilot

Assistente de contabilidade brasileira com RAG (Retrieval-Augmented Generation) híbrido.

### Base de Conhecimento

Conteúdo coberto:
- Lei nº 6.404/1976 (Lei das S.A.) — estrutura do Balanço e DRE
- NBC TG 26 — Apresentação das Demonstrações Contábeis
- Partida Dobrada e Equação Patrimonial
- Plano de Contas Padrão NBC TG
- IRPJ e CSLL (impostos sobre lucro)
- Glossário contábil (200+ termos)
- Templates de relatórios por setor
- Casos de uso práticos

### Arquitetura RAG

- **Embeddings:** Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2) - 100% local
- **Busca Semântica:** PostgreSQL + pgvector com índice HNSW
- **Busca Lexical:** PostgreSQL tsvector com GIN index
- **Web Search:** Wikipedia API como fallback (quando resultados locais insuficientes)
- **Combinação:** Reranking híbrido (semantic + lexical + web)

### Uso

**API:**
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "O que é DRE?"}'
```

**Frontend:**
- Botão flutuante no canto inferior direito
- Chat com histórico de mensagens
- Exibição de fontes relevantes da base de conhecimento
- Streaming de respostas em tempo real

### Fases implementadas

### Fase 1 — Estabilização técnica ✅
- Saneamento do worker (sem duplicatas)
- Pipeline de documentos com estados (uploaded → processing → processed/failed/needs_review)
- Configuração centralizada via `config.py` (pydantic-settings)
- Migração Alembic `002` com novos campos

### Fase 2 — Segurança e auditoria ✅
- RBAC admin / analista / viewer em todos os endpoints
- JWT blacklist via Redis no logout
- Cookie httpOnly no login
- `audit_logs` em todas as ações críticas
- Fluxo de revisão humana (`/entries/{id}/review`)
- Validação de magic bytes no upload
- Logs estruturados JSON (Loki/Promtail) via `observability.py`

### Fase 3 — Motor robusto e IA controlada ✅
- Plano de contas NBC TG (35 contas, seed automático no onboarding)
- Motor filtra somente `status='approved'`, com breakdown por conta
- `AIController` com threshold de confiança, decisão auto/review/reject, fallback
- `AIDecisionLog` auditável por operação
- Telas frontend: onboarding de empresa, revisão de lançamentos

### Fase 4 — Base de Conhecimento Contábil com RAG ✅
- PostgreSQL + pgvector para embeddings e busca semântica
- **Sentence Transformers (HuggingFace)** para embeddings locais - 100% gratuito, sem OpenAI
- Modelo: paraphrase-multilingual-MiniLM-L12-v2 (384 dimensions, multilíngue)
- Base de conhecimento com normas brasileiras (NBC TG, CPC, Lei 6.404/76)
- Glossário contábil com 200+ termos
- Templates de relatórios (DRE, Balanço) e planos de contas por setor
- RAG híbrido (semântico + lexical) para contexto enriquecido no chat
- Web Search (Wikipedia API) como fallback para resultados insuficientes
- Componente de chat flutuante reutilizável no frontend
- Auto-seed no startup (development) - sem necessidade de API keys externas
- Endpoint `/admin/knowledge/seed` para popular base inicial
- Integração RAG no `agent_assistant_local.py` para respostas mais precisas

### Fase 5 — Otimizações de Performance ✅
- **Backend:** Adição de `limit()` em queries SQL para evitar carregamento excessivo
- **Backend:** Uso de `selectinload()` para evitar problema N+1 em relacionamentos
- **Backend:** Índices PostgreSQL otimizados (idx_journal_entries_company_date, idx_journal_items_entry, etc.)
- **Frontend:** Adição de `useMemo()` para otimizar re-renders em componentes pesados
- **Frontend:** Lazy loading do componente Notifications via `dynamic()`
- **Frontend:** TanStack Query configurado com staleTime de 5 minutos para cache
- **Infraestrutura:** Rate limiting configurado em endpoints críticos (10/minute, 5/minute, 20/minute)
