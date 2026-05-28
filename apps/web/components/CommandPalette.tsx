"use client";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { 
  LayoutDashboard, 
  FileText, 
  FileCheck, 
  Scale, 
  TrendingUp, 
  Search, 
  Building2, 
  Users, 
  Settings, 
  FileSpreadsheet,
  Receipt,
  ClipboardCheck,
  Calculator,
  ShieldCheck
} from "lucide-react";

const NAVIGATION_ITEMS = [
  { icon: LayoutDashboard, label: "Dashboard", path: "/dashboard" },
  { icon: FileText, label: "Documentos", path: "/dashboard/documents" },
  { icon: FileCheck, label: "Lançamentos Pendentes", path: "/dashboard/entries-pending" },
  { icon: Scale, label: "Auditoria", path: "/dashboard/audit" },
  { icon: TrendingUp, label: "Forecast", path: "/dashboard/forecast" },
  { icon: Calculator, label: "Conciliação", path: "/dashboard/reconciliation" },
  { icon: ShieldCheck, label: "Compliance", path: "/dashboard/compliance" },
  { icon: FileSpreadsheet, label: "Relatórios", path: "/dashboard/reports" },
  { icon: Receipt, label: "Audit Logs", path: "/dashboard/audit-logs" },
  { icon: Building2, label: "Gestão de Empresas", path: "/dashboard/admin/companies" },
  { icon: Users, label: "Gestão de Usuários", path: "/dashboard/admin/users" },
  { icon: Settings, label: "Configurações", path: "/dashboard/settings" },
];

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  const handleSelect = (path: string) => {
    setOpen(false);
    router.push(path);
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Buscar páginas, empresas, usuários..." />
      <CommandList>
        <CommandEmpty>Nenhum resultado encontrado.</CommandEmpty>
        <CommandGroup heading="Navegação">
          {NAVIGATION_ITEMS.map((item) => (
            <CommandItem
              key={item.path}
              onSelect={() => handleSelect(item.path)}
            >
              <item.icon className="mr-2 h-4 w-4" />
              <span>{item.label}</span>
            </CommandItem>
          ))}
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
