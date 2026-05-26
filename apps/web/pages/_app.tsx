import type { AppProps } from "next/app";
import Link from "next/link";
import { useRouter } from "next/router";
import { AuthProvider, useAuth } from "../contexts/AuthContext";
import "../styles/globals.css";

const NAV_LINKS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/upload", label: "Upload", icon: "📂" },
  { href: "/reports", label: "Relatórios", icon: "📋" },
  { href: "/forecast", label: "Forecast", icon: "📈" },
  { href: "/audit", label: "Auditoria", icon: "🔍" },
  { href: "/assistant", label: "Assistente IA", icon: "🤖" },
  { href: "/reconciliation", label: "Conciliação", icon: "🏦" },
];

function NavBar() {
  const { isAuthenticated, user, logout } = useAuth();
  const router = useRouter();
  const isLogin = router.pathname === "/login";

  if (isLogin || !isAuthenticated) return null;

  return (
    <nav className="bg-gray-900 border-b border-gray-800 text-white px-4 py-3 flex gap-1 text-sm font-medium items-center overflow-x-auto">
      <Link
        href="/dashboard"
        className="font-bold text-base mr-4 text-indigo-400 whitespace-nowrap"
      >
        ⚡ Nexopus
      </Link>
      {NAV_LINKS.map((l) => (
        <Link
          key={l.href}
          href={l.href}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg whitespace-nowrap transition-colors ${
            router.pathname === l.href
              ? "bg-indigo-600 text-white"
              : "text-gray-300 hover:bg-gray-800 hover:text-white"
          }`}
        >
          <span>{l.icon}</span>
          <span className="hidden md:inline">{l.label}</span>
        </Link>
      ))}
      <div className="ml-auto flex items-center gap-3">
        <span className="text-xs text-gray-400 hidden lg:block">{user}</span>
        <button
          onClick={logout}
          className="text-xs bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg transition-colors"
        >
          Sair
        </button>
      </div>
    </nav>
  );
}

export default function App({ Component, pageProps }: AppProps) {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-gray-950">
        <NavBar />
        <main>
          <Component {...pageProps} />
        </main>
      </div>
    </AuthProvider>
  );
}
