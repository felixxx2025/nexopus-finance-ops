/**
 * Página de Forecast — Previsão de Fluxo de Caixa com IA (30/60/90 dias)
 * Agente: Claude Sonnet 4.6
 */
"use client";

import { fetchForecast } from "@/lib/api";
import { useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const RISK_COLORS: Record<string, string> = {
  baixo: "text-green-400",
  medio: "text-yellow-400",
  alto: "text-orange-400",
  critico: "text-red-400",
};

const fmt = (v: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(v);

function KPICard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string;
  icon: string;
  color: string;
}) {
  return (
    <div className={`bg-gray-900 rounded-xl p-4 border-l-4 ${color}`}>
      <div className="text-2xl mb-1">{icon}</div>
      <div className="text-xs text-gray-400 mb-1">{label}</div>
      <div className="text-lg font-bold text-white capitalize">{value}</div>
    </div>
  );
}

interface ForecastResult {
  tendencia?: {
    receita: string;
    despesa: string;
    margem_liquida_media: number;
  };
  projecao: {
    [key: string]: {
      [key: string]: {
        receita: number;
        despesa: number;
        resultado: number;
      } | any;
    };
  };
  monthly_data: Array<{
    mes: string;
    receita: number;
    despesa: number;
    resultado: number;
  }>;
  alertas: string[];
  recomendacoes: string[];
  narrativa: string;
  confianca?: number;
  [key: string]: any;
}

export default function ForecastPage() {
  const { selectedCompanyId, companies } = useCompany();
  const [loading, setLoading] = useState(false);
  const [loadingEntries, setLoadingEntries] = useState(false);
  const [data, setData] = useState<ForecastResult | null>(null);
  const [error, setError] = useState("");
  const [scenario, setScenario] = useState<"otimista" | "base" | "pessimista">(
    "base",
  );
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

  async function runForecast() {
    if (!selectedCompanyId) {
      setError("Selecione uma empresa para gerar o forecast.");
      return;
    }

    if (entries.length === 0) {
      setError("Não há lançamentos aprovados para gerar o forecast.");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const company = companies.find(c => c.id === selectedCompanyId);
      const result = await fetchForecast(entries, company?.name || "Empresa");
      setData(result);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao gerar previsão.");
    } finally {
      setLoading(false);
    }
  }

  const projectionChartData = data
    ? ["30_dias", "60_dias", "90_dias"].map((period) => {
      const s = data.projecao?.[period]?.[scenario] || {};
      return {
        period: period.replace("_dias", "d"),
        receita: s.receita || 0,
        despesa: s.despesa || 0,
        resultado: s.resultado || 0,
      };
    })
    : [];

  const historicalData = data?.monthly_data || [];

  return (
    <div className="space-y-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">
          📈 Forecast de Fluxo de Caixa
        </h1>
        <p className="text-gray-400">
          Previsão inteligente para 30, 60 e 90 dias com IA (Claude Sonnet
          4.6)
        </p>
      </div>

      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={runForecast}
          disabled={loading}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold py-2 px-6 rounded-lg transition-colors"
        >
          {loading ? "⏳ Gerando previsão..." : "🤖 Gerar Forecast com IA"}
        </button>
        {data && (
          <div className="flex gap-2">
            {(["otimista", "base", "pessimista"] as const).map((s) => (
              <button
                key={s}
                onClick={() => setScenario(s)}
                className={`py-1 px-4 rounded-lg text-sm font-medium transition-colors ${scenario === s
                  ? "bg-indigo-600 text-white"
                  : "bg-gray-800 text-gray-300 hover:bg-gray-700"
                  }`}
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </button>
            ))}
          </div>
        )}
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 mb-6 text-red-300">
          {error}
        </div>
      )}

      {data && (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            <KPICard
              label="Tendência Receita"
              value={data.tendencia?.receita || "—"}
              icon="📊"
              color={
                data.tendencia?.receita === "crescimento"
                  ? "border-green-500"
                  : data.tendencia?.receita === "queda"
                    ? "border-red-500"
                    : "border-yellow-500"
              }
            />
            <KPICard
              label="Tendência Despesa"
              value={data.tendencia?.despesa || "—"}
              icon="💸"
              color={
                data.tendencia?.despesa === "crescimento"
                  ? "border-red-500"
                  : "border-green-500"
              }
            />
            <KPICard
              label="Margem Líquida"
              value={`${(data.tendencia?.margem_liquida_media || 0).toFixed(1)}%`}
              icon="📉"
              color="border-indigo-500"
            />
            <KPICard
              label="Confiança IA"
              value={`${((data.confianca || 0) * 100).toFixed(0)}%`}
              icon="🤖"
              color="border-purple-500"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4 text-white">
                Projeção — Cenário {scenario}
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={projectionChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="period" stroke="#9CA3AF" />
                  <YAxis
                    stroke="#9CA3AF"
                    tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(v: number) => fmt(v)}
                    contentStyle={{
                      background: "#111827",
                      border: "1px solid #374151",
                    }}
                  />
                  <Legend />
                  <Bar
                    dataKey="receita"
                    fill="#6366F1"
                    name="Receita"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="despesa"
                    fill="#EF4444"
                    name="Despesa"
                    radius={[4, 4, 0, 0]}
                  />
                  <Bar
                    dataKey="resultado"
                    fill="#10B981"
                    name="Resultado"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-lg font-semibold mb-4 text-white">
                Histórico Mensal
              </h2>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={historicalData}>
                  <defs>
                    <linearGradient id="recGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="#6366F1"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor="#6366F1"
                        stopOpacity={0}
                      />
                    </linearGradient>
                    <linearGradient id="despGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop
                        offset="5%"
                        stopColor="#EF4444"
                        stopOpacity={0.3}
                      />
                      <stop
                        offset="95%"
                        stopColor="#EF4444"
                        stopOpacity={0}
                      />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="mes" stroke="#9CA3AF" />
                  <YAxis
                    stroke="#9CA3AF"
                    tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    formatter={(v: number) => fmt(v)}
                    contentStyle={{
                      background: "#111827",
                      border: "1px solid #374151",
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="receita"
                    stroke="#6366F1"
                    fill="url(#recGrad)"
                    name="Receita"
                  />
                  <Area
                    type="monotone"
                    dataKey="despesa"
                    stroke="#EF4444"
                    fill="url(#despGrad)"
                    name="Despesa"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {data.alertas?.length > 0 && (
              <div className="bg-gray-900 rounded-xl p-6 border border-yellow-700">
                <h3 className="text-lg font-semibold text-yellow-400 mb-3">
                  ⚠️ Alertas
                </h3>
                <ul className="space-y-2">
                  {data.alertas.map((a: string, i: number) => (
                    <li
                      key={i}
                      className="text-gray-300 text-sm flex items-start gap-2"
                    >
                      <span className="text-yellow-400 mt-0.5">•</span> {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {data.recomendacoes?.length > 0 && (
              <div className="bg-gray-900 rounded-xl p-6 border border-green-700">
                <h3 className="text-lg font-semibold text-green-400 mb-3">
                  ✅ Recomendações
                </h3>
                <ul className="space-y-2">
                  {data.recomendacoes.map((r: string, i: number) => (
                    <li
                      key={i}
                      className="text-gray-300 text-sm flex items-start gap-2"
                    >
                      <span className="text-green-400 mt-0.5">•</span> {r}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {data.narrativa && (
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h3 className="text-lg font-semibold text-white mb-3">
                📝 Análise Narrativa (IA)
              </h3>
              <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                {data.narrativa}
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}


