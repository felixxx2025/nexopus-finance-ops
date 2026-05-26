/**
 * Página do Assistente Financeiro IA — Chat com streaming SSE
 * Agente: GPT-5.2 (Copilot endpoint)
 */
import { useEffect, useRef, useState } from "react";
import { streamAssistant } from "../lib/api";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
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
];

export default function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<string>("");

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

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      {/* Header */}
      <div className="border-b border-gray-800 p-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-2xl font-bold text-white">
            🤖 Assistente Financeiro
          </h1>
          <p className="text-gray-400 text-sm">
            Powered by GPT-5.2 · Contexto: {DEMO_CONTEXT.empresa} ·{" "}
            {DEMO_CONTEXT.periodo}
          </p>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="text-6xl mb-4">💬</div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Como posso ajudar?
              </h2>
              <p className="text-gray-400 mb-8">
                Faça perguntas sobre os dados financeiros da sua empresa.
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
                className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === "user"
                    ? "bg-indigo-600 text-white rounded-br-sm"
                    : "bg-gray-900 border border-gray-800 text-gray-200 rounded-bl-sm"
                }`}
              >
                {m.role === "assistant" && (
                  <div className="flex items-center gap-1 mb-2 text-xs text-gray-400">
                    <span>🤖</span> Nexopus AI
                    {streaming && m.content.endsWith("▌") && (
                      <span className="ml-1 text-indigo-400 animate-pulse">
                        gerando...
                      </span>
                    )}
                  </div>
                )}
                <p className="whitespace-pre-wrap">{m.content}</p>
              </div>
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-gray-800 p-4">
        <div className="max-w-4xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
            placeholder="Faça uma pergunta sobre os dados financeiros..."
            disabled={streaming}
            className="flex-1 bg-gray-900 border border-gray-700 focus:border-indigo-500 rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 outline-none transition-colors disabled:opacity-50"
          />
          <button
            onClick={() => sendMessage()}
            disabled={!input.trim() || streaming}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white font-semibold px-5 py-3 rounded-xl transition-colors"
          >
            {streaming ? "⏳" : "→"}
          </button>
        </div>
        <p className="max-w-4xl mx-auto text-xs text-gray-600 mt-2">
          As respostas são baseadas nos dados financeiros carregados. Não
          substitui consultoria contábil profissional.
        </p>
      </div>
    </div>
  );
}
