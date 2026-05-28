"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AlertTriangle, CheckCircle, FileText, Loader2, Scale, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "/api";

const COMPLIANCE_ITEMS = [
  {
    category: "NBC TG",
    items: [
      { id: "nbc-tg-26", name: "NBC TG 26 - Apresentação das Demonstrações", status: "compliant", description: "Demonstrações em conformidade" },
      { id: "nbc-tg-27", name: "NBC TG 27 - Redução ao Valor Recuperável", status: "compliant", description: "Testes de impairment realizados" },
      { id: "nbc-tg-28", name: "NBC TG 28 - Instrumentos Financeiros", status: "warning", description: "Classificação precisa de revisão" },
      { id: "nbc-tg-35", name: "NBC TG 35 - Apresentação de Demonstrações", status: "compliant", description: "Consolidação em conformidade" },
    ],
  },
  {
    category: "Lei 6.404/76",
    items: [
      { id: "lei-6404-1", name: "Escrituração Contábil", status: "compliant", description: "Livros contábeis regularizados" },
      { id: "lei-6404-2", name: "Demonstrações Financeiras", status: "compliant", description: "DRE e Balanço publicados" },
      { id: "lei-6404-3", name: "Lucro Real e Presumido", status: "compliant", description: "Apuração correta" },
      { id: "lei-6404-4", name: "Dividendos Obrigatórios", status: "warning", description: "Verificar cálculo mínimo" },
    ],
  },
  {
    category: "Documentação",
    items: [
      { id: "doc-1", name: "Contratos Sociais", status: "compliant", description: "Ata de constituição disponível" },
      { id: "doc-2", name: "Balancetes Mensais", status: "compliant", description: "Todos os meses de 2026" },
      { id: "doc-3", name: "Notas Fiscais", status: "non-compliant", description: "Faltam notas de dezembro" },
      { id: "doc-4", name: "Comprovantes de Pagamento", status: "warning", description: "Algumas notas pendentes" },
    ],
  },
];

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
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Simulate loading compliance data from API
    const loadCompliance = async () => {
      try {
        setIsLoading(true);
        // Future: fetch from API
        // const res = await fetch(`${API_URL}/compliance`, { credentials: "include" });
        // const data = await res.json();
        // setComplianceData(data);
        await new Promise(resolve => setTimeout(resolve, 500)); // Simulate network delay
      } catch (err) {
        setError(err instanceof Error ? err.message : "Erro ao carregar dados de compliance");
      } finally {
        setIsLoading(false);
      }
    };

    loadCompliance();
  }, []);

  const totalItems = COMPLIANCE_ITEMS.reduce((acc, cat) => acc + cat.items.length, 0);
  const compliantCount = COMPLIANCE_ITEMS.reduce(
    (acc, cat) => acc + cat.items.filter((i) => i.status === "compliant").length,
    0,
  );
  const warningCount = COMPLIANCE_ITEMS.reduce(
    (acc, cat) => acc + cat.items.filter((i) => i.status === "warning").length,
    0,
  );
  const nonCompliantCount = COMPLIANCE_ITEMS.reduce(
    (acc, cat) => acc + cat.items.filter((i) => i.status === "non-compliant").length,
    0,
  );
  const complianceScore = Math.round((compliantCount / totalItems) * 100);

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

      {/* Compliance Categories */}
      {COMPLIANCE_ITEMS.map((category) => (
        <Card key={category.category} className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              {category.category === "NBC TG" && <FileText className="h-5 w-5" />}
              {category.category === "Lei 6.404/76" && <Scale className="h-5 w-5" />}
              {category.category}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {category.items.map((item) => {
                const config = STATUS_CONFIG[item.status as keyof typeof STATUS_CONFIG];
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
            </div>
          </CardContent>
        </Card>
      ))}

      {/* Remediation Tasks */}
      <Card className="bg-orange-900/20 border-orange-700">
        <CardHeader>
          <CardTitle className="text-orange-400 flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            Tarefas de Remediação
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            <li className="text-gray-300 text-sm flex items-start gap-2">
              <span className="text-orange-400 mt-0.5">•</span>
              <span>Revisar classificação de instrumentos financeiros (NBC TG 28)</span>
            </li>
            <li className="text-gray-300 text-sm flex items-start gap-2">
              <span className="text-orange-400 mt-0.5">•</span>
              <span>Verificar cálculo de dividendos obrigatórios (Lei 6.404/76)</span>
            </li>
            <li className="text-gray-300 text-sm flex items-start gap-2">
              <span className="text-red-400 mt-0.5">•</span>
              <span>Obter notas fiscais de dezembro (prioridade alta)</span>
            </li>
            <li className="text-gray-300 text-sm flex items-start gap-2">
              <span className="text-yellow-400 mt-0.5">•</span>
              <span>Complementar comprovantes de pagamento pendentes</span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
