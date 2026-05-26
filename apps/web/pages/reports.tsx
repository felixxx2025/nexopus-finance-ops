"use client";

import { useRouter } from "next/router";
import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { fetchBalance, fetchDRE } from "../lib/api";

type ReportType = "dre" | "balanco";

type DREData = Record<string, number>;
type BalanceData = {
  ativo: Record<string, number>;
  passivo: Record<string, number>;
  pl: Record<string, number>;
  totais: { ativo: number; passivo: number; pl: number };
  equacao_fecha: boolean;
};

function fmt(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function DRETable({ data }: { data: DREData }) {
  const LABELS: Record<string, string> = {
    receita_bruta: "Receita Bruta",
    deducoes: "(-) Deduções",
    receita_liquida: "Receita Líquida",
    cmv: "(-) CMV",
    lucro_bruto: "Lucro Bruto",
    despesas_operacionais: "(-) Despesas Operacionais",
    ebit: "EBIT",
    resultado_financeiro: "Resultado Financeiro",
    lucro_antes_ir: "Lucro antes do IR/CSLL",
    ir_csll: "(-) IR e CSLL",
    lucro_liquido: "Lucro Líquido",
  };

  const rows = Object.entries(LABELS).map(
    ([key, label]) => [label, data[key] ?? 0] as [string, number],
  );

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="bg-brand-900 text-white">
          <th className="text-left px-4 py-2">Descrição</th>
          <th className="text-right px-4 py-2">Valor</th>
        </tr>
      </thead>
      <tbody>
        {rows.map(([label, value], i) => (
          <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
            <td className="px-4 py-2 text-gray-700">{label}</td>
            <td
              className={`px-4 py-2 text-right font-mono ${value < 0 ? "text-red-600" : "text-green-700"}`}
            >
              {fmt(value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function BalanceTable({ data }: { data: BalanceData }) {
  const Section = ({
    title,
    items,
  }: {
    title: string;
    items: Record<string, number>;
  }) => (
    <div>
      <h3 className="font-semibold text-gray-700 px-4 py-2 bg-gray-100">
        {title}
      </h3>
      {Object.entries(items).map(([name, value], i) => (
        <div
          key={i}
          className={`flex justify-between px-4 py-2 text-sm ${i % 2 === 0 ? "bg-white" : "bg-gray-50"}`}
        >
          <span className="text-gray-700">{name}</span>
          <span className="font-mono text-green-700">{fmt(value)}</span>
        </div>
      ))}
    </div>
  );

  return (
    <div className="space-y-4">
      <Section title="Ativo" items={data.ativo} />
      <Section title="Passivo" items={data.passivo} />
      <Section title="Patrimônio Líquido" items={data.pl} />
      <div
        className={`px-4 py-3 rounded-lg text-sm font-medium ${data.equacao_fecha ? "bg-green-50 text-green-700 border border-green-200" : "bg-red-50 text-red-700 border border-red-200"}`}
      >
        {data.equacao_fecha
          ? `✓ Equação patrimonial fechada — Ativo: ${fmt(data.totais.ativo)}`
          : `✗ Balanço não fecha — Diferença detectada (Ativo: ${fmt(data.totais.ativo)}, Passivo+PL: ${fmt(data.totais.passivo + data.totais.pl)})`}
      </div>
    </div>
  );
}

export default function Reports() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [reportType, setReportType] = useState<ReportType>("dre");
  const [companyId, setCompanyId] = useState("");
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dreData, setDreData] = useState<DREData | null>(null);
  const [balanceData, setBalanceData] = useState<BalanceData | null>(null);

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push("/login");
  }, [isAuthenticated, authLoading, router]);

  if (authLoading) return null;

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setDreData(null);
    setBalanceData(null);

    try {
      if (reportType === "dre") {
        const res = await fetchDRE(companyId, parseInt(year, 10));
        setDreData(res.data as DREData);
      } else {
        const res = await fetchBalance(companyId, parseInt(year, 10));
        setBalanceData(res.data);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao gerar relatório");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">
        Relatórios Financeiros
      </h1>

      <form
        onSubmit={handleGenerate}
        className="bg-white rounded-xl shadow p-6 flex flex-wrap gap-4 items-end"
      >
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Tipo
          </label>
          <select
            value={reportType}
            onChange={(e) => setReportType(e.target.value as ReportType)}
            className="border rounded-lg px-3 py-2 text-sm"
          >
            <option value="dre">DRE</option>
            <option value="balanco">Balanço Patrimonial</option>
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Empresa (ID)
          </label>
          <input
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            placeholder="UUID da empresa"
            required
            className="border rounded-lg px-3 py-2 text-sm w-64"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">
            Ano
          </label>
          <input
            type="number"
            value={year}
            onChange={(e) => setYear(e.target.value)}
            min={2000}
            max={2099}
            required
            className="border rounded-lg px-3 py-2 text-sm w-24"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="py-2 px-5 bg-brand-500 text-white font-semibold rounded-lg hover:bg-brand-900
                     transition-colors disabled:opacity-50"
        >
          {loading ? "Gerando…" : "Gerar"}
        </button>
      </form>

      {error && (
        <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </p>
      )}

      {dreData && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-700">DRE — {year}</h2>
          </div>
          <DRETable data={dreData} />
        </div>
      )}

      {balanceData && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <div className="px-6 py-4 border-b">
            <h2 className="font-semibold text-gray-700">
              Balanço Patrimonial — {year}
            </h2>
          </div>
          <div className="p-4">
            <BalanceTable data={balanceData} />
          </div>
        </div>
      )}
    </div>
  );
}
