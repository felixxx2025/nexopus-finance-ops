"use client";

import {
  login as apiLogin,
  logout as apiLogout,
  me as apiMe
} from "@/lib/api";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface AuthContextValue {
  user: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  login: async () => { },
  logout: async () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Restaura sessão via /auth/me (valida cookie httpOnly no servidor)
  useEffect(() => {
    // Skip auth check on login page to prevent loading issues
    if (typeof window === "undefined" || window.location.pathname === "/login") {
      return;
    }

    apiMe()
      .then((data) => setUser(data.username))
      .catch(() => {
        // Expected when not logged in - just set user to null
        setUser(null);
      });
  }, []);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    setUser(data.username);
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
      window.location.href = "/login";
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
