/**
 * Página do Assistente Financeiro IA — Chat com streaming SSE e RAG
 * Agente: GPT-5.2 (Copilot endpoint)
 * RAG: PostgreSQL + pgvector para busca semântica
 */
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { streamAssistant } from "@/lib/api";
import { useEffect, useRef, useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

const DEMO_CONTEXT = {
  empresa: "Empresa Demo",
  periodo: "Jan-Abr 2026",
  dre: {
    receita_bruta: 358000,
    deducoes: 28640,
    receita_liquida: 329360,
    despesas_operacionais: 175000,
    ebitda: 154360,
    resultado_liquido: 98360,
  },
};

const SUGESTOES = [
  "Como está a margem de lucro da empresa?",
  "Quais são os principais riscos financeiros?",
  "Compare receitas com despesas do último trimestre.",
  "O que é EBITDA e como calculá-lo?",
  "Quais ações tomar para melhorar o resultado?",
  "Explique o Balanço Patrimonial em termos simples.",
  "O que diz a NBC TG 26 sobre demonstrações?",
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<string>("");

  useEffect(() => {
    const saved = localStorage.getItem("nexopus_assistant_history");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error("Erro ao carregar histórico:", e);
      }
    }
  }, []);

  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("nexopus_assistant_history", JSON.stringify(messages));
    }
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function sendMessage(question?: string) {
    const q = question || input.trim();
    if (!q || streaming) return;
    setInput("");

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content: q,
    };
    const assistantId = crypto.randomUUID();
    streamRef.current = "";

    setMessages((prev) => [
      ...prev,
      userMsg,
      { id: assistantId, role: "assistant", content: "▌" },
    ]);
    setStreaming(true);

    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    streamAssistant(
      q,
      DEMO_CONTEXT,
      history,
      (chunk) => {
        streamRef.current += chunk;
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: streamRef.current + "▌" }
              : m,
          ),
        );
      },
      () => {
        setStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: streamRef.current } : m,
          ),
        );
      },
      (err) => {
        setStreaming(false);
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, content: `[Erro: ${err}]` } : m,
          ),
        );
      },
    );
  }

  function clearHistory() {
    setMessages([]);
    localStorage.removeItem("nexopus_assistant_history");
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">
            🤖 Assistente Financeiro
          </h1>
          <p className="text-gray-400 mt-1">
            Powered by GPT-5.2 + RAG · Contexto: {DEMO_CONTEXT.empresa} ·{" "}
            {DEMO_CONTEXT.periodo}
          </p>
        </div>
        <button
          onClick={clearHistory}
          className="text-gray-400 hover:text-white text-sm transition-colors"
        >
          Limpar histórico
        </button>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6">
          <div className="max-w-4xl mx-auto space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-12">
                <div className="text-6xl mb-4">💬</div>
                <h2 className="text-xl font-semibold text-white mb-2">
                  Como posso ajudar?
                </h2>
                <p className="text-gray-400 mb-8">
                  Faça perguntas sobre os dados financeiros da sua empresa ou
                  conceitos contábeis.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                  {SUGESTOES.map((s, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(s)}
                      className="text-left bg-gray-900 hover:bg-gray-800 border border-gray-700 hover:border-indigo-500 rounded-xl p-3 text-sm text-gray-300 transition-all"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) => (
              <div
                key={m.id}
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${m.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-sm"
                    : "bg-gray-900 border border-gray-800 text-gray-200 rounded-bl-sm"
                    }`}
                >
                  {m.role === "assistant" && (
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-1 text-xs text-gray-400">
                        <span>🤖</span>
                        <span>Nexopus AI</span>
                        {streaming && m.content.endsWith("▌") && (
                          <span className="ml-1 text-indigo-400 animate-pulse">
                            gerando...
                          </span>
                        )}
                      </div>
                      {m.sources && m.sources.length > 0 && (
                        <button
                          onClick={() => setShowSources(!showSources)}
                          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                        >
                          {showSources ? "Ocultar fontes" : "Ver fontes"}
                        </button>
                      )}
                    </div>
                  )}
                  <p className="whitespace-pre-wrap">{m.content}</p>
                  {m.sources && m.sources.length > 0 && showSources && (
                    <div className="mt-3 pt-3 border-t border-gray-700">
                      <p className="text-xs text-gray-400 mb-2">Fontes consultadas:</p>
                      <ul className="text-xs text-gray-500 space-y-1">
                        {m.sources.map((source, i) => (
                          <li key={i} className="flex items-start gap-1">
                            <span>📄</span>
                            <span>{source}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>
        </CardContent>
      </Card>

      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-4">
          <div className="max-w-4xl mx-auto flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
              placeholder="Faça uma pergunta sobre os dados financeiros ou contabilidade..."
              disabled={streaming}
              className="flex-1 bg-gray-800 border border-gray-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition-colors disabled:opacity-50"
            />
            <button
              onClick={() => sendMessage()}
              disabled={!input.trim() || streaming}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold px-5 py-3 rounded-xl transition-colors"
            >
              {streaming ? "⏳" : "→"}
            </button>
          </div>
          <p className="max-w-4xl mx-auto text-xs text-gray-500 mt-2 flex items-center justify-center gap-2">
            <span>Respostas baseadas em RAG + dados financeiros</span>
            <span>·</span>
            <span>Não substitui consultoria contábil profissional</span>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
