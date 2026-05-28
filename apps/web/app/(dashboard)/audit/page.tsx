/**
 * Página de Auditoria — Detecção de Anomalias e Compliance com IA
 * Agente: Claude Sonnet 4.6 + RAG
 */
"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { fetchAudit } from "@/lib/api";
import { useState } from "react";

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

interface AuditResult {
  score_risco: number;
  nivel_risco: string;
  anomalias: Array<{
    tipo: string;
    descricao: string;
    severidade: string;
    lancamento_ref: string;
    valor_suspeito: number;
    norma_violada: string;
    recomendacao: string;
  }>;
  compliance: {
    equacao_patrimonial: boolean;
    partida_dobrada: boolean;
    observacoes?: string[];
    [key: string]: any;
  };
  resumo_executivo: string;
  acoes_recomendadas: string[];
  confianca: number;
  lancamentos_auditados?: number;
  [key: string]: any;
}

export default function AuditPage() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<AuditResult | null>(null);
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
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao executar auditoria.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Auditoria Inteligente</h1>
          <p className="text-gray-400 mt-1">
            Detecção de anomalias, fraudes e desvios de compliance
          </p>
        </div>
        <Button onClick={runAudit} disabled={loading}>
          {loading ? "Auditando..." : "Executar Auditoria"}
        </Button>
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}

      <Tabs defaultValue="analysis" className="space-y-4">
        <TabsList className="bg-gray-800 border-gray-700">
          <TabsTrigger value="analysis" className="data-[state=active]:bg-gray-700">
            Análise IA
          </TabsTrigger>
        </TabsList>

        <TabsContent value="analysis">
          {data ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card className="bg-gray-900 border-gray-800 col-span-2">
                  <CardContent className="p-6 flex items-center gap-6">
                    <div className="text-center">
                      <div className={`text-6xl font-black ${RISK_GAUGE[data.nivel_risco] || "text-gray-400"}`}>
                        {data.score_risco ?? "—"}
                      </div>
                      <div className="text-xs text-gray-400 mt-1">
                        Score de Risco (0-100)
                      </div>
                    </div>
                    <div>
                      <div className={`text-2xl font-bold capitalize ${RISK_GAUGE[data.nivel_risco] || "text-gray-400"}`}>
                        Risco {data.nivel_risco}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        {data.lancamentos_auditados} lançamentos auditados
                      </div>
                      <div className="text-sm text-gray-400">
                        Confiança: {((data.confianca || 0) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gray-900 border-gray-800">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-400 mb-2">Equação Patrimonial</div>
                    <div className={`text-2xl font-bold ${data.compliance?.equacao_patrimonial ? "text-green-400" : "text-red-400"}`}>
                      {data.compliance?.equacao_patrimonial ? "✅ OK" : "❌ Falha"}
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-gray-900 border-gray-800">
                  <CardContent className="p-4">
                    <div className="text-xs text-gray-400 mb-2">Partida Dobrada</div>
                    <div className={`text-2xl font-bold ${data.compliance?.partida_dobrada ? "text-green-400" : "text-red-400"}`}>
                      {data.compliance?.partida_dobrada ? "✅ OK" : "❌ Falha"}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {data.anomalias?.length > 0 && (
                <Card className="bg-gray-900 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-lg text-white">
                      Anomalias Detectadas ({data.anomalias.length})
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
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
                              <p className="text-sm font-medium mb-1">{a.descricao}</p>
                              {a.lancamento_ref && (
                                <p className="text-xs opacity-70">Ref: {a.lancamento_ref}</p>
                              )}
                              {a.norma_violada && (
                                <p className="text-xs opacity-70">Norma: {a.norma_violada}</p>
                              )}
                            </div>
                            {a.valor_suspeito && (
                              <div className="text-right">
                                <div className="text-xs text-gray-400">Valor suspeito</div>
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
                  </CardContent>
                </Card>
              )}

              {data.acoes_recomendadas?.length > 0 && (
                <Card className="bg-gray-900 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-lg text-white">Ações Recomendadas</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ol className="space-y-2">
                      {data.acoes_recomendadas.map((a: string, i: number) => (
                        <li key={i} className="text-gray-300 text-sm flex items-start gap-2">
                          <span className="text-indigo-400 font-bold">{i + 1}.</span> {a}
                        </li>
                      ))}
                    </ol>
                  </CardContent>
                </Card>
              )}

              {data.resumo_executivo && (
                <Card className="bg-gray-900 border-gray-800">
                  <CardHeader>
                    <CardTitle className="text-lg text-white">Resumo Executivo</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {data.resumo_executivo}
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          ) : (
            <Card className="bg-gray-900 border-gray-800">
              <CardContent className="p-8 text-center text-gray-400">
                Execute a auditoria para ver os resultados
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
