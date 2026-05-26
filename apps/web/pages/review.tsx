import { useEffect, useState } from "react";
import { useAuth } from "../contexts/AuthContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Entry {
  id: string;
  date: string;
  description: string;
  status: string;
  ai_confidence: number | null;
  created_at: string;
}

async function fetchPending(companyId: string): Promise<Entry[]> {
  const res = await fetch(`${API}/entries/pending?company_id=${companyId}`, {
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
  const res = await fetch(`${API}/entries/${entryId}/review`, {
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
    green: "bg-green-100 text-green-700",
    yellow: "bg-yellow-100 text-yellow-700",
    red: "bg-red-100 text-red-700",
  }[color];
  return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>{pct}%</span>;
}

export default function Review() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<Entry[]>([]);
  const [loading, setLoading] = useState(true);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [toast, setToast] = useState<{ msg: string; type: "success" | "error" } | null>(null);

  // Em produção virá de um selector de empresa
  const companyId = typeof window !== "undefined"
    ? new URLSearchParams(window.location.search).get("company_id") ?? ""
    : "";

  useEffect(() => {
    if (!companyId) { setLoading(false); return; }
    fetchPending(companyId).then((e) => { setEntries(e); setLoading(false); });
  }, [companyId]);

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

  if (!companyId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Parâmetro <code>company_id</code> ausente na URL.</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Revisão de Lançamentos</h1>
        <p className="text-sm text-gray-500 mb-6">
          Lançamentos gerados por IA aguardando aprovação humana.
        </p>

        {toast && (
          <div
            className={`mb-4 p-3 rounded-lg text-sm border ${
              toast.type === "success"
                ? "bg-green-50 border-green-200 text-green-700"
                : "bg-red-50 border-red-200 text-red-700"
            }`}
          >
            {toast.msg}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-gray-400">Carregando...</div>
        ) : entries.length === 0 ? (
          <div className="bg-white rounded-2xl shadow p-12 text-center">
            <p className="text-gray-400 text-lg">Nenhum lançamento pendente de revisão.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div key={entry.id} className="bg-white rounded-2xl shadow p-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-semibold text-gray-800">
                        {entry.description || "(sem descrição)"}
                      </span>
                      <ConfidenceBadge confidence={entry.ai_confidence} />
                    </div>
                    <p className="text-xs text-gray-500">
                      Data: {entry.date} · Criado em: {new Date(entry.created_at).toLocaleString("pt-BR")}
                    </p>
                    <input
                      type="text"
                      placeholder="Nota de revisão (opcional)"
                      value={notes[entry.id] ?? ""}
                      onChange={(e) => setNotes((n) => ({ ...n, [entry.id]: e.target.value }))}
                      className="mt-2 w-full border border-gray-200 rounded-lg px-3 py-1.5 text-xs
                        focus:outline-none focus:ring-1 focus:ring-blue-400"
                    />
                  </div>
                  <div className="flex flex-col gap-2 shrink-0">
                    <button
                      onClick={() => handleAction(entry.id, "approve")}
                      disabled={actionLoading !== null}
                      className="px-4 py-1.5 bg-green-600 text-white text-xs font-medium rounded-lg
                        hover:bg-green-700 disabled:opacity-50 transition"
                    >
                      {actionLoading === entry.id + "approve" ? "..." : "Aprovar"}
                    </button>
                    <button
                      onClick={() => handleAction(entry.id, "reject")}
                      disabled={actionLoading !== null}
                      className="px-4 py-1.5 bg-red-100 text-red-700 text-xs font-medium rounded-lg
                        hover:bg-red-200 disabled:opacity-50 transition"
                    >
                      {actionLoading === entry.id + "reject" ? "..." : "Rejeitar"}
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
