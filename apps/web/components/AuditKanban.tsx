"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { AlertCircle, CheckCircle, Clock, User } from "lucide-react";
import { useState } from "react";

interface Entry {
  id: string;
  description: string;
  amount: number;
  date: string;
  status: "pending" | "review" | "approved" | "rejected";
  assignedTo?: string;
  category: string;
}

const MOCK_ENTRIES: Entry[] = [
  {
    id: "1",
    description: "Pagamento de fornecedor ABC Ltda",
    amount: 15420.50,
    date: "2026-04-15",
    status: "pending",
    assignedTo: "admin",
    category: "Despesa",
  },
  {
    id: "2",
    description: "Recebimento de cliente XYZ",
    amount: 45000.00,
    date: "2026-04-14",
    status: "review",
    assignedTo: "admin",
    category: "Receita",
  },
  {
    id: "3",
    description: "Provisão de impostos",
    amount: 8750.00,
    date: "2026-04-13",
    status: "approved",
    assignedTo: "admin",
    category: "Imposto",
  },
  {
    id: "4",
    description: "Ajuste de conciliação bancária",
    amount: -250.00,
    date: "2026-04-12",
    status: "rejected",
    assignedTo: "admin",
    category: "Ajuste",
  },
  {
    id: "5",
    description: "Pagamento de salários",
    amount: 125000.00,
    date: "2026-04-11",
    status: "pending",
    assignedTo: "admin",
    category: "Despesa",
  },
];

const COLUMNS = {
  pending: { title: "Pendente", color: "border-yellow-700", bgColor: "bg-yellow-900/10" },
  review: { title: "Em Revisão", color: "border-blue-700", bgColor: "bg-blue-900/10" },
  approved: { title: "Aprovado", color: "border-green-700", bgColor: "bg-green-900/10" },
  rejected: { title: "Rejeitado", color: "border-red-700", bgColor: "bg-red-900/10" },
};

const STATUS_CONFIG = {
  pending: { icon: Clock, color: "text-yellow-400" },
  review: { icon: AlertCircle, color: "text-blue-400" },
  approved: { icon: CheckCircle, color: "text-green-400" },
  rejected: { icon: AlertCircle, color: "text-red-400" },
};

export function AuditKanban() {
  const [entries] = useState<Entry[]>(MOCK_ENTRIES);

  const groupedEntries = {
    pending: entries.filter((e) => e.status === "pending"),
    review: entries.filter((e) => e.status === "review"),
    approved: entries.filter((e) => e.status === "approved"),
    rejected: entries.filter((e) => e.status === "rejected"),
  };

  function fmt(v: number) {
    return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-white">Trilha de Auditoria</h2>
        <Button variant="outline" size="sm">Filtrar</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(COLUMNS).map(([status, config]) => {
          const columnEntries = groupedEntries[status as keyof typeof groupedEntries];
          const StatusIcon = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG].icon;
          const statusColor = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG].color;

          return (
            <div key={status} className={`rounded-lg border ${config.color} ${config.bgColor} p-4`}>
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <StatusIcon className={`h-5 w-5 ${statusColor}`} />
                  <h3 className="font-semibold text-white">{config.title}</h3>
                </div>
                <Badge variant="outline" className="bg-gray-800 border-gray-700 text-white">
                  {columnEntries.length}
                </Badge>
              </div>

              <div className="space-y-3">
                {columnEntries.map((entry) => (
                  <Card key={entry.id} className="bg-gray-900 border-gray-800 cursor-pointer hover:border-gray-600 transition-colors">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <Badge variant="outline" className="text-xs border-gray-700 text-gray-400">
                          {entry.category}
                        </Badge>
                        <span className="text-xs text-gray-500">{entry.date}</span>
                      </div>
                      <p className="text-sm text-white font-medium mb-2">{entry.description}</p>
                      <div className="flex items-center justify-between">
                        <span className={`text-sm font-mono ${entry.amount >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {fmt(entry.amount)}
                        </span>
                        {entry.assignedTo && (
                          <div className="flex items-center gap-1 text-xs text-gray-400">
                            <User className="h-3 w-3" />
                            {entry.assignedTo}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {columnEntries.length === 0 && (
                  <div className="text-center py-8 text-gray-500 text-sm">
                    Nenhum lançamento
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
