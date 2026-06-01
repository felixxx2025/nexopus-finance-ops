"use client";

import { ActivityFeed } from "@/components/ActivityFeed";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useCompany } from "@/contexts/CompanyContext";
import { fetchDRE } from "@/lib/api";
import { ResponsiveBar } from "@nivo/bar";
import { ResponsiveLine } from "@nivo/line";
import {
  AlertTriangle,
  ArrowDownRight,
  ArrowUpRight,
  CheckCircle,
  DollarSign,
  Percent,
  TrendingDown,
  TrendingUp,
} from "lucide-react";
import React, { useEffect, useMemo, useState } from "react";

type KPIData = {
  receita_bruta: number;
  receita_liquida: number;
  despesas_operacionais: number;
  ebitda: number;
  lucro_liquido: number;
  margem_liquida: number;
  margem_ebitda: number;
  crescimento_receita: number;
  crescimento_lucro: number;
};

function fmt(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function fmtPct(v: number) {
  return `${v.toFixed(1)}%`;
}

function KPICard({
  label,
  value,
  previousValue,
  trend,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  previousValue?: number;
  trend?: "up" | "down" | "neutral";
  icon: any;
  color: string;
}) {
  const trendIcon = trend === "up" ? ArrowUpRight : trend === "down" ? ArrowDownRight : null;
  const trendColor = trend === "up" ? "text-green-400" : trend === "down" ? "text-red-400" : "text-gray-400";
  const trendValue = previousValue ? ((value.replace(/[^0-9,-]/g, "") as any) - previousValue) / previousValue * 100 : 0;

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-gray-400">{label}</CardTitle>
        <Icon className={`h-4 w-4 ${color}`} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-white">{value}</div>
        {trendIcon && (
          <div className={`flex items-center text-xs ${trendColor} mt-1`}>
            {React.createElement(trendIcon, { className: "h-3 w-3 mr-1" })}
            <span>{Math.abs(trendValue).toFixed(1)}% vs período anterior</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const { selectedCompanyId, selectedYear, selectedCompany } = useCompany();
  const [kpi, setKpi] = useState<KPIData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedCompanyId) {
      loadKPIs();
    }
  }, [selectedCompanyId, selectedYear]);

  async function loadKPIs() {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetchDRE(selectedCompanyId, selectedYear);
      const d = res.data as Record<string, number>;

      const receita_bruta = d.receita_bruta ?? 0;
      const receita_liquida = d.receita_liquida ?? receita_bruta;
      const despesas = Math.abs(d.despesas_operacionais ?? 0);
      const ebitda = receita_liquida - despesas;
      const lucro_liquido = d.lucro_liquido ?? 0;
      const margem_liquida = receita_liquida > 0 ? (lucro_liquido / receita_liquida) * 100 : 0;
      const margem_ebitda = receita_liquida > 0 ? (ebitda / receita_liquida) * 100 : 0;

      setKpi({
        receita_bruta,
        receita_liquida,
        despesas_operacionais: despesas,
        ebitda,
        lucro_liquido,
        margem_liquida,
        margem_ebitda,
        crescimento_receita: 12.5, // Simulado - viria da API
        crescimento_lucro: 8.3, // Simulado - viria da API
      });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Erro ao carregar dados");
    } finally {
      setLoading(false);
    }
  }

  const alerts = useMemo(() => {
    if (!kpi) return [];
    return [
      {
        id: 1,
        type: "warning" as const,
        icon: AlertTriangle,
        message: "Despesas operacionais acima de 70% da receita",
        visible: kpi.despesas_operacionais / kpi.receita_liquida > 0.7,
      },
      {
        id: 2,
        type: "success" as const,
        icon: CheckCircle,
        message: "Margem EBITDA saudável (> 20%)",
        visible: kpi.margem_ebitda > 20,
      },
      {
        id: 3,
        type: "warning" as const,
        icon: TrendingDown,
        message: "Lucro em queda vs período anterior",
        visible: kpi.crescimento_lucro < 0,
      },
    ].filter(a => a.visible);
  }, [kpi]);

  if (!selectedCompany) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-gray-400 text-lg">Selecione uma empresa para visualizar o dashboard</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Dashboard Financeiro</h1>
          <p className="text-gray-400 mt-1">
            {selectedCompany.name} • {selectedYear}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadKPIs} disabled={loading}>
          {loading ? "Atualizando..." : "Atualizar"}
        </Button>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      {loading && !kpi ? (
        <PageSkeleton />
      ) : kpi ? (
        <>
          {/* KPIs Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <KPICard
              label="Receita Bruta"
              value={fmt(kpi.receita_bruta)}
              trend={kpi.crescimento_receita > 0 ? "up" : "down"}
              icon={DollarSign}
              color="text-blue-400"
            />
            <KPICard
              label="Receita Líquida"
              value={fmt(kpi.receita_liquida)}
              trend={kpi.crescimento_receita > 0 ? "up" : "down"}
              icon={DollarSign}
              color="text-indigo-400"
            />
            <KPICard
              label="EBITDA"
              value={fmt(kpi.ebitda)}
              icon={TrendingUp}
              color="text-purple-400"
            />
            <KPICard
              label="Lucro Líquido"
              value={fmt(kpi.lucro_liquido)}
              trend={kpi.crescimento_lucro > 0 ? "up" : "down"}
              icon={DollarSign}
              color="text-green-400"
            />
            <KPICard
              label="Margem Líquida"
              value={fmtPct(kpi.margem_liquida)}
              icon={Percent}
              color="text-emerald-400"
            />
            <KPICard
              label="Margem EBITDA"
              value={fmtPct(kpi.margem_ebitda)}
              icon={Percent}
              color="text-cyan-400"
            />
            <KPICard
              label="Crescimento Receita"
              value={fmtPct(kpi.crescimento_receita)}
              trend={kpi.crescimento_receita > 0 ? "up" : "down"}
              icon={TrendingUp}
              color={kpi.crescimento_receita > 0 ? "text-green-400" : "text-red-400"}
            />
            <KPICard
              label="Crescimento Lucro"
              value={fmtPct(kpi.crescimento_lucro)}
              trend={kpi.crescimento_lucro > 0 ? "up" : "down"}
              icon={TrendingUp}
              color={kpi.crescimento_lucro > 0 ? "text-green-400" : "text-red-400"}
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-lg text-white">Evolução Mensal</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveLine
                    data={[
                      {
                        id: "Receita",
                        data: [
                          { x: "Jan", y: 85000 },
                          { x: "Fev", y: 91000 },
                          { x: "Mar", y: 88000 },
                          { x: "Abr", y: 94000 },
                          { x: "Mai", y: 92000 },
                          { x: "Jun", y: 98000 },
                        ],
                      },
                      {
                        id: "Despesa",
                        data: [
                          { x: "Jan", y: 42000 },
                          { x: "Fev", y: 45000 },
                          { x: "Mar", y: 43000 },
                          { x: "Abr", y: 47000 },
                          { x: "Mai", y: 46000 },
                          { x: "Jun", y: 49000 },
                        ],
                      },
                    ]}
                    margin={{ top: 20, right: 30, bottom: 50, left: 60 }}
                    xScale={{ type: "point" }}
                    yScale={{
                      type: "linear",
                      min: 0,
                      max: "auto",
                    }}
                    yFormat=" >-.2f"
                    curve="monotoneX"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: 0,
                      legend: "Mês",
                      legendOffset: 36,
                      legendPosition: "middle",
                      truncateTickAt: 0,
                    }}
                    axisLeft={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: 0,
                      legend: "Valor (R$)",
                      legendOffset: -40,
                      legendPosition: "middle",
                      truncateTickAt: 0,
                    }}
                    enableGridY={true}
                    enablePoints={true}
                    pointSize={8}
                    pointColor={{ theme: "background" }}
                    pointBorderWidth={2}
                    pointBorderColor={{ from: "serieColor" }}
                    pointLabelYOffset={-12}
                    useMesh={true}
                    legends={[
                      {
                        anchor: "top-right",
                        direction: "column",
                        justify: false,
                        translateX: 0,
                        translateY: 0,
                        itemsSpacing: 0,
                        itemDirection: "left-to-right",
                        itemWidth: 80,
                        itemHeight: 20,
                        itemOpacity: 0.75,
                        symbolSize: 12,
                        symbolShape: "circle",
                        symbolBorderColor: "rgba(0, 0, 0, .5)",
                        effects: [
                          {
                            on: "hover",
                            style: {
                              itemBackground: "rgba(0, 0, 0, .03)",
                              itemOpacity: 1,
                            },
                          },
                        ],
                      },
                    ]}
                    theme={{
                      axis: {
                        ticks: { text: { fill: "#9ca3af" } },
                        legend: { text: { fill: "#9ca3af" } },
                      },
                      grid: { line: { stroke: "#374151" } },
                      legends: { text: { fill: "#e5e7eb" } },
                      tooltip: { container: { background: "#1f2937", color: "#e5e7eb" } },
                    }}
                    colors={["#6366f1", "#ef4444"]}
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-lg text-white">Composição de Despesas</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-80">
                  <ResponsiveBar
                    data={[
                      { categoria: "Pessoal", valor: 180000 },
                      { categoria: "Operacional", valor: 95000 },
                      { categoria: "Marketing", valor: 45000 },
                      { categoria: "TI", valor: 35000 },
                      { categoria: "Outros", valor: 25000 },
                    ]}
                    keys={["valor"]}
                    indexBy="categoria"
                    margin={{ top: 20, right: 30, bottom: 50, left: 60 }}
                    padding={0.3}
                    valueScale={{ type: "linear" }}
                    valueFormat=" >-.2f"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: 0,
                      legend: "Categoria",
                      legendOffset: 36,
                      legendPosition: "middle",
                      truncateTickAt: 0,
                    }}
                    axisLeft={{
                      tickSize: 5,
                      tickPadding: 5,
                      tickRotation: 0,
                      legend: "Valor (R$)",
                      legendOffset: -40,
                      legendPosition: "middle",
                      truncateTickAt: 0,
                    }}
                    enableGridY={true}
                    labelSkipWidth={12}
                    labelSkipHeight={12}
                    labelTextColor={{
                      from: "color",
                      modifiers: [["darker", 1.6]],
                    }}
                    theme={{
                      axis: {
                        ticks: { text: { fill: "#9ca3af" } },
                        legend: { text: { fill: "#9ca3af" } },
                      },
                      grid: { line: { stroke: "#374151" } },
                      labels: { text: { fill: "#e5e7eb" } },
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Activity Feed */}
          <ActivityFeed />

          {/* Alerts */}
          {alerts.length > 0 && (
            <Card className="bg-gray-900 border-gray-800">
              <CardHeader>
                <CardTitle className="text-lg text-white">Alertas e Insights</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {alerts.map((alert) => (
                    <div
                      key={alert.id}
                      className={`flex items-center gap-3 p-3 rounded-lg ${alert.type === "warning"
                        ? "bg-yellow-900/20 border border-yellow-700"
                        : "bg-green-900/20 border border-green-700"
                        }`}
                    >
                      <alert.icon
                        className={`h-5 w-5 ${alert.type === "warning" ? "text-yellow-400" : "text-green-400"
                          }`}
                      />
                      <span className="text-sm text-gray-300">{alert.message}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <EmptyState
          icon="file"
          title="Nenhum dado disponível"
          description="Selecione uma empresa e período para visualizar os dados do dashboard."
          action={{
            label: "Atualizar",
            onClick: loadKPIs,
          }}
        />
      )}
    </div>
  );
}
