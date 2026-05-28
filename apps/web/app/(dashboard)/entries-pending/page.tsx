"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompany } from "@/contexts/CompanyContext";
import { fetchPendingEntries } from "@/lib/api";
import { AlertCircle, CheckCircle, Loader2, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "/api";

interface PendingEntry {
  id: string;
  date: string;
  account: string;
  description: string;
  debit: number;
  credit: number;
  status: string;
  company_id: string;
}

const STATUS_COLORS = {
  pending: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
  approved: "bg-green-900/40 text-green-400 border-green-700",
  rejected: "bg-red-900/40 text-red-400 border-red-700",
};

function fmt(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

export default function EntriesPendingPage() {
  const [entries, setEntries] = useState<PendingEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { selectedCompanyId } = useCompany();

  useEffect(() => {
    loadEntries();
  }, [selectedCompanyId]);

  const loadEntries = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchPendingEntries({
        limit: 100,
        company_id: selectedCompanyId || undefined,
      });
      setEntries(data.entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar lançamentos");
      console.error("Error loading pending entries:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/entries/${id}/approve`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }
      // Reload entries after approval
      loadEntries();
    } catch (err) {
      console.error("Error approving entry:", err);
      alert(err instanceof Error ? err.message : "Erro ao aprovar lançamento");
    }
  };

  const handleReject = async (id: string) => {
    try {
      const res = await fetch(`${API_URL}/entries/${id}/reject`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }
      // Reload entries after rejection
      loadEntries();
    } catch (err) {
      console.error("Error rejecting entry:", err);
      alert(err instanceof Error ? err.message : "Erro ao rejeitar lançamento");
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("pt-BR");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Lançamentos Pendentes</h1>
          <p className="text-gray-400 mt-1">
            Aprove ou rejeite lançamentos contábeis pendentes
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadEntries}>
          <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <AlertCircle className="h-5 w-5 text-yellow-400" />
            {entries.length} lançamentos pendentes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={loadEntries} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : entries.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-400">Nenhum lançamento pendente</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-400">Data</TableHead>
                  <TableHead className="text-gray-400">Conta</TableHead>
                  <TableHead className="text-gray-400">Descrição</TableHead>
                  <TableHead className="text-gray-400">Débito</TableHead>
                  <TableHead className="text-gray-400">Crédito</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => (
                  <TableRow key={entry.id} className="border-gray-800">
                    <TableCell className="text-gray-300">{formatDate(entry.date)}</TableCell>
                    <TableCell className="text-white font-medium">{entry.account}</TableCell>
                    <TableCell className="text-gray-400">{entry.description}</TableCell>
                    <TableCell className="text-gray-300">{entry.debit > 0 ? fmt(entry.debit) : "-"}</TableCell>
                    <TableCell className="text-gray-300">{entry.credit > 0 ? fmt(entry.credit) : "-"}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={`border ${STATUS_COLORS[entry.status as keyof typeof STATUS_COLORS]}`}
                      >
                        {entry.status}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-green-400 hover:text-green-300"
                          onClick={() => handleApprove(entry.id)}
                        >
                          <CheckCircle className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-red-400 hover:text-red-300"
                          onClick={() => handleReject(entry.id)}
                        >
                          <XCircle className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
