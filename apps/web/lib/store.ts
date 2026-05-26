/**
 * Store global Zustand — estado da aplicação Nexopus Finance Ops.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

// ── Tipos ─────────────────────────────────────────────────────────────────────
export interface User {
  username: string;
  role?: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface FinancialContext {
  empresa?: string;
  periodo?: string;
  dre?: object;
  balanco?: object;
  forecast?: object;
  audit?: object;
  lancamentos_recentes?: object[];
}

// ── Store principal ───────────────────────────────────────────────────────────
interface AppState {
  // Auth
  user: User | null;
  setUser: (user: User | null) => void;

  // Empresa selecionada
  selectedCompanyId: string;
  selectedYear: number;
  setSelectedCompany: (id: string) => void;
  setSelectedYear: (year: number) => void;

  // Chat Assistant
  chatMessages: ChatMessage[];
  chatContext: FinancialContext;
  addChatMessage: (msg: Omit<ChatMessage, "id" | "timestamp">) => void;
  clearChat: () => void;
  setChatContext: (ctx: FinancialContext) => void;

  // Notificações
  notifications: Array<{
    id: string;
    message: string;
    type: "info" | "success" | "warning" | "error";
  }>;
  addNotification: (n: Omit<AppState["notifications"][0], "id">) => void;
  removeNotification: (id: string) => void;

  // Upload status
  uploadProgress: number;
  uploadStatus: "idle" | "uploading" | "processing" | "done" | "error";
  setUploadProgress: (p: number) => void;
  setUploadStatus: (s: AppState["uploadStatus"]) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // Auth
      user: null,
      setUser: (user) => set({ user }),

      // Empresa
      selectedCompanyId: "",
      selectedYear: new Date().getFullYear(),
      setSelectedCompany: (id) => set({ selectedCompanyId: id }),
      setSelectedYear: (year) => set({ selectedYear: year }),

      // Chat
      chatMessages: [],
      chatContext: {},
      addChatMessage: (msg) =>
        set((state) => ({
          chatMessages: [
            ...state.chatMessages,
            { ...msg, id: crypto.randomUUID(), timestamp: new Date() },
          ],
        })),
      clearChat: () => set({ chatMessages: [] }),
      setChatContext: (ctx) => set({ chatContext: ctx }),

      // Notificações
      notifications: [],
      addNotification: (n) =>
        set((state) => ({
          notifications: [
            ...state.notifications,
            { ...n, id: crypto.randomUUID() },
          ],
        })),
      removeNotification: (id) =>
        set((state) => ({
          notifications: state.notifications.filter((n) => n.id !== id),
        })),

      // Upload
      uploadProgress: 0,
      uploadStatus: "idle",
      setUploadProgress: (p) => set({ uploadProgress: p }),
      setUploadStatus: (s) => set({ uploadStatus: s }),
    }),
    {
      name: "nexopus-store",
      partialize: (state) => ({
        user: state.user,
        selectedCompanyId: state.selectedCompanyId,
        selectedYear: state.selectedYear,
      }),
    },
  ),
);
