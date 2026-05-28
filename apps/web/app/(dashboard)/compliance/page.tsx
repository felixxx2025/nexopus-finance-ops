"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, FileText, Loader2, Scale, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { fetchCompliance } from "@/lib/api";
import { useCompany } from "@/contexts/CompanyContext";

const API_URL = "/api";

const STATUS_CONFIG = {
  compliant: {
    icon: CheckCircle,
    color: "text-green-400",
    bg: "bg-green-900/40",
    border: "border-green-700",
    label: "Conforme",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-yellow-400",
    bg: "bg-yellow-900/40",
    border: "border-yellow-700",
    label: "Atenção",
  },
  "non-compliant": {
    icon: XCircle,
    color: "text-red-400",
    bg: "bg-red-900/40",
    border: "border-red-700",
    label: "Não Conforme",
  },
};

export default function CompliancePage() {
  const { selectedCompanyId } = useCompany();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [complianceData, setComplianceData] = useState<any>(null);

  useEffect(() => {
    const loadCompliance = async () => {
      if (!selectedCompanyId) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        const data = await fetchCompliance(selectedCompanyId);
        setComplianceData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar dados de compliance");
      } finally {
        setIsLoading(false);
      }
    };

    loadCompliance();
  }, [selectedCompanyId]);

  const complianceItems = complianceData?.items || [];
  const complianceScore = complianceData?.score || 0;
  const compliantCount = complianceItems.filter((i: any) => i.status === "compliant").length;
  const warningCount = complianceItems.filter((i: any) => i.status === "warning").length;
  const nonCompliantCount = complianceItems.filter((i: any) => i.status === "non-compliant").length;

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Compliance Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Monitoramento de conformidade com normas contábeis brasileiras
          </p>
        </div>
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-white">Compliance Dashboard</h1>
          <p className="text-gray-400 mt-1">
            Monitoramento de conformidade com normas contábeis brasileiras
          </p>
        </div>
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 text-red-300">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Compliance Dashboard</h1>
        <p className="text-gray-400 mt-1">
          Monitoramento de conformidade com normas contábeis brasileiras
        </p>
      </div>

      {/* Score Card */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white">Score de Compliance Geral</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-8">
            <div className="text-center">
              <div className="text-7xl font-black text-green-400">{complianceScore}%</div>
              <div className="text-sm text-gray-400 mt-2">Conformidade Total</div>
            </div>
            <div className="flex-1 grid grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-900/20 rounded-lg border border-green-700">
                <div className="text-3xl font-bold text-green-400">{compliantCount}</div>
                <div className="text-xs text-gray-400 mt-1">Conforme</div>
              </div>
              <div className="text-center p-4 bg-yellow-900/20 rounded-lg border border-yellow-700">
                <div className="text-3xl font-bold text-yellow-400">{warningCount}</div>
                <div className="text-xs text-gray-400 mt-1">Atenção</div>
              </div>
              <div className="text-center p-4 bg-red-900/20 rounded-lg border border-red-700">
                <div className="text-3xl font-bold text-red-400">{nonCompliantCount}</div>
                <div className="text-xs text-gray-400 mt-1">Não Conforme</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Compliance Items */}
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Scale className="h-5 w-5" />
            Itens de Compliance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {complianceItems.map((item: any) => {
              const config = STATUS_CONFIG[item.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.warning;
              const Icon = config.icon;
              return (
                <div
                  key={item.id}
                  className={`p-4 rounded-lg border ${config.bg} ${config.border}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Icon className={`h-4 w-4 ${config.color}`} />
                        <h3 className="font-semibold text-white">{item.name}</h3>
                        <Badge variant="outline" className={`border ${config.bg} ${config.color}`}>
                          {config.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-400">{item.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
            {complianceItems.length === 0 && (
              <div className="text-center py-8 text-gray-400">
                Nenhum item de compliance disponível
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Errors Section */}
      {complianceData?.errors && (
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              Erros de Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {complianceData.errors.cnpj && complianceData.errors.cnpj.length > 0 && (
                <div className="p-3 bg-red-900/20 border border-red-700 rounded-lg">
                  <h4 className="font-semibold text-red-400 mb-2">CNPJ</h4>
                  <ul className="text-sm text-gray-300 list-disc list-inside">
                    {complianceData.errors.cnpj.map((err: string, idx: number) => (
                      <li key={idx}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
              {complianceData.errors.partida_dobrada && complianceData.errors.partida_dobrada.length > 0 && (
                <div className="p-3 bg-yellow-900/20 border border-yellow-700 rounded-lg">
                  <h4 className="font-semibold text-yellow-400 mb-2">Partida Dobrada</h4>
                  <ul className="text-sm text-gray-300 list-disc list-inside">
                    {complianceData.errors.partida_dobrada.map((err: any, idx: number) => (
                      <li key={idx}>
                        {err.description} - Débito: {err.debit}, Crédito: {err.credit}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {complianceData.errors.equacao_patrimonial && complianceData.errors.equacao_patrimonial.length > 0 && (
                <div className="p-3 bg-orange-900/20 border border-orange-700 rounded-lg">
                  <h4 className="font-semibold text-orange-400 mb-2">Equação Patrimonial</h4>
                  <ul className="text-sm text-gray-300 list-disc list-inside">
                    {complianceData.errors.equacao_patrimonial.map((err: any, idx: number) => (
                      <li key={idx}>
                        Diferença: {err.diferenca} (Ativo: {err.ativo}, Passivo+PL: {err.passivo + err.pl})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {!complianceData.errors.cnpj?.length && !complianceData.errors.partida_dobrada?.length && !complianceData.errors.equacao_patrimonial?.length && (
                <div className="text-center py-4 text-green-400">
                  Nenhum erro de compliance detectado
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
