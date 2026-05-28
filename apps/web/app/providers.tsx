"use client";

import { ErrorBoundary } from "@/components/ErrorBoundary";
import { ThemeProvider } from "@/components/ThemeProvider";
import { AuthProvider } from "@/contexts/AuthContext";
import { CompanyProvider } from "@/contexts/CompanyContext";
import { QueryProvider } from "@/providers/QueryProvider";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary>
      <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
        <QueryProvider>
          <AuthProvider>
            <CompanyProvider>{children}</CompanyProvider>
          </AuthProvider>
        </QueryProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
}
