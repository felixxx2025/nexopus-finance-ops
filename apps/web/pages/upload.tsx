"use client";

import { useRouter } from "next/router";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { uploadDocument } from "../lib/api";

type UploadStatus = "idle" | "uploading" | "success" | "error";

export default function Upload() {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState<UploadStatus>("idle");
  const [docId, setDocId] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Redireciona para login se não autenticado
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, authLoading, router]);

  if (authLoading) return null;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const file = inputRef.current?.files?.[0];
    if (!file) return;

    const allowed = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
      "text/plain",
    ];
    if (!allowed.includes(file.type)) {
      setErrorMsg("Apenas PDF, Excel (.xlsx) ou SPED (.txt) são aceitos.");
      setStatus("error");
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setErrorMsg("Arquivo excede o limite de 50 MB.");
      setStatus("error");
      return;
    }

    setStatus("uploading");
    setErrorMsg(null);

    try {
      const data = await uploadDocument(file);
      setDocId(data.doc_id);
      setStatus("success");
      if (inputRef.current) inputRef.current.value = "";
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Erro desconhecido");
      setStatus("error");
    }
  }

  return (
    <div className="max-w-xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">Upload de Documento</h1>
      <p className="text-sm text-gray-500">
        Envie um PDF, planilha Excel ou arquivo SPED. A IA irá extrair os dados
        e gerar os lançamentos automaticamente.
      </p>

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl shadow p-6 space-y-4"
      >
        <label className="block">
          <span className="text-sm font-medium text-gray-700">
            Selecionar arquivo
          </span>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,.xlsx,.txt"
            required
            className="mt-1 block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg
                       file:border-0 file:text-sm file:font-semibold file:bg-brand-50 file:text-brand-500
                       hover:file:bg-brand-100"
          />
        </label>

        <button
          type="submit"
          disabled={status === "uploading"}
          className="w-full py-2 px-4 bg-brand-500 text-white font-semibold rounded-lg hover:bg-brand-900
                     transition-colors disabled:opacity-50"
        >
          {status === "uploading" ? "Enviando…" : "Enviar Documento"}
        </button>
      </form>

      {status === "success" && (
        <div className="rounded-lg bg-green-50 border border-green-300 text-green-800 px-4 py-3 text-sm">
          Documento enviado com sucesso! ID:{" "}
          <code className="font-mono">{docId}</code>. Processamento em
          andamento.
        </div>
      )}

      {status === "error" && (
        <div className="rounded-lg bg-red-50 border border-red-300 text-red-800 px-4 py-3 text-sm">
          {errorMsg}
        </div>
      )}
    </div>
  );
}
