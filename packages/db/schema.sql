-- =============================================================
-- Nexopus Finance Ops — Schema PostgreSQL
-- Referência: Lei nº 6.404/1976 + NBC TG 26
-- =============================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- -------------------------------------------------------------
-- companies
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS companies (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT         NOT NULL,
  cnpj        VARCHAR(14)  NOT NULL UNIQUE,
  created_at  TIMESTAMP    NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- accounts (plano de contas)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS accounts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  code        VARCHAR(20)  NOT NULL,
  name        TEXT         NOT NULL,
  type        VARCHAR(20)  NOT NULL CHECK (type IN ('ativo','passivo','receita','despesa','pl')),
  parent_id   UUID         REFERENCES accounts(id),
  UNIQUE (company_id, code)
);

-- -------------------------------------------------------------
-- journal_entries (cabeçalho dos lançamentos)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_entries (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  date        DATE         NOT NULL,
  description TEXT
);

-- -------------------------------------------------------------
-- journal_items (partidas de débito/crédito)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS journal_items (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  entry_id    UUID         NOT NULL REFERENCES journal_entries(id) ON DELETE CASCADE,
  account_id  UUID         NOT NULL REFERENCES accounts(id),
  type        VARCHAR(10)  NOT NULL CHECK (type IN ('debit','credit')),
  amount      NUMERIC(14,2) NOT NULL CHECK (amount > 0)
);

-- -------------------------------------------------------------
-- documents (arquivos enviados)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  file_url    TEXT         NOT NULL,
  type        VARCHAR(20)  NOT NULL CHECK (type IN ('pdf','excel','sped')),
  parsed      BOOLEAN      NOT NULL DEFAULT FALSE,
  created_at  TIMESTAMP    NOT NULL DEFAULT now()
);

-- -------------------------------------------------------------
-- reports (DRE, Balanço etc.)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS reports (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  company_id  UUID         NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
  type        VARCHAR(20)  NOT NULL CHECK (type IN ('dre','balanco')),
  year        INT          NOT NULL,
  data        JSONB        NOT NULL DEFAULT '{}',
  created_at  TIMESTAMP    NOT NULL DEFAULT now(),
  UNIQUE (company_id, type, year)
);

-- Índices de performance
CREATE INDEX IF NOT EXISTS idx_journal_entries_company_date ON journal_entries(company_id, date);
CREATE INDEX IF NOT EXISTS idx_journal_items_entry ON journal_items(entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_items_account ON journal_items(account_id);
CREATE INDEX IF NOT EXISTS idx_documents_company ON documents(company_id);
CREATE INDEX IF NOT EXISTS idx_reports_company_type_year ON reports(company_id, type, year);
