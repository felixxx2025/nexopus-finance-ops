"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useCompany } from "@/contexts/CompanyContext";
import { fetchBalance, fetchDRE } from "@/lib/api";
import {
  ColumnDef,
  getCoreRowModel,
  getPaginationRowModel,
  useReactTable
} from "@tanstack/react-table";
import { Download, FileText, Scale } from "lucide-react";
import { useMemo, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

  const rows = useMemo(() => Object.entries(LABELS).map(
    ([key, label]) => ({ label, value: data[key] ?? 0, key }),
  ), [data]);

  const columns: ColumnDef<typeof rows[0]>[] = useMemo(() => [
    {
      accessorKey: "label",
      header: "Descrição",
      cell: ({ row }) => <span className="text-white">{row.original.label}</span>,
    },
    {
      accessorKey: "value",
      header: "Valor",
      cell: ({ row }) => (
        <span
          className={`font-mono text-right ${row.original.value < 0 ? "text-red-400" : "text-green-400"
            }`}
        >
          {fmt(row.original.value)}
        </span>
      ),
    },
  ], []);

  const table = useReactTable({
    data: rows,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="rounded-md border border-gray-700">
      <table className="w-full">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th
                  key={header.id}
                  className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                >
                  {header.column.columnDef.header as string}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id} className="border-t border-gray-800 hover:bg-gray-800/50">
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-4 py-3">
                  {cell.getValue() as React.ReactNode}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function BalanceTable({ data }: { data: BalanceData }) {
  const allItems = [
    ...Object.entries(data.ativo).map(([name, value]) => ({ name, value, section: "Ativo" })),
    ...Object.entries(data.passivo).map(([name, value]) => ({ name, value, section: "Passivo" })),
    ...Object.entries(data.pl).map(([name, value]) => ({ name, value, section: "Patrimônio Líquido" })),
  ];

  const columns: ColumnDef<typeof allItems[0]>[] = [
    {
      accessorKey: "section",
      header: "Seção",
      cell: ({ row }) => <span className="text-gray-400">{row.original.section}</span>,
    },
    {
      accessorKey: "name",
      header: "Conta",
      cell: ({ row }) => <span className="text-white">{row.original.name}</span>,
    },
    {
      accessorKey: "value",
      header: "Valor",
      cell: ({ row }) => (
        <span className="font-mono text-green-400">{fmt(row.original.value)}</span>
      ),
    },
  ];

  const table = useReactTable({
    data: allItems,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
  });

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-gray-700">
        <table className="w-full">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                  >
                    {header.column.columnDef.header as string}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 py-3">
                    {cell.getValue() as React.ReactNode}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div
        className={`px-4 py-3 rounded-lg text-sm font-medium ${data.equacao_fecha
          ? "bg-green-900/20 text-green-400 border border-green-700"
          : "bg-red-900/20 text-red-400 border border-red-700"
          }`}
      >
        {data.equacao_fecha
          ? `✓ Equação patrimonial fechada — Ativo: ${fmt(data.totais.ativo)}`
          : `✗ Balanço não fecha — Diferença detectada (Ativo: ${fmt(data.totais.ativo)}, Passivo+PL: ${fmt(data.totais.passivo + data.totais.pl)})`}
      </div>
    </div>
  );
}

export default function Reports() {
  const { selectedCompanyId, selectedYear, selectedCompany } = useCompany();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dreData, setDreData] = useState<DREData | null>(null);
  const [balanceData, setBalanceData] = useState<BalanceData | null>(null);

  async function loadReports() {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError(null);
    setDreData(null);
    setBalanceData(null);

    try {
      const [dreRes, balanceRes] = await Promise.all([
        fetchDRE(selectedCompanyId, selectedYear).catch(() => null),
        fetchBalance(selectedCompanyId, selectedYear).catch(() => null),
      ]);
      if (dreRes) setDreData(dreRes.data as DREData);
      if (balanceRes) setBalanceData(balanceRes.data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar relatórios");
    } finally {
      setLoading(false);
    }
  }

  const handleExport = async (type: ReportType) => {
    if (!selectedCompanyId) {
      alert("Selecione uma empresa para exportar");
      return;
    }

    try {
      const endpoint = type === "dre"
        ? `${API_URL}/reports/dre/export?company_id=${selectedCompanyId}&year=${selectedYear}`
        : `${API_URL}/reports/balance/export?company_id=${selectedCompanyId}&year=${selectedYear}`;

      const res = await fetch(endpoint, {
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Download the file
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type}_${selectedCompany?.name?.replace(/\s+/g, "_") || "company"}_${selectedYear}.xlsx`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Error exporting report:", err);
      alert(err instanceof Error ? err.message : "Erro ao exportar relatório");
    }
  };

  if (!selectedCompany) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-gray-400 text-lg">Selecione uma empresa para visualizar os relatórios</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Relatórios Financeiros</h1>
          <p className="text-gray-400 mt-1">
            {selectedCompany.name} • {selectedYear}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadReports} disabled={loading}>
            {loading ? "Carregando..." : "Atualizar"}
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("dre")}>
            <Download className="h-4 w-4 mr-2" />
            Exportar DRE
          </Button>
          <Button variant="outline" size="sm" onClick={() => handleExport("balanco")}>
            <Download className="h-4 w-4 mr-2" />
            Exportar Balanço
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      <Tabs defaultValue="dre" className="space-y-4">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="dre" className="data-[state=active]:bg-gray-700">
            <FileText className="h-4 w-4 mr-2" />
            DRE
          </TabsTrigger>
          <TabsTrigger value="balanco" className="data-[state=active]:bg-gray-700">
            <Scale className="h-4 w-4 mr-2" />
            Balanço Patrimonial
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dre">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                Demonstrativo do Resultado do Exercício
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-gray-400">Carregando...</div>
              ) : dreData ? (
                <DRETable data={dreData} />
              ) : (
                <div className="text-center py-8 text-gray-400">
                  Nenhum dado disponível
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="balanco">
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle className="text-lg text-white">
                Balanço Patrimonial
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-8 text-gray-400">Carregando...</div>
              ) : balanceData ? (
                <BalanceTable data={balanceData} />
              ) : (
                <div className="text-center py-8 text-gray-400">
                  Nenhum dado disponível
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
