/**
 * API client centralizado.
 * Usa httpOnly cookies (credentials: "include") para autenticação.
 * O token JWT nunca é armazenado em JavaScript — trafega apenas via cookie httpOnly.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { headers: extraHeaders, ...rest } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(extraHeaders as Record<string, string>),
  };

  const res = await fetch(`${API_URL}${path}`, {
    headers,
    credentials: "include", // envia cookie httpOnly automaticamente
    ...rest,
  });

  if (res.status === 401) {
    if (
      typeof window !== "undefined" &&
      window.location.pathname !== "/login"
    ) {
      window.location.href = "/login";
    }
    throw new Error("Sessão expirada. Faça login novamente.");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { detail?: string }).detail ?? `HTTP ${res.status}`,
    );
  }

  if (res.status === 204) return undefined as unknown as T;
  return res.json() as Promise<T>;
}

/** Realiza login — o servidor define o cookie httpOnly automaticamente. */
export async function login(
  username: string,
  password: string,
): Promise<{ username: string; token_type: string }> {
  return request<{
    access_token: string;
    token_type: string;
    username: string;
  }>("/auth/token", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

/** Encerra sessão — revoga token no servidor e limpa o cookie. */
export async function logout(): Promise<void> {
  await request("/auth/logout", { method: "POST" });
}

/** Retorna o usuário autenticado atual (valida cookie no servidor). */
export async function me(): Promise<{ username: string }> {
  return request<{ username: string }>("/auth/me");
}

/** Renova access token usando refresh token. */
export async function refreshToken(refreshToken: string): Promise<{
  access_token: string;
  token_type: string;
  username: string;
  role: string;
}> {
  return request<{
    access_token: string;
    token_type: string;
    username: string;
    role: string;
  }>("/auth/refresh", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${refreshToken}`,
    },
  });
}

/** Upload de documento — cookie é enviado automaticamente. */
export async function uploadDocument(
  file: File,
  companyId?: string,
): Promise<{ doc_id: string; status: string; filename: string }> {
  const formData = new FormData();
  formData.append("file", file);

  const url = companyId
    ? `${API_URL}/documents/upload?company_id=${encodeURIComponent(companyId)}`
    : `${API_URL}/documents/upload`;

  const res = await fetch(url, {
    method: "POST",
    credentials: "include",
    body: formData,
    // Não definir Content-Type — o browser define multipart/form-data + boundary
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Sessão expirada");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { detail?: string }).detail ?? `HTTP ${res.status}`,
    );
  }

  return res.json();
}

/** Lista lançamentos aprovados para uso em auditoria e forecast. */
export async function fetchApprovedEntries(companyId: string) {
  return request<{
    entries: Array<{
      id: string;
      date: string;
      description: string;
      status: string;
      items: Array<{
        account: string;
        debit: number;
        credit: number;
      }>;
      created_at: string;
    }>;
  }>(`/entries/approved?company_id=${encodeURIComponent(companyId)}`);
}

/** Busca status de compliance da empresa. */
export async function fetchCompliance(companyId: string) {
  return request<{
    score: number;
    items: Array<{
      id: string;
      name: string;
      status: string;
      description: string;
    }>;
    errors: {
      cnpj: string[];
      partida_dobrada: Array<{
        entry_id: string;
        date: string;
        description: string;
        debit: number;
        credit: number;
      }>;
      equacao_patrimonial: Array<{
        type: string;
        ativo: number;
        passivo: number;
        pl: number;
        diferenca: number;
      }>;
    };
  }>(`/compliance?company_id=${encodeURIComponent(companyId)}`);
}

/** Busca DRE do ano para a empresa. */
export async function fetchDRE(companyId: string, year: number) {
  return request<{
    company_id: string;
    year: number;
    type: string;
    data: Record<string, number>;
  }>(`/reports/dre/${encodeURIComponent(companyId)}/${year}`);
}

/** Busca Balanço Patrimonial do ano para a empresa. */
export async function fetchBalance(companyId: string, year: number) {
  return request<{
    company_id: string;
    year: number;
    type: string;
    data: {
      ativo: Record<string, number>;
      passivo: Record<string, number>;
      pl: Record<string, number>;
      totais: { ativo: number; passivo: number; pl: number };
      equacao_fecha: boolean;
    };
  }>(`/reports/balance/${encodeURIComponent(companyId)}/${year}`);
}

// ── AI Agents ────────────────────────────────────────────────────────────────

/** Gera previsão de fluxo de caixa (30/60/90 dias, 3 cenários). */
export async function fetchForecast(lancamentos: object[], companyName = "") {
  return request<{
    tendencia: {
      receita: string;
      despesa: string;
      margem_liquida_media: number;
    };
    projecao: Record<
      string,
      { otimista: object; base: object; pessimista: object }
    >;
    alertas: string[];
    recomendacoes: string[];
    narrativa: string;
    monthly_data: Array<{
      mes: string;
      receita: number;
      despesa: number;
      resultado: number;
    }>;
    confianca: number;
  }>("/ai/forecast", {
    method: "POST",
    body: JSON.stringify({ lancamentos, company_name: companyName }),
  });
}

/** Executa auditoria automática sobre lançamentos. */
export async function fetchAudit(
  lancamentos: object[],
  dre?: object,
  balanco?: object,
  companyName = "",
) {
  return request<{
    score_risco: number;
    nivel_risco: string;
    anomalias: Array<{
      tipo: string;
      descricao: string;
      severidade: string;
      lancamento_ref: string | null;
      valor_suspeito: number | null;
      norma_violada: string | null;
      recomendacao: string;
    }>;
    compliance: {
      equacao_patrimonial: boolean;
      partida_dobrada: boolean;
      observacoes: string[];
    };
    resumo_executivo: string;
    acoes_recomendadas: string[];
    confianca: number;
  }>("/ai/audit", {
    method: "POST",
    body: JSON.stringify({
      lancamentos,
      dre,
      balanco,
      company_name: companyName,
    }),
  });
}

/** Executa conciliação bancária automática. */
export async function fetchReconcile(
  bankEntries: object[],
  accountingEntries: object[],
  companyName = "",
) {
  return request<{
    resumo: {
      total_banco: number;
      total_contabil: number;
      conciliados: number;
      divergentes: number;
      apenas_banco: number;
      apenas_contabil: number;
      taxa_conciliacao: number;
    };
    matches: object[];
    alertas: string[];
    acoes_recomendadas: string[];
  }>("/ai/reconcile", {
    method: "POST",
    body: JSON.stringify({
      bank_entries: bankEntries,
      accounting_entries: accountingEntries,
      company_name: companyName,
    }),
  });
}

/** Envia pergunta para o assistente financeiro (streaming SSE). */
export function streamAssistant(
  question: string,
  context: object,
  history: Array<{ role: string; content: string }> = [],
  onChunk: (chunk: string) => void,
  onDone: () => void,
  onError: (err: string) => void,
): void {
  fetch(`${API_URL}/ai/assistant`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, context, history }),
  })
    .then(async (response) => {
      if (!response.ok || !response.body) {
        onError(`HTTP ${response.status}`);
        return;
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split("\n")) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              onDone();
              return;
            }
            onChunk(data);
          }
        }
      }
      onDone();
    })
    .catch((e) => onError(e?.message ?? "Erro desconhecido"));
}

/** Busca logs de auditoria administrativos. */
export async function fetchAuditLogs(params?: {
  limit?: number;
  offset?: number;
  action?: string;
  user?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());
  if (params?.action) queryParams.append("action", params.action);
  if (params?.user) queryParams.append("user", params.user);

  const url = `/admin/audit-logs${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return request<{
    logs: Array<{
      id: string;
      timestamp: string;
      user: string;
      action: string;
      entity: string;
      entity_id: string;
      details: string;
      ip_address: string;
    }>;
    total: number;
  }>(url);
}

/** Busca lista de documentos. */
export async function fetchDocuments(params?: {
  limit?: number;
  offset?: number;
  company_id?: string;
  status?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());
  if (params?.company_id) queryParams.append("company_id", params.company_id);
  if (params?.status) queryParams.append("status", params.status);

  const url = `/documents${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return request<{
    documents: Array<{
      id: string;
      filename: string;
      type: string;
      status: string;
      parsed: boolean;
      error_message: string | null;
      ai_confidence: number | null;
      created_at: string;
    }>;
  }>(url);
}

/** Busca lançamentos pendentes de aprovação. */
export async function fetchPendingEntries(params?: {
  limit?: number;
  offset?: number;
  company_id?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());
  if (params?.company_id) queryParams.append("company_id", params.company_id);

  const url = `/entries/pending${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return request<{
    entries: Array<{
      id: string;
      date: string;
      account: string;
      description: string;
      debit: number;
      credit: number;
      status: string;
      company_id: string;
    }>;
    total: number;
  }>(url);
}

/** Busca lista de usuários administrativos. */
export async function fetchUsers(params?: {
  limit?: number;
  offset?: number;
}) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());

  const url = `/admin/users${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return request<{
    users: Array<{
      username: string;
      email?: string;
      role: string;
      is_active: boolean;
      created_at: string;
    }>;
  }>(url);
}

/** Busca artigos da base de conhecimento. */
export async function fetchKnowledgeArticles(params?: {
  limit?: number;
  offset?: number;
  category?: string;
}) {
  const queryParams = new URLSearchParams();
  if (params?.limit) queryParams.append("limit", params.limit.toString());
  if (params?.offset) queryParams.append("offset", params.offset.toString());
  if (params?.category) queryParams.append("category", params.category);

  const url = `/knowledge/articles${queryParams.toString() ? `?${queryParams.toString()}` : ""}`;
  return request<{
    articles: Array<{
      id: string;
      title: string;
      category: string;
      content: string;
      tags: string[];
      created_at: string;
    }>;
    total: number;
  }>(url);
}

/** Busca artigo específico por ID. */
export async function fetchKnowledgeArticle(articleId: string) {
  return request<{
    id: string;
    title: string;
    category: string;
    subcategory?: string;
    content: string;
    tags: string[];
    source?: string;
    source_url?: string;
    created_at: string;
  }>(`/knowledge/articles/${articleId}`);
}

/** Busca na base de conhecimento. */
export async function searchKnowledge(query: string) {
  return request<{
    results: Array<{
      id: string;
      title: string;
      category: string;
      snippet: string;
      relevance: number;
    }>;
  }>(`/knowledge/search?q=${encodeURIComponent(query)}`);
}

/** Busca templates de relatórios. */
export async function fetchReportTemplates() {
  return request<{
    templates: Array<{
      id: string;
      name: string;
      category: string;
      description: string;
    }>;
  }>("/templates/reports");
}

/** Busca templates de contas. */
export async function fetchAccountTemplates() {
  return request<{
    templates: Array<{
      id: string;
      name: string;
      category: string;
      description: string;
    }>;
  }>("/templates/accounts");
}

/** Faz seed de contas para uma empresa. */
export async function seedCompanyAccounts(companyId: string) {
  return request<{
    success: boolean;
    message: string;
    accounts_created: number;
  }>(`/companies/${companyId}/seed-accounts`, {
    method: "POST",
  });
}

/** Cria nova empresa. */
export async function createCompany(data: {
  name: string;
  cnpj: string;
}) {
  return request<{
    id: string;
    name: string;
    cnpj: string;
    created_at: string;
  }>("/companies", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Atualiza empresa existente. */
export async function updateCompany(
  companyId: string,
  data: {
    name?: string;
    cnpj?: string;
  }
) {
  return request<{
    id: string;
    name: string;
    cnpj: string;
    updated_at: string;
  }>(`/companies/${companyId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Exclui empresa. */
export async function deleteCompany(companyId: string) {
  return request<{ message: string }>(`/companies/${companyId}`, {
    method: "DELETE",
  });
}

/** Cria novo artigo na base de conhecimento. */
export async function createKnowledgeArticle(data: {
  title: string;
  content: string;
  category: string;
  subcategory?: string;
  tags?: string[];
  source?: string;
  source_url?: string;
  language?: string;
}) {
  return request<{ id: string; message: string }>("/knowledge/articles", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Atualiza artigo existente na base de conhecimento. */
export async function updateKnowledgeArticle(
  articleId: string,
  data: {
    title?: string;
    content?: string;
    category?: string;
    subcategory?: string;
    tags?: string[];
    source?: string;
    source_url?: string;
  }
) {
  return request<{ id: string; message: string }>(
    `/knowledge/articles/${articleId}`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    }
  );
}

/** Exclui artigo da base de conhecimento. */
export async function deleteKnowledgeArticle(articleId: string) {
  return request<{ message: string }>(`/knowledge/articles/${articleId}`, {
    method: "DELETE",
  });
}

/** Upload de PDF para base de conhecimento RAG. */
export async function uploadKnowledgePDF(
  file: File,
  title?: string,
  category?: string
) {
  const formData = new FormData();
  formData.append("file", file);
  if (title) formData.append("title", title);
  if (category) formData.append("category", category);

  const res = await fetch(`${API_URL}/knowledge/upload`, {
    method: "POST",
    credentials: "include",
    body: formData,
  });

  if (res.status === 401) {
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Sessão expirada");
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { detail?: string }).detail ?? `HTTP ${res.status}`
    );
  }

  return res.json() as Promise<{ id: string; message: string; title: string }>;
}

/** Cria registro de documento manualmente. */
export async function createDocument(data: {
  company_id: string;
  file_url: string;
  original_filename?: string;
  type: string;
  status?: string;
}) {
  return request<{ id: string; message: string }>("/documents", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Atualiza status e metadados de um documento. */
export async function updateDocument(
  documentId: string,
  data: {
    status?: string;
    error_message?: string;
    ai_confidence?: number;
  }
) {
  return request<{ id: string; message: string }>(
    `/documents/${documentId}`,
    {
      method: "PUT",
      body: JSON.stringify(data),
    }
  );
}

/** Exclui documento. */
export async function deleteDocument(documentId: string) {
  return request<{ message: string }>(`/documents/${documentId}`, {
    method: "DELETE",
  });
}

/** Busca detalhes de um documento específico. */
export async function fetchDocument(documentId: string) {
  return request<{
    id: string;
    company_id: string;
    file_url: string;
    filename: string;
    type: string;
    status: string;
    parsed: boolean;
    error_message: string | null;
    ai_confidence: number | null;
    created_at: string;
    updated_at: string;
  }>(`/documents/${documentId}`);
}

/** Health check endpoint. */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
  return request<{ status: string; service: string; version: string }>("/health");
}

/** Readiness check endpoint. */
export async function readyCheck(): Promise<{ status: string; dependencies: Record<string, string> }> {
  return request<{ status: string; dependencies: Record<string, string> }>("/ready");
}

/** Review entry (approve/reject). */
export async function reviewEntry(entryId: string, data: {
  approved: boolean;
  reviewer_notes?: string;
}) {
  return request<{ id: string; status: string }>(`/entries/${entryId}/review`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Approve report. */
export async function approveReport(reportId: string) {
  return request<{ id: string; approved: boolean; approved_at: string }>(
    `/reports/${reportId}/approve`,
    {
      method: "PATCH",
    }
  );
}

/** Create user (admin). */
export async function createUser(data: {
  username: string;
  email?: string;
  password: string;
  role: string;
}) {
  return request<{
    username: string;
    email?: string;
    role: string;
    created_at: string;
  }>("/admin/users", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Update user (admin). */
export async function updateUser(username: string, data: {
  email?: string;
  role?: string;
}) {
  return request<{
    username: string;
    email?: string;
    role: string;
    updated_at: string;
  }>(`/admin/users/${username}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

/** Deactivate user (admin). */
export async function deactivateUser(username: string) {
  return request<{ username: string; is_active: boolean }>(
    `/admin/users/${username}/deactivate`,
    {
      method: "PATCH",
    }
  );
}

/** Seed knowledge base (admin). */
export async function seedKnowledge() {
  return request<{
    success: boolean;
    message: string;
    articles_created: number;
  }>("/admin/knowledge/seed", {
    method: "POST",
  });
}
