# FASE 1 - CONTRACT-FIRST VALIDATION
**Data:** 1 de Junho de 2026

## Backend Endpoints (36 REST + 1 WebSocket)

### Auth (4)
- ✅ POST /auth/token → login()
- ✅ POST /auth/refresh → **FALTA** (não implementado no frontend)
- ✅ POST /auth/logout → logout()
- ✅ GET /auth/me → me()

### Infra (2)
- ✅ GET /health → **FALTA** (não exposto no frontend)
- ✅ GET /ready → **FALTA** (não exposto no frontend)

### Companies (5)
- ❌ POST /companies → **FALTA** (não implementado no frontend)
- ❌ PATCH /companies/{company_id} → **FALTA** (não implementado no frontend)
- ❌ DELETE /companies/{company_id} → **FALTA** (não implementado no frontend)
- ✅ GET /companies → fetchCompanies (CompanyContext)
- ✅ POST /companies/{company_id}/seed-accounts → seedCompanyAccounts()

### Documents (6)
- ✅ POST /documents/upload → uploadDocument()
- ✅ GET /documents → fetchDocuments()
- ✅ GET /documents/{document_id} → fetchDocument()
- ✅ POST /documents → createDocument()
- ✅ PUT /documents/{document_id} → updateDocument()
- ✅ DELETE /documents/{document_id} → deleteDocument()

### Entries (3)
- ❌ PATCH /entries/{entry_id}/review → **FALTA** (não implementado no frontend - usa /entries/{id}/approve e /entries/{id}/reject)
- ✅ GET /entries/pending → fetchPendingEntries()
- ✅ GET /entries/approved → fetchApprovedEntries()

### Compliance (1)
- ✅ GET /compliance → fetchCompliance()

### Reports (3)
- ✅ GET /reports/dre/{company_id}/{year} → fetchDRE()
- ✅ GET /reports/balance/{company_id}/{year} → fetchBalance()
- ❌ PATCH /reports/{report_id}/approve → **FALTA** (não implementado no frontend)

### AI (4)
- ✅ POST /ai/forecast → fetchForecast()
- ✅ POST /ai/audit → fetchAudit()
- ✅ POST /ai/assistant → streamAssistant()
- ✅ POST /ai/reconcile → fetchReconcile()

### Admin (5)
- ✅ GET /admin/audit-logs → fetchAuditLogs()
- ✅ GET /admin/users → fetchUsers()
- ❌ POST /admin/users → **FALTA** (não implementado no frontend - usa fetch direto)
- ❌ PATCH /admin/users/{username} → **FALTA** (não implementado no frontend - usa fetch direto)
- ❌ PATCH /admin/users/{username}/deactivate → **FALTA** (não implementado no frontend - usa fetch direto)
- ❌ POST /admin/knowledge/seed → **FALTA** (não implementado no frontend)

### Knowledge (6)
- ✅ POST /knowledge/search → searchKnowledge()
- ✅ POST /knowledge/articles → createKnowledgeArticle()
- ✅ PUT /knowledge/articles/{article_id} → updateKnowledgeArticle()
- ✅ DELETE /knowledge/articles/{article_id} → deleteKnowledgeArticle()
- ✅ POST /knowledge/upload → uploadKnowledgePDF()
- ✅ GET /knowledge/articles/{article_id} → fetchKnowledgeArticle()
- ✅ GET /knowledge/articles → fetchKnowledgeArticles()
- ✅ GET /templates/reports → fetchReportTemplates()
- ✅ GET /templates/accounts → fetchAccountTemplates()

### WebSocket (1)
- ✅ WS /ws/notifications → useWebSocket()

## Gaps Identificados

### Endpoints Backend sem Frontend (9)
1. POST /auth/refresh
2. GET /health
3. GET /ready
4. POST /companies
5. PATCH /companies/{company_id}
6. DELETE /companies/{company_id}
7. PATCH /entries/{entry_id}/review
8. PATCH /reports/{report_id}/approve
9. POST /admin/knowledge/seed

### Endpoints Frontend sem Backend (0)
Nenhum endpoint órfão encontrado.

### Implementações Diretas no Frontend (3)
1. POST /admin/users (admin/users/page.tsx - fetch direto)
2. PATCH /admin/users/{username} (admin/users/page.tsx - fetch direto)
3. PATCH /admin/users/{username}/deactivate (admin/users/page.tsx - fetch direto)

### Divergências de Contrato (1)
1. Frontend usa /entries/{id}/approve e /entries/{id}/reject, mas backend expõe PATCH /entries/{entry_id}/review

## Status
- Total Backend Endpoints: 37 (36 REST + 1 WebSocket)
- Endpoints Mapeados: 28 (76%)
- Gaps: 9 (24%)
- Divergências: 1
