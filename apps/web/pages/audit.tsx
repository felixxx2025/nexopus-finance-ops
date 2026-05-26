/**
 * Página de Auditoria — Detecção de Anomalias e Compliance com IA
 * Agente: Claude Sonnet 4.6 + RAG
 */
import { useState } from "react";
import { fetchAudit } from "../lib/api";

const DEMO_LANCAMENTOS = [
  {
    data: "2026-01-15",
    tipo_conta: "receita",
    valor: 85000,
    descricao: "Receita de serviços Jan",
  },
  {
    data: "2026-01-20",
    tipo_conta: "despesa",
    valor: 42000,
    descricao: "Folha de pagamento Jan",
  },
  {
    data: "2026-02-28",
    tipo_conta: "despesa",
    valor: 999999,
    descricao: "Despesa suspeita round",
  },
  {
    data: "2026-03-05",
    tipo_conta: "receita",
    valor: 88000,
    descricao: "Receita Mar",
  },
  {
    data: "2026-03-18",
    tipo_conta: "despesa",
    valor: 43000,
    descricao: "Despesa operacional Mar",
  },
];

const SEVERITY_STYLES: Record<string, string> = {
  critica: "bg-red-900/40 border-red-500 text-red-300",
  alta: "bg-orange-900/40 border-orange-500 text-orange-300",
  media: "bg-yellow-900/40 border-yellow-500 text-yellow-300",
  baixa: "bg-blue-900/40 border-blue-500 text-blue-300",
};

const RISK_GAUGE: Record<string, string> = {
  baixo: "text-green-400",
  medio: "text-yellow-400",
  alto: "text-orange-400",
  critico: "text-red-400",
};

export default function AuditPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");

  async function runAudit() {
    setLoading(true);
    setError("");
    try {
      const result = await fetchAudit(
        DEMO_LANCAMENTOS,
        undefined,
        undefined,
        "Empresa Demo",
      );
      setData(result);
    } catch (e: any) {
      setError(e?.message || "Erro ao executar auditoria.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-white mb-2">
            🔍 Auditoria Inteligente
          </h1>
          <p className="text-gray-400">
            Detecção de anomalias, fraudes e desvios de compliance (NBC TG / CPC
            / Lei 6.404/76)
          </p>
        </div>

        <button
          onClick={runAudit}
          disabled={loading}
          className="mb-6 bg-red-700 hover:bg-red-600 disabled:opacity-50 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
        >
          {loading ? "⏳ Auditando..." : "🔎 Executar Auditoria com IA"}
        </button>

        {error && (
          <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
            {error}
          </div>
        )}

        {data && (
          <>
            {/* Score de Risco */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 col-span-2 flex items-center gap-6">
                <div className="text-center">
                  <div
                    className={`text-6xl font-black ${RISK_GAUGE[data.nivel_risco] || "text-gray-400"}`}
                  >
                    {data.score_risco ?? "—"}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    Score de Risco (0-100)
                  </div>
                </div>
                <div>
                  <div
                    className={`text-2xl font-bold capitalize ${RISK_GAUGE[data.nivel_risco] || "text-gray-400"}`}
                  >
                    Risco {data.nivel_risco}
                  </div>
                  <div className="text-sm text-gray-400 mt-1">
                    {data.lancamentos_auditados} lançamentos auditados
                  </div>
                  <div className="text-sm text-gray-400">
                    Confiança: {((data.confianca || 0) * 100).toFixed(0)}%
                  </div>
                </div>
              </div>

              <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                <div className="text-xs text-gray-400 mb-2">
                  Equação Patrimonial
                </div>
                <div
                  className={`text-2xl font-bold ${data.compliance?.equacao_patrimonial ? "text-green-400" : "text-red-400"}`}
                >
                  {data.compliance?.equacao_patrimonial ? "✅ OK" : "❌ Falha"}
                </div>
              </div>

              <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
                <div className="text-xs text-gray-400 mb-2">
                  Partida Dobrada
                </div>
                <div
                  className={`text-2xl font-bold ${data.compliance?.partida_dobrada ? "text-green-400" : "text-red-400"}`}
                >
                  {data.compliance?.partida_dobrada ? "✅ OK" : "❌ Falha"}
                </div>
              </div>
            </div>

            {/* Anomalias */}
            {data.anomalias?.length > 0 && (
              <div className="mb-8">
                <h2 className="text-xl font-semibold text-white mb-4">
                  ⚠️ Anomalias Detectadas ({data.anomalias.length})
                </h2>
                <div className="space-y-3">
                  {data.anomalias.map((a: any, i: number) => (
                    <div
                      key={i}
                      className={`rounded-xl p-4 border ${SEVERITY_STYLES[a.severidade] || "bg-gray-900 border-gray-700"}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono bg-black/30 px-2 py-0.5 rounded uppercase">
                              {a.tipo}
                            </span>
                            <span className="text-xs uppercase font-bold">
                              {a.severidade}
                            </span>
                          </div>
                          <p className="text-sm font-medium mb-1">
                            {a.descricao}
                          </p>
                          {a.lancamento_ref && (
                            <p className="text-xs opacity-70">
                              Ref: {a.lancamento_ref}
                            </p>
                          )}
                          {a.norma_violada && (
                            <p className="text-xs opacity-70">
                              Norma: {a.norma_violada}
                            </p>
                          )}
                        </div>
                        {a.valor_suspeito && (
                          <div className="text-right">
                            <div className="text-xs text-gray-400">
                              Valor suspeito
                            </div>
                            <div className="font-bold">
                              {new Intl.NumberFormat("pt-BR", {
                                style: "currency",
                                currency: "BRL",
                              }).format(a.valor_suspeito)}
                            </div>
                          </div>
                        )}
                      </div>
                      {a.recomendacao && (
                        <div className="mt-2 pt-2 border-t border-white/10 text-xs opacity-80">
                          💡 {a.recomendacao}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Ações Recomendadas */}
            {data.acoes_recomendadas?.length > 0 && (
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800 mb-8">
                <h3 className="text-lg font-semibold text-white mb-3">
                  📋 Ações Recomendadas
                </h3>
                <ol className="space-y-2">
                  {data.acoes_recomendadas.map((a: string, i: number) => (
                    <li
                      key={i}
                      className="text-gray-300 text-sm flex items-start gap-2"
                    >
                      <span className="text-indigo-400 font-bold">
                        {i + 1}.
                      </span>{" "}
                      {a}
                    </li>
                  ))}
                </ol>
              </div>
            )}

            {/* Resumo Executivo */}
            {data.resumo_executivo && (
              <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
                <h3 className="text-lg font-semibold text-white mb-3">
                  📝 Resumo Executivo
                </h3>
                <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                  {data.resumo_executivo}
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
