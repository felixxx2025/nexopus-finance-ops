"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fetchAuditLogs } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";
import { Download, Filter, Loader2, Search } from "lucide-react";
import { useState } from "react";

const API_URL = "/api";

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  entity: string;
  entity_id: string;
  details: string;
  ip_address: string;
}

const ACTION_COLORS: Record<string, string> = {
  create: "bg-green-900/40 text-green-400 border-green-700",
  update: "bg-blue-900/40 text-blue-400 border-blue-700",
  delete: "bg-red-900/40 text-red-400 border-red-700",
  upload: "bg-purple-900/40 text-purple-400 border-purple-700",
  approve: "bg-green-900/40 text-green-400 border-green-700",
  reject: "bg-red-900/40 text-red-400 border-red-700",
  generate: "bg-indigo-900/40 text-indigo-400 border-indigo-700",
};

export default function AuditLogsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["audit-logs"],
    queryFn: () => fetchAuditLogs({ limit: 100 }),
  });

  const logs = data?.logs || [];

  const filteredLogs = logs.filter((log) => {
    const matchesSearch =
      log.user.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.action.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.entity.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesAction = actionFilter === "all" || log.action === actionFilter;
    return matchesSearch && matchesAction;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const handleExportLogs = async () => {
    try {
      const res = await fetch(`${API_URL}/audit-logs/export`, {
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Download the CSV file
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `audit_logs_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Error exporting audit logs:", err);
      alert(err instanceof Error ? err.message : "Erro ao exportar logs");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Audit Logs</h1>
          <p className="text-gray-400 mt-1">
            Histórico completo de todas as ações no sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportLogs}>
            <Download className="h-4 w-4 mr-2" />
            Exportar Logs
          </Button>
        </div>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Search className="h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar por usuário, ação ou entidade..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
              />
            </div>
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-gray-400" />
              <select
                value={actionFilter}
                onChange={(e) => setActionFilter(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
              >
                <option value="all">Todas as Ações</option>
                <option value="create">Criar</option>
                <option value="update">Atualizar</option>
                <option value="delete">Deletar</option>
                <option value="upload">Upload</option>
                <option value="approve">Aprovar</option>
                <option value="reject">Rejeitar</option>
                <option value="generate">Gerar</option>
              </select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-400">{error instanceof Error ? error.message : "Erro ao carregar logs"}</p>
              <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-400">Timestamp</TableHead>
                  <TableHead className="text-gray-400">Usuário</TableHead>
                  <TableHead className="text-gray-400">Ação</TableHead>
                  <TableHead className="text-gray-400">Entidade</TableHead>
                  <TableHead className="text-gray-400">Empresa</TableHead>
                  <TableHead className="text-gray-400">IP Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredLogs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-gray-400 py-8">
                      Nenhum log encontrado
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredLogs.map((log) => (
                    <TableRow key={log.id} className="border-gray-800">
                      <TableCell className="text-gray-300">{formatDate(log.timestamp)}</TableCell>
                      <TableCell className="text-white font-medium">{log.user}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={`border ${ACTION_COLORS[log.action] || "bg-gray-800 text-gray-300"}`}
                        >
                          {log.action}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-300">{log.entity}</TableCell>
                      <TableCell className="text-gray-400">{log.details}</TableCell>
                      <TableCell className="text-gray-500 font-mono text-xs">
                        {log.ip_address}
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
