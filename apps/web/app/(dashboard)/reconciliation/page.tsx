/**
 * Página de Conciliação Bancária — Match automático OFX vs. Lançamentos
 * Agente: Meta-LLaMA 3.1 405B
 */
"use client";

import { useCompany } from "@/contexts/CompanyContext";
import { fetchApprovedEntries, fetchReconcile } from "@/lib/api";
import { useEffect, useState } from "react";

const STATUS_STYLES: Record<string, { badge: string; row: string }> = {
  CONCILIADO: {
    badge: "bg-green-900/40 text-green-400 border-green-700",
    row: "border-green-900/30",
  },
  DIVERGENTE: {
    badge: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
    row: "border-yellow-900/30",
  },
  APENAS_BANCO: {
    badge: "bg-orange-900/40 text-orange-400 border-orange-700",
    row: "border-orange-900/30",
  },
  APENAS_CONTABIL: {
    badge: "bg-blue-900/40 text-blue-400 border-blue-700",
    row: "border-blue-900/30",
  },
};

const fmt = (v: number) =>
  new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(
    v,
  );

function SummaryCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: string;
}) {
  return (
    <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center">
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold ${color}`}>{value ?? "—"}</div>
    </div>
  );
}

interface ReconciliationMatch {
  data?: string;
  descricao_banco?: string;
  descricao_contabil?: string;
  valor_banco?: number;
  valor_contabil?: number;
  status?: string;
  [key: string]: any;
}

interface ReconciliationResult {
  matches: ReconciliationMatch[];
  resumo: {
    conciliados?: number;
    divergentes?: number;
    apenas_banco?: number;
    apenas_contabil?: number;
    total_banco?: number;
    total_contabil?: number;
    taxa_conciliacao?: number;
    [key: string]: any;
  };
  alertas: string[];
  acoes_recomendadas?: string[];
  [key: string]: any;
}

export default function ReconciliationPage() {
  const { selectedCompanyId, companies } = useCompany();
  const [loading, setLoading] = useState(false);
  const [loadingEntries, setLoadingEntries] = useState(false);
  const [data, setData] = useState<ReconciliationResult | null>(null);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("TODOS");
  const [entries, setEntries] = useState<any[]>([]);

  useEffect(() => {
    if (selectedCompanyId) {
      loadEntries();
    }
  }, [selectedCompanyId]);

  async function loadEntries() {
    if (!selectedCompanyId) return;

    try {
      setLoadingEntries(true);
      const result = await fetchApprovedEntries(selectedCompanyId);
      setEntries(result.entries);
    } catch (e) {
      console.error("Error loading entries:", e);
      setError(e instanceof Error ? e.message : "Erro ao carregar lançamentos.");
    } finally {
      setLoadingEntries(false);
    }
  }

  async function runReconcile() {
    if (!selectedCompanyId) {
      setError("Selecione uma empresa para executar a conciliação.");
      return;
    }

    if (entries.length === 0) {
      setError("Não há lançamentos aprovados para conciliar.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const company = companies.find(c => c.id === selectedCompanyId);
      // Converter lançamentos para formato esperado pelo backend
      const bankEntries = entries.map(e => ({
        data: e.date,
        descricao: e.description,
        valor: e.items.reduce((sum: number, item: any) => sum + (item.debit || 0) - (item.credit || 0), 0),
      }));

      const accountingEntries = entries.map(e => ({
        data: e.date,
        descricao: e.description,
        valor: e.items.reduce((sum: number, item: any) => sum + (item.debit || 0) - (item.credit || 0), 0),
        tipo_conta: e.items.some((i: any) => i.credit > 0) ? "receita" : "despesa",
      }));

      const result = await fetchReconcile(
        bankEntries,
        accountingEntries,
        company?.name || "Empresa",
      );
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao executar conciliação.");
    } finally {
      setLoading(false);
    }
  }

  const filteredMatches =
    filter === "TODOS"
      ? data?.matches || []
      : (data?.matches || []).filter((m) => m.status === filter);

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          🏦 Conciliação Bancária
        </h1>
        <p className="text-gray-400">
          Match automático entre extrato bancário e lançamentos contábeis
          (LLaMA 3.1 405B)
        </p>
      </div>

      <button
        onClick={runReconcile}
        disabled={loading}
        className="mb-6 bg-teal-700 hover:bg-teal-600 disabled:opacity-50 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
      >
        {loading ? "⏳ Conciliando..." : "🔄 Executar Conciliação com IA"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-8">
            <SummaryCard
              label="Banco"
              value={data.resumo?.total_banco}
              color="text-blue-400"
            />
            <SummaryCard
              label="Contábil"
              value={data.resumo?.total_contabil}
              color="text-purple-400"
            />
            <SummaryCard
              label="Conciliados"
              value={data.resumo?.conciliados}
              color="text-green-400"
            />
            <SummaryCard
              label="Divergentes"
              value={data.resumo?.divergentes}
              color="text-yellow-400"
            />
            <SummaryCard
              label="Só Banco"
              value={data.resumo?.apenas_banco}
              color="text-orange-400"
            />
            <SummaryCard
              label="Só Contábil"
              value={data.resumo?.apenas_contabil}
              color="text-blue-400"
            />
            <div className="bg-gray-900 rounded-xl p-4 border border-gray-800 text-center col-span-1">
              <div className="text-xs text-gray-400 mb-1">Taxa Conc.</div>
              <div className="text-2xl font-bold text-green-400">
                {data.resumo?.taxa_conciliacao?.toFixed(1)}%
              </div>
            </div>
          </div>

          <div className="flex gap-2 mb-4 flex-wrap">
            {[
              "TODOS",
              "CONCILIADO",
              "DIVERGENTE",
              "APENAS_BANCO",
              "APENAS_CONTABIL",
            ].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${filter === f
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                  }`}
              >
                {f.replace("_", " ")}{" "}
                {f !== "TODOS"
                  ? `(${(data.matches || []).filter((m: any) => m.status === f).length})`
                  : `(${data.matches?.length || 0})`}
              </button>
            ))}
          </div>

          <div className="space-y-2 mb-8">
            {filteredMatches.map((m: any, i: number) => {
              const st =
                STATUS_STYLES[m.status] || STATUS_STYLES["APENAS_BANCO"];
              return (
                <div
                  key={i}
                  className={`bg-gray-900 rounded-xl p-4 border ${st.row}`}
                >
                  <div className="flex items-center justify-between gap-4 flex-wrap">
                    <span
                      className={`text-xs font-bold px-2 py-0.5 rounded-full border ${st.badge}`}
                    >
                      {m.status.replace("_", " ")}
                    </span>

                    <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3 min-w-0">
                      {m.banco && (
                        <div className="text-sm">
                          <div className="text-xs text-gray-500 mb-0.5">
                            🏦 BANCO
                          </div>
                          <div className="text-gray-200 truncate">
                            {m.banco.descricao}
                          </div>
                          <div className="text-xs text-gray-400">
                            {m.banco.data}
                          </div>
                        </div>
                      )}
                      {m.contabil && (
                        <div className="text-sm">
                          <div className="text-xs text-gray-500 mb-0.5">
                            📒 CONTÁBIL
                          </div>
                          <div className="text-gray-200 truncate">
                            {m.contabil.descricao}
                          </div>
                          <div className="text-xs text-gray-400">
                            {m.contabil.data}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="text-right">
                      {m.banco && (
                        <div className="font-bold text-white">
                          {fmt(m.banco.valor || 0)}
                        </div>
                      )}
                      {m.diferenca_valor !== null &&
                        m.diferenca_valor !== undefined && (
                          <div className="text-xs text-yellow-400">
                            Δ {fmt(Math.abs(m.diferenca_valor))}
                          </div>
                        )}
                    </div>
                  </div>

                  {m.observacao && (
                    <div className="mt-2 text-xs text-gray-500">
                      {m.observacao}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {data.alertas?.length > 0 && (
            <div className="bg-orange-900/20 border border-orange-700 rounded-xl p-4">
              <h3 className="text-orange-400 font-semibold mb-2">
                ⚠️ Alertas
              </h3>
              {data.alertas.map((a: string, i: number) => (
                <p key={i} className="text-sm text-gray-300">
                  • {a}
                </p>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}


