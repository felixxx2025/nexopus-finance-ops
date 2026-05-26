-- =============================================================
-- Nexopus Finance Ops — Schema PostgreSQL
-- Referência: Lei nº 6.404/1976 + NBC TG 26
-- =============================================================
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
-- -------------------------------------------------------------
-- companies
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  cnpj VARCHAR(14) NOT NULL UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- -------------------------------------------------------------
-- accounts (plano de contas)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  code VARCHAR(20) NOT NULL,
  name TEXT NOT NULL,
  type VARCHAR(20) NOT NULL CHECK (
    type IN ('ativo', 'passivo', 'receita', 'despesa', 'pl')
  ),
  parent_id UUID REFERENCES accounts(id),
  UNIQUE (company_id, code)
);
-- -------------------------------------------------------------
-- journal_entries (cabeçalho dos lançamentos)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_entries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  description TEXT
);
-- -------------------------------------------------------------
-- journal_items (partidas de débito/crédito)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id UUID NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
  account_id UUID NOT NULL REFERENCES accounts(id),
  type VARCHAR(10) NOT NULL CHECK (type IN ('debit', 'credit')),
  amount NUMERIC(14, 2) NOT NULL CHECK (amount > 0)
);
-- -------------------------------------------------------------
-- documents (arquivos enviados)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  file_url TEXT NOT NULL,
  original_filename TEXT,
  type VARCHAR(20) NOT NULL CHECK (type IN ('pdf', 'excel', 'sped')),
  status VARCHAR(20) NOT NULL DEFAULT 'uploaded'
    CHECK (status IN ('uploaded','processing','processed','failed','needs_review')),
  parsed BOOLEAN NOT NULL DEFAULT FALSE,
  error_message TEXT,
  ai_confidence NUMERIC(4,3),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- -------------------------------------------------------------
-- reports (DRE, Balanço etc.)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL CHECK (type IN ('dre', 'balanco')),
  year INT NOT NULL,
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (company_id, type, year)
);
-- -------------------------------------------------------------
-- users (usuários do sistema — RBAC)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username VARCHAR(100) NOT NULL UNIQUE,
  email VARCHAR(255) UNIQUE,
  password_hash TEXT NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'viewer'
    CHECK (role IN ('admin','analista','viewer')),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- -------------------------------------------------------------
-- user_companies (vínculo usuário ↔ empresa)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_companies (
  user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  role VARCHAR(20) NOT NULL DEFAULT 'viewer'
    CHECK (role IN ('admin','analista','viewer')),
  PRIMARY KEY (user_id, company_id)
);
-- -------------------------------------------------------------
-- audit_logs (trilha de auditoria)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE SET NULL,
  username VARCHAR(100),
  action VARCHAR(50) NOT NULL,
  entity_type VARCHAR(50),
  entity_id UUID,
  company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
  metadata JSONB DEFAULT '{}',
  ip_address VARCHAR(45),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- -------------------------------------------------------------
-- journal_entries: campos de revisão humana
-- -------------------------------------------------------------
ALTER TABLE journal_entries
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'approved'
    CHECK (status IN ('draft','approved','rejected')),
  ADD COLUMN IF NOT EXISTS review_note TEXT,
  ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
  ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS ai_generated BOOLEAN NOT NULL DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS ai_confidence NUMERIC(4,3),
  ADD COLUMN IF NOT EXISTS created_by VARCHAR(100),
  ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now();
-- -------------------------------------------------------------
-- reports: versionamento e aprovação
-- -------------------------------------------------------------
ALTER TABLE reports
  ADD COLUMN IF NOT EXISTS version INT NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS status VARCHAR(20) NOT NULL DEFAULT 'preliminary'
    CHECK (status IN ('preliminary','approved','closed')),
  ADD COLUMN IF NOT EXISTS approved_by VARCHAR(100),
  ADD COLUMN IF NOT EXISTS approved_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
-- Índices de performance
CREATE INDEX IF NOT EXISTS idx_journal_entries_company_date ON journal_entries(company_id, date);
CREATE INDEX IF NOT EXISTS idx_journal_items_entry ON journal_items(entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_items_account ON journal_items(account_id);
CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_company_type_year ON reports(company_id, type, year);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_audit_logs_username ON audit_logs(username);
CREATE INDEX IF NOT EXISTS idx_audit_logs_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_journal_entries_status ON journal_entries(status);