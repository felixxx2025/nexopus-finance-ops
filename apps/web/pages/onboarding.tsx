import { useState } from "react";
import { useRouter } from "next/router";
import { useAuth } from "../contexts/AuthContext";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function createCompany(name: string, cnpj: string, token: string) {
  const res = await fetch(`${API}/companies`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ name, cnpj }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Erro ${res.status}`);
  }
  return res.json();
}

export default function Onboarding() {
  const { user } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [cnpj, setCnpj] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  function formatCnpj(v: string) {
    const d = v.replace(/\D/g, "").slice(0, 14);
    return d
      .replace(/^(\d{2})(\d)/, "$1.$2")
      .replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/\.(\d{3})(\d)/, ".$1/$2")
      .replace(/(\d{4})(\d)/, "$1-$2");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await createCompany(name, cnpj, "");
      setSuccess(
        `Empresa "${result.name}" criada com ${result.contas_semeadas} contas do plano padrão NBC TG.`
      );
      setTimeout(() => router.push("/dashboard"), 2500);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 w-full max-w-md">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Cadastrar Empresa</h1>
        <p className="text-sm text-gray-500 mb-6">
          O plano de contas padrão NBC TG será semeado automaticamente.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            {error}
          </div>
        )}
        {success && (
          <div className="mb-4 p-3 rounded-lg bg-green-50 border border-green-200 text-green-700 text-sm">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Razão Social
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              placeholder="Empresa Exemplo Ltda"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">CNPJ</label>
            <input
              type="text"
              value={cnpj}
              onChange={(e) => setCnpj(formatCnpj(e.target.value))}
              required
              placeholder="00.000.000/0001-00"
              maxLength={18}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <button
            type="submit"
            disabled={loading || !name || cnpj.replace(/\D/g, "").length < 14}
            className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-medium text-sm
              hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? "Cadastrando..." : "Cadastrar Empresa"}
          </button>
        </form>

        <p className="mt-4 text-center text-xs text-gray-400">
          Somente administradores podem cadastrar empresas.
        </p>
      </div>
    </div>
  );
}
