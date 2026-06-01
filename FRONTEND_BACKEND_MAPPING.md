# FRONTEND BACKEND MAPPING
**Data:** 1 de Junho de 2026

## Mapeamento Completo de Endpoints

### Auth Endpoints (4)
| Backend | Frontend | Status |
|----------|----------|--------|
| POST /auth/token | login() | ✅ |
| POST /auth/refresh | refreshToken() | ✅ |
| POST /auth/logout | logout() | ✅ |
| GET /auth/me | me() | ✅ |

### Infra Endpoints (2)
| Backend | Frontend | Status |
|----------|----------|--------|
| GET /health | healthCheck() | ✅ |
| GET /ready | readyCheck() | ✅ |

### Companies Endpoints (5)
| Backend | Frontend | Status |
|----------|----------|--------|
| POST /companies | createCompany() | ✅ |
| PATCH /companies/{id} | updateCompany() | ✅ |
| DELETE /companies/{id} | deleteCompany() | ✅ |
| GET /companies | fetchCompanies() | ✅ |
| POST /companies/{id}/seed-accounts | seedCompanyAccounts() | ✅ |

### Documents Endpoints (6)
| Backend | Frontend | Status |
|----------|----------|--------|
| POST /documents/upload | uploadDocument() | ✅ |
| GET /documents | fetchDocuments() | ✅ |
| GET /documents/{id} | fetchDocument() | ✅ |
| POST /documents | createDocument() | ✅ |
| PUT /documents/{id} | updateDocument() | ✅ |
| DELETE /documents/{id} | deleteDocument() | ✅ |

### Entries Endpoints (3)
| Backend | Frontend | Status |
|----------|----------|--------|
| PATCH /entries/{id}/review | reviewEntry() | ✅ |
| GET /entries/pending | fetchPendingEntries() | ✅ |
| GET /entries/approved | fetchApprovedEntries() | ✅ |

### Compliance Endpoints (1)
| Backend | Frontend | Status |
|----------|----------|--------|
| GET /compliance | fetchCompliance() | ✅ |

### Reports Endpoints (3)
| Backend | Frontend | Status |
|----------|----------|--------|
| GET /reports/dre/{id}/{year} | fetchDRE() | ✅ |
| GET /reports/balance/{id}/{year} | fetchBalance() | ✅ |
| PATCH /reports/{id}/approve | approveReport() | ✅ |

### AI Endpoints (4)
| Backend | Frontend | Status |
|----------|----------|--------|
| POST /ai/forecast | fetchForecast() | ✅ |
| POST /ai/audit | fetchAudit() | ✅ |
| POST /ai/assistant | streamAssistant() | ✅ |
| POST /ai/reconcile | fetchReconcile() | ✅ |

### Admin Endpoints (5)
| Backend | Frontend | Status |
|----------|----------|--------|
| GET /admin/audit-logs | fetchAuditLogs() | ✅ |
| GET /admin/users | fetchUsers() | ✅ |
| POST /admin/users | createUser() | ✅ |
| PATCH /admin/users/{username} | updateUser() | ✅ |
| PATCH /admin/users/{username}/deactivate | deactivateUser() | ✅ |
| POST /admin/knowledge/seed | seedKnowledge() | ✅ |

### Knowledge Endpoints (6)
| Backend | Frontend | Status |
|----------|----------|--------|
| POST /knowledge/search | searchKnowledge() | ✅ |
| POST /knowledge/articles | createKnowledgeArticle() | ✅ |
| PUT /knowledge/articles/{id} | updateKnowledgeArticle() | ✅ |
| DELETE /knowledge/articles/{id} | deleteKnowledgeArticle() | ✅ |
| POST /knowledge/upload | uploadKnowledgePDF() | ✅ |
| GET /knowledge/articles/{id} | fetchKnowledgeArticle() | ✅ |
| GET /knowledge/articles | fetchKnowledgeArticles() | ✅ |
| GET /templates/reports | fetchReportTemplates() | ✅ |
| GET /templates/accounts | fetchAccountTemplates() | ✅ |

### WebSocket (1)
| Backend | Frontend | Status |
|----------|----------|--------|
| WS /ws/notifications | useWebSocket() | ✅ |

## Resumo
- Total Backend Endpoints: 37 (36 REST + 1 WebSocket)
- Total Frontend Functions: 37
- Coverage: 100%
- Divergências: 0
- Endpoints Órfãos: 0
