"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { formatDistanceToNow } from "date-fns";
import { ptBR } from "date-fns/locale";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  FileText,
  TrendingUp,
  Upload,
  User,
} from "lucide-react";

interface Activity {
  id: string;
  type: "upload" | "approval" | "report" | "alert" | "forecast";
  title: string;
  description: string;
  timestamp: Date;
  user?: string;
  metadata?: Record<string, any>;
}

const MOCK_ACTIVITIES: Activity[] = [
  {
    id: "1",
    type: "upload",
    title: "Documento enviado",
    description: "SPED Fiscal 2026 foi processado com sucesso",
    timestamp: new Date(Date.now() - 1000 * 60 * 5), // 5 min ago
    user: "admin",
  },
  {
    id: "2",
    type: "approval",
    title: "Lançamento aprovado",
    description: "3 lançamentos foram aprovados automaticamente",
    timestamp: new Date(Date.now() - 1000 * 60 * 30), // 30 min ago
    user: "admin",
  },
  {
    id: "3",
    type: "report",
    title: "DRE gerada",
    description: "Demonstrativo do Resultado do Exercício de Abril 2026",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), // 2 hours ago
    user: "admin",
  },
  {
    id: "4",
    type: "alert",
    title: "Alerta de compliance",
    description: "Margem EBITDA abaixo do esperado (18.5%)",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 4), // 4 hours ago
  },
  {
    id: "5",
    type: "forecast",
    title: "Forecast atualizado",
    description: "Previsão de fluxo de caixa para os próximos 90 dias",
    timestamp: new Date(Date.now() - 1000 * 60 * 60 * 24), // 1 day ago
    user: "admin",
  },
];

const ACTIVITY_CONFIG = {
  upload: { icon: Upload, color: "text-blue-400", bgColor: "bg-blue-900/20", borderColor: "border-blue-700" },
  approval: { icon: CheckCircle, color: "text-green-400", bgColor: "bg-green-900/20", borderColor: "border-green-700" },
  report: { icon: FileText, color: "text-purple-400", bgColor: "bg-purple-900/20", borderColor: "border-purple-700" },
  alert: { icon: AlertTriangle, color: "text-yellow-400", bgColor: "bg-yellow-900/20", borderColor: "border-yellow-700" },
  forecast: { icon: TrendingUp, color: "text-cyan-400", bgColor: "bg-cyan-900/20", borderColor: "border-cyan-700" },
};

export function ActivityFeed() {
  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-lg text-white flex items-center gap-2">
          <Clock className="h-5 w-5 text-gray-400" />
          Atividades Recentes
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80 pr-4">
          <div className="space-y-4">
            {MOCK_ACTIVITIES.map((activity) => {
              const config = ACTIVITY_CONFIG[activity.type];
              const Icon = config.icon;

              return (
                <div
                  key={activity.id}
                  className={`flex gap-3 p-3 rounded-lg border ${config.bgColor} ${config.borderColor}`}
                >
                  <div className={`mt-0.5 ${config.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-medium text-white">{activity.title}</p>
                      <Badge variant="outline" className="text-xs border-gray-700 text-gray-400">
                        {activity.type}
                      </Badge>
                    </div>
                    <p className="text-xs text-gray-400 mb-1">{activity.description}</p>
                    <div className="flex items-center gap-2 text-xs text-gray-500">
                      {activity.user && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {activity.user}
                        </span>
                      )}
                      <span>•</span>
                      <span>{formatDistanceToNow(activity.timestamp, { addSuffix: true, locale: ptBR })}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
