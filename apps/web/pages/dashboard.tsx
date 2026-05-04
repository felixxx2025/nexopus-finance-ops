"use client";

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";

const mockData = [
  { mes: "Jan", receita: 120000, despesa: 85000, lucro: 35000 },
  { mes: "Fev", receita: 135000, despesa: 90000, lucro: 45000 },
  { mes: "Mar", receita: 98000,  despesa: 88000, lucro: 10000 },
  { mes: "Abr", receita: 152000, despesa: 95000, lucro: 57000 },
  { mes: "Mai", receita: 140000, despesa: 102000, lucro: 38000 },
];

const alerts = [
  { id: 1, type: "warning", message: "Despesas operacionais acima de 70% da receita em Março." },
  { id: 2, type: "info",    message: "DRE de Abril disponível para exportação." },
];

function KPICard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className={`rounded-xl p-5 text-white ${color} shadow`}>
      <p className="text-sm opacity-80">{label}</p>
      <p className="text-2xl font-bold mt-1">{value}</p>
    </div>
  );
}

export default function Dashboard() {
  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-gray-800">Dashboard Financeiro</h1>

      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <KPICard label="Receita Total (Maio)" value="R$ 140.000" color="bg-brand-500" />
        <KPICard label="Despesas (Maio)"       value="R$ 102.000" color="bg-amber-500" />
        <KPICard label="Lucro Líquido (Maio)"  value="R$ 38.000"  color="bg-green-600" />
      </div>

      {/* Gráfico */}
      <div className="bg-white rounded-xl shadow p-6">
        <h2 className="text-lg font-semibold text-gray-700 mb-4">Receita vs Despesa vs Lucro</h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={mockData}>
            <XAxis dataKey="mes" />
            <YAxis tickFormatter={(v) => `${(v / 1000).toFixed(0)}k`} />
            <Tooltip formatter={(v: number) => `R$ ${v.toLocaleString("pt-BR")}`} />
            <Legend />
            <Bar dataKey="receita" fill="#1a6fd4" name="Receita" />
            <Bar dataKey="despesa" fill="#f59e0b" name="Despesas" />
            <Bar dataKey="lucro"   fill="#16a34a" name="Lucro" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Alertas IA */}
      <div className="space-y-2">
        <h2 className="text-lg font-semibold text-gray-700">Alertas IA</h2>
        {alerts.map((a) => (
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
    </div>
  );
}
