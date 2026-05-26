/**
 * API client centralizado.
 * Usa httpOnly cookies (credentials: "include") para autenticação.
 * O token JWT nunca é armazenado em JavaScript — trafega apenas via cookie httpOnly.
 */

const API_URL = "/api";

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
