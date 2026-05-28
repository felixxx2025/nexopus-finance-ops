/**
 * FloatingChat — Componente de chat flutuante reutilizável.
 *
 * Botão toggle fixo no canto inferior direito com chat expansível.
 * Integração com contexto da página atual.
 * Persistência de estado via localStorage.
 */
"use client";

import { streamAssistant } from "@/lib/api";
import { useEffect, useRef, useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

interface FloatingChatProps {
  /** Contexto financeiro da página atual */
  pageContext?: {
    empresa?: string;
    periodo?: string;
    dre?: any;
    balanco?: any;
    forecast?: any;
    audit?: any;
    lancamentos_recentes?: any[];
  };
  /** Sugestões contextuais baseadas na página */
  suggestions?: string[];
  /** Título personalizado para o chat */
  title?: string;
}

const DEFAULT_SUGGESTIONS = [
  "O que é EBITDA?",
  "Explique a partida dobrada",
  "Como calcular o lucro líquido?",
  "O que diz a NBC TG 26?",
];

export default function FloatingChat({
  pageContext = {},
  suggestions = DEFAULT_SUGGESTIONS,
  title = "🤖 Nexopus AI",
}: FloatingChatProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const streamRef = useRef<string>("");

  // Carregar histórico do localStorage
  useEffect(() => {
    const saved = localStorage.getItem("nexopus_chat_history");
    if (saved) {
      try {
        setMessages(JSON.parse(saved));
      } catch (e) {
        console.error("Erro ao carregar histórico:", e);
      }
    }
  }, []);

  // Salvar histórico no localStorage
  useEffect(() => {
    if (messages.length > 0) {
      localStorage.setItem("nexopus_chat_history", JSON.stringify(messages));
    }
  }, [messages]);

  // Auto-scroll para o final
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
      pageContext,
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
    localStorage.removeItem("nexopus_chat_history");
  }

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-indigo-600 hover:bg-indigo-700 text-white p-4 rounded-full shadow-lg transition-all hover:scale-110 z-50"
        title="Abrir Assistente"
      >
        <svg
          className="w-6 h-6"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
          />
        </svg>
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 max-h-[600px] bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl z-50 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="text-xl">🤖</span>
          <h3 className="font-semibold text-white">{title}</h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsMinimized(!isMinimized)}
            className="text-gray-400 hover:text-white transition-colors"
            title={isMinimized ? "Expandir" : "Minimizar"}
          >
            {isMinimized ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
              </svg>
            )}
          </button>
          <button
            onClick={clearHistory}
            className="text-gray-400 hover:text-white transition-colors"
            title="Limpar histórico"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
          </button>
          <button
            onClick={() => setIsOpen(false)}
            className="text-gray-400 hover:text-white transition-colors"
            title="Fechar"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      {!isMinimized && (
        <>
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 max-h-96">
            {messages.length === 0 && (
              <div className="text-center py-8">
                <div className="text-4xl mb-3">💬</div>
                <h4 className="text-white font-semibold mb-2">
                  Como posso ajudar?
                </h4>
                <p className="text-gray-400 text-sm mb-4">
                  Pergunte sobre contabilidade, DRE, Balanço ou normas.
                </p>
                <div className="grid grid-cols-1 gap-2">
                  {suggestions.slice(0, 3).map((s, i) => (
                    <button
                      key={i}
                      onClick={() => sendMessage(s)}
                      className="text-left bg-gray-800 hover:bg-gray-700 border border-gray-700 hover:border-indigo-500 rounded-lg p-2 text-xs text-gray-300 transition-all"
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
                className={`flex ${m.role === "user" ? "justify-end" : "justify-start"
                  }`}
              >
                <div
                  className={`max-w-[85%] rounded-xl px-3 py-2 text-sm leading-relaxed ${m.role === "user"
                      ? "bg-indigo-600 text-white rounded-br-sm"
                      : "bg-gray-800 border border-gray-700 text-gray-200 rounded-bl-sm"
                    }`}
                >
                  {m.role === "assistant" && (
                    <div className="flex items-center gap-1 mb-1 text-xs text-gray-400">
                      <span>🤖</span>
                      <span>Nexopus AI</span>
                      {streaming && m.content.endsWith("▌") && (
                        <span className="ml-1 text-indigo-400 animate-pulse">
                          digitando...
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

          {/* Input */}
          <div className="p-4 border-t border-gray-700">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) =>
                  e.key === "Enter" && !e.shiftKey && sendMessage()
                }
                placeholder="Digite sua pergunta..."
                disabled={streaming}
                className="flex-1 bg-gray-800 border border-gray-700 focus:border-indigo-500 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-500 outline-none transition-colors disabled:opacity-50"
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || streaming}
                className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white p-2 rounded-lg transition-colors"
              >
                {streaming ? (
                  <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                  </svg>
                )}
              </button>
            </div>
            <p className="text-xs text-gray-600 mt-2 text-center">
              Respostas baseadas em RAG + dados financeiros
            </p>
          </div>
        </>
      )}
    </div>
  );
}
