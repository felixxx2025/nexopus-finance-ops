# Nexopus Finance Ops

Plataforma de contabilidade inteligente com geração automática de DRE, Balanço Patrimonial e relatórios financeiros via IA (OpenAI GPT-4o-mini).

## Stack

| Camada   | Tecnologia                             |
| -------- | -------------------------------------- |
| Frontend | Next.js 14 + Tailwind CSS + TypeScript |
| Backend  | FastAPI + SQLAlchemy Async             |
| Auth     | JWT Bearer (python-jose)               |
| Banco    | PostgreSQL 16 + SQLAlchemy ORM         |
| Cache    | Redis 7                                |
| Fila     | Celery 5 + RabbitMQ                    |
| IA       | OpenAI GPT-4o-mini                     |
| Storage  | MinIO (S3-compatible)                  |
| Testes   | pytest + pytest-asyncio                |
| CI/CD    | GitHub Actions                         |

## Estrutura

```
apps/
  api/          → FastAPI: auth, upload, reports
  web/          → Next.js: login, dashboard, upload, reports
services/
  accounting_core/  → AccountingEngine (DRE, Balanço)
  ai_engine/        → agent_parser, agent_classifier, agent_generator
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

# Serviços disponíveis:
# → API:       http://localhost:8000/docs
# → Frontend:  http://localhost:3000
# → MinIO:     http://localhost:9001
# → RabbitMQ:  http://localhost:15672
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

| Método | Endpoint                               | Descrição             |
| ------ | -------------------------------------- | --------------------- |
| `GET`  | `/health`                              | Health check          |
| `POST` | `/auth/token`                          | Login → retorna JWT   |
| `POST` | `/documents/upload`                    | Upload PDF/Excel/SPED |
| `GET`  | `/reports/dre/{company_id}/{year}`     | DRE do exercício      |
| `GET`  | `/reports/balance/{company_id}/{year}` | Balanço Patrimonial   |

## Pipeline de processamento de documentos

```
Upload → MinIO (armazenamento) → Celery (fila)
  → agent_parser (extração de texto)
  → agent_classifier (classificação de contas via LLM)
  → agent_generator (geração de lançamentos em partida dobrada)
  → compliance (validate_double_entry)
  → PostgreSQL (journal_entries + journal_items)
  → documents.parsed = True
```

## Testes

```bash
cd apps/api
DATABASE_URL="postgresql+asyncpg://..." \
SECRET_KEY="..." \
ADMIN_USERNAME="admin" \
ADMIN_PASSWORD="admin" \
PYTHONPATH="../../" \
python3 -m pytest -v
# → 37 testes | auth, engine, compliance, health
```

## Variáveis de ambiente

Veja [.env.example](.env.example) para a lista completa. Variáveis críticas:

| Variável                            | Descrição                               |
| ----------------------------------- | --------------------------------------- |
| `SECRET_KEY`                        | Chave de assinatura JWT (mín. 32 chars) |
| `ADMIN_USERNAME` / `ADMIN_PASSWORD` | Credenciais de acesso inicial           |
| `DATABASE_URL`                      | PostgreSQL async URL                    |
| `OPENAI_API_KEY`                    | Chave da API OpenAI                     |
| `ALLOWED_ORIGINS`                   | Origins CORS permitidos                 |

## Compliance contábil

O motor implementa:

- **Partida Dobrada** (Lei nº 6.404/1976): todo débito tem crédito correspondente
- **Equação Patrimonial**: Ativo = Passivo + PL
- **Validação de CNPJ** (algoritmo RFB)
- **Natureza das contas**: ativo/despesa = devedoras; passivo/receita/PL = credoras

## Roadmap MVP

- **Semana 1** — Setup backend + DB + upload de arquivos
- **Semana 2** — Parser PDF básico
- **Semana 3** — Geração de DRE simples
- **Semana 4** — UI mínima + export PDF
