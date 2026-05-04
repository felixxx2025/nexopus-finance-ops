import type { AppProps } from "next/app";
import Link from "next/link";
import "../styles/globals.css";

export default function App({ Component, pageProps }: AppProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-brand-900 text-white px-6 py-3 flex gap-6 text-sm font-medium">
        <span className="font-bold text-lg mr-4">Nexopus Finance Ops</span>
        <Link
          href="/dashboard"
          className="hover:text-brand-50 transition-colors"
        >
          Dashboard
        </Link>
        <Link href="/upload" className="hover:text-brand-50 transition-colors">
          Upload
        </Link>
        <Link href="/reports" className="hover:text-brand-50 transition-colors">
          Relatórios
        </Link>
      </nav>
      <main className="p-6">
        <Component {...pageProps} />
      </main>
    </div>
  );
}
