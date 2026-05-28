import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function useKeyboardShortcuts() {
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Shift + D: Dashboard
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "d") {
        e.preventDefault();
        router.push("/dashboard");
      }

      // Cmd/Ctrl + Shift + D: Documents
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "e") {
        e.preventDefault();
        router.push("/dashboard/documents");
      }

      // Cmd/Ctrl + Shift + A: Audit
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "a") {
        e.preventDefault();
        router.push("/dashboard/audit");
      }

      // Cmd/Ctrl + Shift + F: Forecast
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "f") {
        e.preventDefault();
        router.push("/dashboard/forecast");
      }

      // Cmd/Ctrl + Shift + R: Reports
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "r") {
        e.preventDefault();
        router.push("/dashboard/reports");
      }

      // Cmd/Ctrl + Shift + C: Companies
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "c") {
        e.preventDefault();
        router.push("/dashboard/admin/companies");
      }

      // Cmd/Ctrl + Shift + U: Users
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "u") {
        e.preventDefault();
        router.push("/dashboard/admin/users");
      }

      // Cmd/Ctrl + Shift + S: Settings
      if ((e.metaKey || e.ctrlKey) && e.shiftKey && e.key === "s") {
        e.preventDefault();
        router.push("/dashboard/settings");
      }

      // Escape: Voltar para dashboard
      if (e.key === "Escape") {
        e.preventDefault();
        router.push("/dashboard");
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [router]);
}
