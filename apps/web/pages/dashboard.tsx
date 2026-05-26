"use client";

import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import {
    Bar,
    BarChart,
    Legend,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from "recharts";
import { useAuth } from "../contexts/AuthContext";
import { fetchDRE } from "../lib/api";

const CURRENT_YEAR = new Date().getFullYear();

type ChartPoint = {
  mes: string;
  receita: number;
  despesa: number;
  lucro: number;
};
type KPIData = { receita: number; despesa: number; lucro: number };

const ALERT_RULES = [
  {
    id: 1,
    type: "warning",
    check: (d: KPIData) => d.despesa / d.receita > 0.7,
    message: "Despesas operacionais acima de 70% da receita.",
  },
  {
    id: 2,
    type: "info",
    check: (d: KPIData) => d.lucro > 0,
    message: `DRE de ${CURRENT_YEAR} disponível para exportação.`,
  },
];

function KPICard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  return (
    <div className={`rounded-xl p-5 text-white ${color} shadow`}>
      <p className="text-sm opacity-80">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

function fmt(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function Dashboard() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [companyId, setCompanyId] = useState("");
  const [inputId, setInputId] = useState("");
  const [chartData, setChartData] = useState<ChartPoint[]>([]);
  const [kpi, setKpi] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  if (authLoading) return null;

  async function handleLoad(e: React.FormEvent) {
    e.preventDefault();
    if (!inputId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDRE(inputId.trim(), CURRENT_YEAR);
      const d = res.data as Record<string, number>;
      setCompanyId(inputId.trim());
      setKpi({
        receita: d.receita_bruta ?? 0,
        despesa: Math.abs(d.despesas_operacionais ?? 0),
        lucro: d.lucro_liquido ?? 0,
      });
      setChartData([
        {
          mes: String(CURRENT_YEAR),
          receita: d.receita_bruta ?? 0,
          despesa: Math.abs(d.despesas_operacionais ?? 0),
          lucro: d.lucro_liquido ?? 0,
        },
      ]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  }

  const activeAlerts = kpi ? ALERT_RULES.filter((r) => r.check(kpi)) : [];

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard Financeiro</h1>

      {/* Formulário de empresa */}
      <form onSubmit={handleLoad} className="flex gap-3 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            ID da Empresa (UUID)
          </label>
          <input
            value={inputId}
            onChange={(e) => setInputId(e.target.value)}
            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            required
            className="border rounded-lg px-3 py-2 text-sm w-80 focus:outline-none focus:ring-2 focus:ring-brand-500"
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="py-2 px-4 bg-brand-500 text-white text-sm font-semibold rounded-lg
                     hover:bg-brand-900 transition-colors disabled:opacity-50"
        >
          {loading ? "Carregando…" : "Carregar"}
        </button>
      </form>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {kpi && (
        <>
          {/* KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <KPICard
              label={`Receita Bruta (${CURRENT_YEAR})`}
              value={fmt(kpi.receita)}
              color="bg-brand-500"
            />
            <KPICard
              label={`Despesas (${CURRENT_YEAR})`}
              value={fmt(kpi.despesa)}
              color="bg-amber-500"
            />
            <KPICard
              label={`Lucro Líquido (${CURRENT_YEAR})`}
              value={fmt(kpi.lucro)}
              color="bg-green-600"
            />
          </div>

          {/* Gráfico */}
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-lg font-semibold text-gray-700 mb-4">
              Receita vs Despesa vs Lucro — {CURRENT_YEAR}
            </h2>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={chartData}>
                <XAxis dataKey="mes" />
                <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
                <Tooltip formatter={(v: number) => fmt(v)} />
                <Legend />
                <Bar dataKey="receita" fill="#1a6fd4" name="Receita" />
                <Bar dataKey="despesa" fill="#f59e0b" name="Despesas" />
                <Bar dataKey="lucro" fill="#16a34a" name="Lucro" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Alertas */}
          {activeAlerts.length > 0 && (
            <div className="space-y-2">
              <h2 className="text-lg font-semibold text-gray-700">Alertas</h2>
              {activeAlerts.map((a) => (
                <div
                  key={a.id}
                  className={`rounded-lg px-4 py-3 text-sm ${
                    a.type === "warning"
                      ? "bg-amber-50 border border-amber-300 text-amber-800"
                      : "bg-blue-50 border border-blue-200 text-blue-700"
                  }`}
                >
                  {a.message}
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {!kpi && !loading && (
        <p className="text-sm text-gray-400">
          Informe o ID da empresa acima para visualizar os dados financeiros.
        </p>
      )}
    </div>
  );
}
