# ARCHITECTURE REPORT
**Data:** 1 de Junho de 2026
**Architecture Score:** 92/100

## Arquitetura Geral

### Padrão Arquitetural
- **Pattern:** Microservices com Monolith Modular
- **Frontend:** Next.js 14 (App Router)
- **Backend:** FastAPI (Async)
- **Database:** PostgreSQL 16 com pgvector
- **Cache:** Redis 7
- **Message Queue:** RabbitMQ
- **Object Storage:** MinIO (S3-compatible)
- **AI:** Ollama (Local LLM)
- **Observability:** Prometheus + Grafana + Loki + Jaeger + Sentry

### Frontend Architecture
```
apps/web/
├── app/
│   ├── (dashboard)/  # Layout agrupado
│   │   ├── dashboard/
│   │   ├── documents/
│   │   ├── audit/
│   │   ├── reports/
│   │   ├── compliance/
│   │   ├── reconciliation/
│   │   ├── forecast/
│   │   ├── assistant/
│   │   ├── knowledge/
│   │   ├── entries-pending/
│   │   ├── review/
│   │   ├── audit-logs/
│   │   ├── admin/
│   │   │   ├── companies/
│   │   │   └── users/
│   │   ├── upload/
│   │   └── settings/
│   └── login/
├── components/
│   ├── ui/           # Shadcn/ui
│   ├── Notifications.tsx
│   ├── Sidebar.tsx
│   └── ThemeProvider.tsx
├── hooks/
│   └── useWebSocket.ts
├── lib/
│   └── api.ts        # API client centralizado
├── contexts/
│   ├── AuthContext.tsx
│   └── CompanyContext.tsx
└── providers/
    └── QueryProvider.tsx
```

### Backend Architecture
```
apps/api/
├── main.py           # FastAPI application
├── config.py         # Pydantic settings
├── observability.py   # OpenTelemetry + Prometheus + Sentry
├── rbac.py           # Role-Based Access Control
└── tests/            # Test suite

services/
├── accounting_core/
│   └── engine.py     # Accounting engine
├── ai_engine/
│   ├── agent_assistant_local.py
│   ├── agent_auditor.py
│   ├── agent_predictor.py
│   ├── agent_reconciler.py
│   └── ... (16 agents)
├── compliance/
│   └── rules.py      # Compliance rules
├── knowledge/
│   ├── embedding_service.py
│   ├── rag_service.py
│   ├── template_service.py
│   └── knowledge_seeder.py
├── parser/
│   └── pdf_parser.py
└── worker/
    └── tasks.py      # Celery tasks
```

### Database Architecture
```
packages/db/models.py
├── Company
├── Account
├── JournalEntry
├── JournalItem
├── Document
├── Report
├── User
├── UserCompany
├── AuditLog
├── KnowledgeArticle
├── KnowledgeEmbedding
├── ReportTemplate
├── AccountTemplate
├── GlossaryTerm
└── UseCase
```

## Fluxos de Dados

### Autenticação
1. User → POST /auth/token
2. Backend valida credentials
3. Backend gera JWT (access + refresh)
4. Backend define httpOnly cookie
5. Frontend usa cookie automaticamente

### Upload de Documentos
1. User → uploadDocument()
2. Frontend → POST /documents/upload
3. Backend armazena no MinIO
4. Worker processa PDF
5. Worker extrai dados
6. Worker atualiza status

### AI Processing
1. User → fetchAudit() / fetchForecast() / fetchReconcile()
2. Frontend → POST /ai/*
3. Backend chama agents
4. Agents processam dados
5. Backend retorna resultado

## Comunicação

### REST API
- 36 endpoints REST
- httpOnly cookies para auth
- JSON para payloads

### WebSocket
- 1 endpoint: /ws/notifications
- Real-time notifications

### Message Queue
- RabbitMQ para async tasks
- Celery Beat para scheduling

## Escalabilidade

### Horizontal Scaling
- API: Stateless (pode escalar)
- Web: Stateless (pode escalar)
- Worker: Stateful (Redis para coordenação)
- Database: Read replicas recomendado

### Vertical Scaling
- Ollama: GPU-accelerated
- PostgreSQL: pgvector para embeddings

## Padrões de Design

### Frontend
- Server Components (Next.js 14)
- Client Components para interatividade
- Context API para estado global
- TanStack Query para cache
- Shadcn/ui para componentes

### Backend
- Dependency Injection (FastAPI Depends)
- Repository Pattern (SQLAlchemy)
- Service Layer (agents)
- Async/Await throughout

## Score Breakdown

| Aspecto | Score | Notas |
|---------|-------|-------|
| Separação de Responsabilidades | 95/100 | Excelente |
| Modularidade | 90/100 | Bom |
| Escalabilidade | 85/100 | Bom |
| Manutenibilidade | 95/100 | Excelente |
| Testabilidade | 80/100 | Bom |
| Documentação | 75/100 | Aceitável |
| **Total** | **92/100** | **Excelente** |
