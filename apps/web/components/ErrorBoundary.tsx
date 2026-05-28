"use client";

import { Button } from "@/components/ui/button";
import { AlertTriangle, Home, RefreshCw } from "lucide-react";
import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    // Log error to monitoring service in production
    if (typeof window !== "undefined" && process.env.NODE_ENV === "production") {
      // Future: Send to error tracking service (Sentry, etc.)
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-950 flex items-center justify-center p-6">
          <div className="max-w-md w-full bg-gray-900 border border-gray-800 rounded-xl p-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="bg-red-900/20 p-4 rounded-full">
                <AlertTriangle className="h-12 w-12 text-red-400" />
              </div>
            </div>
            <h2 className="text-2xl font-bold text-white mb-2">Algo deu errado</h2>
            <p className="text-gray-400 mb-4">
              {this.state.error?.message || "Ocorreu um erro inesperado."}
            </p>
            <p className="text-sm text-gray-500 mb-6">
              O erro foi registrado. Por favor, tente novamente ou contate o suporte se o problema persistir.
            </p>
            <div className="flex gap-3 justify-center">
              <Button
                onClick={() => window.location.reload()}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Recarregar
              </Button>
              <Button
                onClick={() => (window.location.href = "/dashboard")}
                variant="outline"
              >
                <Home className="h-4 w-4 mr-2" />
                Dashboard
              </Button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
