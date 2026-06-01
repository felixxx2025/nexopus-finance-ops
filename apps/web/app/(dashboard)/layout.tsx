"use client";

import { CommandPalette } from "@/components/CommandPalette";
import { Sidebar } from "@/components/Sidebar";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAuth } from "@/contexts/AuthContext";
import { useCompany } from "@/contexts/CompanyContext";
import { useKeyboardShortcuts } from "@/hooks/useKeyboardShortcuts";
import { seedCompanyAccounts } from "@/lib/api";
import { Database, Loader2, Menu, Moon, Search, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import dynamic from "next/dynamic";
import { useState } from "react";
import { Toaster } from "sonner";

// Lazy load Notifications component
const Notifications = dynamic(
  () => import("@/components/Notifications").then((mod) => ({ default: mod.Notifications })),
  {
    loading: () => <div className="h-10 w-10" />,
    ssr: false,
  }
);

// Lazy load FloatingChat component
const FloatingChat = dynamic(
  () => import("@/components/FloatingChat"),
  {
    loading: () => <div className="h-14 w-14" />,
    ssr: false,
  }
);

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated } = useAuth();
  const { companies, selectedCompanyId, selectedYear, setSelectedCompanyId, setSelectedYear } = useCompany();
  const { theme, setTheme } = useTheme();
  const [isSeeding, setIsSeeding] = useState(false);

  useKeyboardShortcuts();

  const handleSeedAccounts = async () => {
    if (!selectedCompanyId) return;
    try {
      setIsSeeding(true);
      const result = await seedCompanyAccounts(selectedCompanyId);
      if (result.success) {
        alert(`Seed de contas realizado com sucesso! ${result.accounts_created} contas criadas.`);
      } else {
        alert(`Erro ao fazer seed de contas: ${result.message}`);
      }
    } catch (error) {
      alert("Erro ao fazer seed de contas");
      console.error(error);
    } finally {
      setIsSeeding(false);
    }
  };

  if (!isAuthenticated) {
    return null;
  }

  const currentYear = new Date().getFullYear();
  const years = [currentYear - 2, currentYear - 1, currentYear, currentYear + 1];

  return (
    <div className="min-h-screen bg-gray-950">
      <Sidebar />
      <CommandPalette />
      <Toaster position="top-right" richColors closeButton />
      <FloatingChat />

      {/* Main content area with margin for sidebar */}
      <div className="lg:ml-64">
        {/* Header */}
        <header className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-sm border-b border-gray-800 px-6 py-4">
          <div className="flex items-center justify-between gap-4">
            {/* Mobile menu button */}
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => document.dispatchEvent(new CustomEvent('toggle-mobile-sidebar'))}
            >
              <Menu className="h-5 w-5" />
            </Button>

            {/* Company & Year Selectors */}
            <div className="flex items-center gap-3 flex-1">
              {companies.length > 0 && (
                <Select value={selectedCompanyId || undefined} onValueChange={setSelectedCompanyId}>
                  <SelectTrigger className="w-64 bg-gray-800 border-gray-700 text-white">
                    <SelectValue placeholder="Selecione a empresa" />
                  </SelectTrigger>
                  <SelectContent className="bg-gray-800 border-gray-700">
                    {companies.map((company) => (
                      <SelectItem key={company.id} value={company.id} className="text-white">
                        {company.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}

              <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v, 10))}>
                <SelectTrigger className="w-32 bg-gray-800 border-gray-700 text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-gray-800 border-gray-700">
                  {years.map((year) => (
                    <SelectItem key={year} value={year.toString()} className="text-white">
                      {year}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {selectedCompanyId && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleSeedAccounts}
                  disabled={isSeeding}
                  className="text-xs"
                >
                  {isSeeding ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Database className="h-4 w-4 mr-2" />
                  )}
                  Seed Contas
                </Button>
              )}
            </div>

            {/* Right side actions */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'k', metaKey: true }))}
                className="text-gray-400 hover:text-white"
              >
                <Search className="h-5 w-5" />
                <span className="ml-2 text-xs text-gray-500">⌘K</span>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                className="text-gray-400 hover:text-white"
              >
                {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
              </Button>
              <Notifications />
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">{children}</main>
      </div>
    </div>
  );
}
