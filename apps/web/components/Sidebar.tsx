"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/contexts/AuthContext";
import {
  ArrowRightLeft,
  Building2,
  CheckCircle,
  ChevronLeft,
  ChevronRight,
  Clock,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquare,
  Search,
  Settings,
  Shield,
  TrendingUp,
  Upload,
  User,
  X
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

const NAV_GROUPS = [
  {
    title: "Principal",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/upload", label: "Upload", icon: Upload },
      { href: "/documents", label: "Documentos", icon: FileText },
      { href: "/reports", label: "Relatórios", icon: FileText },
    ],
  },
  {
    title: "Inteligência Artificial",
    items: [
      { href: "/forecast", label: "Forecast", icon: TrendingUp },
      { href: "/audit", label: "Auditoria", icon: Search },
      { href: "/assistant", label: "Assistente", icon: MessageSquare },
      { href: "/reconciliation", label: "Conciliação", icon: ArrowRightLeft },
    ],
  },
  {
    title: "Workflow",
    items: [
      { href: "/entries-pending", label: "Lançamentos Pendentes", icon: Clock },
      { href: "/review", label: "Revisão", icon: CheckCircle },
    ],
  },
  {
    title: "Compliance",
    items: [
      { href: "/audit-logs", label: "Audit Logs", icon: Search },
      { href: "/compliance", label: "Compliance", icon: FileText },
    ],
  },
  {
    title: "Conhecimento",
    items: [
      { href: "/knowledge", label: "Base de Conhecimento", icon: FileText },
    ],
  },
  {
    title: "Administração",
    items: [
      { href: "/admin/companies", label: "Gestão de Empresas", icon: Building2 },
      { href: "/admin/users", label: "Gestão de Usuários", icon: Shield },
      { href: "/settings", label: "Configurações", icon: Settings },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const handleToggle = () => setMobileOpen(prev => !prev);
    document.addEventListener('toggle-mobile-sidebar', handleToggle);
    return () => document.removeEventListener('toggle-mobile-sidebar', handleToggle);
  }, []);

  const NavLink = ({
    href,
    label,
    icon: Icon,
  }: {
    href: string;
    label: string;
    icon: any;
  }) => {
    const isActive = pathname === href;
    return (
      <Link
        href={href}
        onClick={() => setMobileOpen(false)}
        className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive
          ? "bg-indigo-600 text-white"
          : "text-gray-300 hover:bg-gray-800 hover:text-white"
          }`}
      >
        <Icon className="h-4 w-4 shrink-0" />
        {!collapsed && <span>{label}</span>}
      </Link>
    );
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 z-50 h-screen bg-gray-900 border-r border-gray-800 transition-all duration-300 ${collapsed ? "w-16" : "w-64"
          } ${mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}
      >
        {/* Logo */}
        <div className="flex items-center justify-between p-4 border-b border-gray-800">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center shrink-0">
              <span className="text-white font-bold text-lg">⚡</span>
            </div>
            {!collapsed && (
              <span className="text-white font-bold text-lg truncate">Nexopus</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="lg:hidden"
              onClick={() => setMobileOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="hidden lg:flex"
              onClick={() => setCollapsed(!collapsed)}
            >
              {collapsed ? (
                <ChevronRight className="h-4 w-4" />
              ) : (
                <ChevronLeft className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 p-3">
          {NAV_GROUPS.map((group, i) => (
            <div key={i} className="mb-6">
              {!collapsed && (
                <p className="text-xs font-semibold text-gray-500 uppercase mb-2 px-3">
                  {group.title}
                </p>
              )}
              <div className="space-y-1">
                {group.items.map((item) => (
                  <NavLink key={item.href} {...item} />
                ))}
              </div>
              {i < NAV_GROUPS.length - 1 && <Separator className="my-4 bg-gray-800" />}
            </div>
          ))}
        </ScrollArea>

        {/* User menu */}
        <div className="p-3 border-t border-gray-800">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className={`w-full justify-start gap-3 ${collapsed ? "px-2" : "px-3"}`}
              >
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback className="bg-indigo-600 text-white">
                    {user?.charAt(0).toUpperCase() || "U"}
                  </AvatarFallback>
                </Avatar>
                {!collapsed && (
                  <div className="text-left overflow-hidden">
                    <p className="text-sm font-medium text-white truncate">
                      {user || "Usuário"}
                    </p>
                    <p className="text-xs text-gray-500 truncate">Admin</p>
                  </div>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>Minha Conta</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem>
                <User className="mr-2 h-4 w-4" />
                <span>Perfil</span>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                <span>Configurações</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Sair</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </aside>

      {/* Mobile menu button */}
      <Button
        variant="ghost"
        size="icon"
        className="lg:hidden fixed top-4 left-4 z-50"
        onClick={() => setMobileOpen(true)}
      >
        <Menu className="h-5 w-5" />
      </Button>
    </>
  );
}
