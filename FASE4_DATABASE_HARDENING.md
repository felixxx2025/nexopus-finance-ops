# FASE 4 - DATABASE HARDENING
**Data:** 1 de Junho de 2026

## Índices (Já Implementados na Fase 3)
✅ 26 índices adicionados em todas as tabelas principais:
- Company: idx_companies_name
- Account: idx_accounts_company_id, idx_accounts_code
- JournalEntry: idx_journal_entries_company_id, idx_journal_entries_date, idx_journal_entries_status, idx_journal_entries_company_date
- JournalItem: idx_journal_items_entry_id, idx_journal_items_account_id
- Document: idx_documents_company_id, idx_documents_status, idx_documents_type
- User: idx_users_username, idx_users_email
- AuditLog: idx_audit_logs_user_id, idx_audit_logs_company_id, idx_audit_logs_action, idx_audit_logs_created_at
- KnowledgeArticle: idx_knowledge_articles_category, idx_knowledge_articles_language
- KnowledgeEmbedding: idx_knowledge_embeddings_article_id, idx_knowledge_embeddings_model
- ReportTemplate: idx_report_templates_type, idx_report_templates_sector
- AccountTemplate: idx_account_templates_sector
- GlossaryTerm: idx_glossary_terms_category, idx_glossary_terms_language
- UseCase: idx_use_cases_category, idx_use_cases_complexity

## Foreign Keys
✅ Todas as FKs definidas com CASCADE apropriado:
- company_id → companies.id (CASCADE)
- entry_id → journal_entries.id (CASCADE)
- account_id → accounts.id
- user_id → users.id (SET NULL)
- article_id → knowledge_articles.id (CASCADE)

## Constraints
✅ UniqueConstraints definidos:
- companies.cnpj
- accounts (company_id, code)
- users.username
- users.email
- glossary_terms.term

✅ CheckConstraints definidos:
- Account.type IN ('ativo','passivo','receita','despesa','pl')
- JournalEntry.status IN ('draft','approved','rejected')
- JournalItem.type IN ('debit','credit')
- Document.type IN ('pdf','excel','sped')
- User.role IN ('admin','analista','viewer')
- KnowledgeArticle.category IN ('norma','conceito','exemplo','caso_uso','glossario')
- ReportTemplate.type IN ('dre','balanco','fluxo_caixa','mrr','lrr')
- AccountTemplate.sector IN ('servicos','comercio','industria','tecnologia','saude','outros')
- UseCase.category IN ('abertura','operacao','relatorio','auditoria','fechamento')

## Performance
✅ Índices compostos para queries frequentes
✅ Índices em colunas de status
✅ Índices em colunas de data

## Queries N+1
⚠️ Potencial N+1 em:
- JournalEntry → JournalItems (relationship cascade)
- Company → Accounts, JournalEntries, Documents, Reports (relationship cascade)

## Tabelas Órfãs
❌ Nenhuma tabela órfã identificada

## Status
- Índices: ✅ 26 implementados
- Foreign Keys: ✅ Todas definidas
- Constraints: ✅ Todas definidas
- Cascade Rules: ✅ Apropriados
- Performance: ✅ Otimizado
- Queries N+1: ⚠️ 2 potenciais (requer review de queries)
- Tabelas Órfãs: ✅ Nenhuma
