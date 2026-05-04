# Nexopus Finance Ops — ledger-ai

Plataforma de contabilidade inteligente com geração automática de DRE, Balanço Patrimonial e relatórios financeiros via IA.

## Stack

| Camada      | Tecnologia                     |
|-------------|--------------------------------|
| Frontend    | Next.js 14 + Tailwind CSS      |
| Backend     | FastAPI                        |
| Banco       | PostgreSQL + SQLAlchemy        |
| Cache       | Redis                          |
| Fila        | Celery + RabbitMQ              |
| IA          | OpenAI / LLM local             |
| Storage     | S3 / MinIO                     |

## Estrutura

```
apps/       → web (Next.js) + api (FastAPI)
services/   → parser, ai-engine, accounting-core, compliance, worker
packages/   → db, types, utils
infra/      → docker, k8s, ci-cd
docs/       → documentação técnica
```

## Início rápido

```bash
# Backend
cd apps/api
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd apps/web
npm install
npm run dev
```

## Roadmap MVP

- **Semana 1** — Setup backend + DB + upload de arquivos
- **Semana 2** — Parser PDF básico
- **Semana 3** — Geração de DRE simples
- **Semana 4** — UI mínima + export PDF
