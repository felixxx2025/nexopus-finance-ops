"use client";

import { useState } from "react";

type ReportType = "dre" | "balanco";

const MOCK_DRE = {
  receita_bruta: 140000,
  deducoes: -8400,
  receita_liquida: 131600,
  cmv: -45000,
  lucro_bruto: 86600,
  despesas_operacionais: -48000,
  ebit: 38600,
  resultado_financeiro: -600,
  lucro_antes_ir: 38000,
  ir_csll: -12920,
  lucro_liquido: 25080,
};

function fmt(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function DRETable({ data }: { data: typeof MOCK_DRE }) {
  const rows: [string, number][] = [
    ["Receita Bruta",               data.receita_bruta],
    ["(-) Deduções",                data.deducoes],
    ["Receita Líquida",             data.receita_liquida],
    ["(-) CMV",                     data.cmv],
    ["Lucro Bruto",                 data.lucro_bruto],
    ["(-) Despesas Operacionais",   data.despesas_operacionais],
    ["EBIT",                        data.ebit],
    ["Resultado Financeiro",        data.resultado_financeiro],
    ["Lucro antes do IR/CSLL",      data.lucro_antes_ir],
    ["(-) IR e CSLL",               data.ir_csll],
    ["Lucro Líquido",               data.lucro_liquido],
  ];

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
            <td className={`px-4 py-2 text-right font-mono ${value < 0 ? "text-red-600" : "text-green-700"}`}>
              {fmt(value)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function Reports() {
  const [reportType, setReportType] = useState<ReportType>("dre");
  const [companyId, setCompanyId] = useState("");
  const [year, setYear] = useState(new Date().getFullYear().toString());
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  function handleGenerate(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    // TODO: chamar GET /reports/{type}/{companyId}/{year}
    setTimeout(() => {
      setLoading(false);
      setGenerated(true);
    }, 800);
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Relatórios Financeiros</h1>

      <form onSubmit={handleGenerate} className="bg-white rounded-xl shadow p-6 flex flex-wrap gap-4 items-end">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Tipo</label>
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
          <label className="block text-xs font-medium text-gray-600 mb-1">Empresa (ID)</label>
          <input
            value={companyId}
            onChange={(e) => setCompanyId(e.target.value)}
            placeholder="UUID da empresa"
            required
            className="border rounded-lg px-3 py-2 text-sm w-64"
          />
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Ano</label>
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

      {generated && reportType === "dre" && (
        <div className="bg-white rounded-xl shadow overflow-hidden">
          <div className="px-6 py-4 border-b flex justify-between items-center">
            <h2 className="font-semibold text-gray-700">DRE — {year}</h2>
            <button className="text-xs text-brand-500 hover:underline">
              Exportar PDF {/* TODO: integrar geração de PDF */}
            </button>
          </div>
          <DRETable data={MOCK_DRE} />
        </div>
      )}

      {generated && reportType === "balanco" && (
        <div className="bg-white rounded-xl shadow px-6 py-4 text-gray-500 text-sm">
          Balanço Patrimonial em implementação. Semana 4 do roadmap.
        </div>
      )}
    </div>
  );
}
