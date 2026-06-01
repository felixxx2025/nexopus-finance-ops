"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCompany } from "@/contexts/CompanyContext";
import { CheckCircle, XCircle } from "lucide-react";
import { useEffect, useState } from "react";

interface Entry {
  id: string;
  date: string;
  description: string;
  status: string;
  ai_confidence: number | null;
  created_at: string;
}

async function fetchPending(companyId: string): Promise<Entry[]> {
  const API_URL = "/api";
  const res = await fetch(`${API_URL}/entries/pending?company_id=${companyId}`, {
    credentials: "include",
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.entries ?? [];
}

async function reviewEntry(
  entryId: string,
  action: "approve" | "reject",
  note?: string
): Promise<void> {
  const API_URL = "/api";
  const res = await fetch(`${API_URL}/entries/${entryId}/review`, {
    method: "PATCH",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, note }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erro ${res.status}`);
  }
}

function ConfidenceBadge({ confidence }: { confidence: number | null }) {
  if (confidence === null) return <span className="text-gray-400 text-xs">—</span>;
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? "green" : pct >= 60 ? "yellow" : "red";
  const cls = {
    green: "bg-green-900/20 text-green-400 border-green-700",
    yellow: "bg-yellow-900/20 text-yellow-400 border-yellow-700",
    red: "bg-red-900/20 text-red-400 border-red-700",
  }[color];
  return <Badge variant="outline" className={cls}>{pct}%</Badge>;
}

export default function Review() {
  const { selectedCompanyId } = useCompany();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  useEffect(() => {
    if (!selectedCompanyId) { setLoading(false); return; }
    fetchPending(selectedCompanyId).then((entries) => { setEntries(entries); setLoading(false); });
  }, [selectedCompanyId]);

  function showToast(msg: string, type: "success" | "error") {
    setToast({ msg, type });
    setTimeout(() => setToast(null), 3000);
  }

  async function handleAction(id: string, action: "approve" | "reject") {
    setActionLoading(id + action);
    try {
      await reviewEntry(id, action, notes[id]);
      setEntries((prev) => prev.filter((e) => e.id !== id));
      showToast(action === "approve" ? "Lançamento aprovado." : "Lançamento rejeitado.", "success");
    } catch (err: any) {
      showToast(err.message, "error");
    } finally {
      setActionLoading(null);
    }
  }

  if (!selectedCompanyId) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <p className="text-gray-400 text-lg">Selecione uma empresa para revisar lançamentos</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Revisão de Lançamentos</h1>
        <p className="text-gray-400 mt-1">
          Lançamentos gerados por IA aguardando aprovação humana
        </p>
      </div>

      {toast && (
        <div
          className={`p-3 rounded-lg text-sm border ${toast.type === "success"
            ? "bg-green-900/40 border-green-500 text-green-300"
            : "bg-red-900/40 border-red-500 text-red-300"
            }`}
        >
          {toast.msg}
        </div>
      )}

      {loading ? (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-8 text-center text-gray-400">Carregando...</CardContent>
        </Card>
      ) : entries.length === 0 ? (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-8 text-center text-gray-400">
            Nenhum lançamento pendente de revisão
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => (
            <Card key={entry.id} className="bg-gray-900 border-gray-800">
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-white">
                        {entry.description || "(sem descrição)"}
                      </span>
                      <ConfidenceBadge confidence={entry.ai_confidence} />
                    </div>
                    <p className="text-xs text-gray-400">
                      Data: {entry.date} · Criado em: {new Date(entry.created_at).toLocaleString("pt-BR")}
                    </p>
                    <input
                      type="text"
                      placeholder="Nota de revisão (opcional)"
                      value={notes[entry.id] ?? ""}
                      onChange={(e) => setNotes((n) => ({ ...n, [entry.id]: e.target.value }))}
                      className="mt-2 w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-1.5 text-xs text-white
                        focus:outline-none focus:ring-1 focus:ring-indigo-500"
                    />
                  </div>
                  <div className="flex flex-col gap-2 shrink-0">
                    <Button
                      onClick={() => handleAction(entry.id, "approve")}
                      disabled={actionLoading !== null}
                      size="sm"
                      className="bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="h-4 w-4 mr-1" />
                      {actionLoading === entry.id + "approve" ? "..." : "Aprovar"}
                    </Button>
                    <Button
                      onClick={() => handleAction(entry.id, "reject")}
                      disabled={actionLoading !== null}
                      size="sm"
                      variant="outline"
                      className="bg-red-900/20 border-red-700 text-red-400 hover:bg-red-900/30"
                    >
                      <XCircle className="h-4 w-4 mr-1" />
                      {actionLoading === entry.id + "reject" ? "..." : "Rejeitar"}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
