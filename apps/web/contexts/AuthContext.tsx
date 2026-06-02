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
  token: string | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  token: null,
  login: async () => { },
  logout: async () => { },
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [hasCheckedAuth, setHasCheckedAuth] = useState(false);

  // Restaura sessão via /auth/me (valida cookie httpOnly no servidor)
  useEffect(() => {
    // Skip auth check on login page to prevent loading issues
    if (typeof window === "undefined" || window.location.pathname === "/login") {
      setIsLoading(false);
      setHasCheckedAuth(true);
      return;
    }

    // Only check auth once to prevent retry loops
    if (hasCheckedAuth) {
      return;
    }

    let mounted = true;
    setIsLoading(true);
    
    // Add timeout to prevent hanging on fetch errors
    const timeoutId = setTimeout(() => {
      if (mounted) {
        console.warn("Auth check timed out, assuming not logged in");
        setUser(null);
        setToken(null);
        setIsLoading(false);
        setHasCheckedAuth(true);
      }
    }, 5000);

    apiMe()
      .then((data) => {
        clearTimeout(timeoutId);
        if (mounted) {
          setUser(data.username);
          // Token is stored in httpOnly cookie, not accessible via JS
          // We'll use a placeholder for WebSocket authentication
          setToken("cookie-auth");
        }
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        if (mounted) {
          console.warn("Auth check failed:", error);
          // Expected when not logged in - just set user to null
          setUser(null);
          setToken(null);
        }
      })
      .finally(() => {
        clearTimeout(timeoutId);
        if (mounted) {
          setIsLoading(false);
          setHasCheckedAuth(true);
        }
      });

    return () => {
      mounted = false;
      clearTimeout(timeoutId);
    };
  }, [hasCheckedAuth]);

  const login = useCallback(async (username: string, password: string) => {
    const data = await apiLogin(username, password);
    setUser(data.username);
    setToken("cookie-auth");
  }, []);

  const logout = useCallback(async () => {
    try {
      await apiLogout();
    } finally {
      setUser(null);
      setToken(null);
      window.location.href = "/login";
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, isAuthenticated: !!user, isLoading, token, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
