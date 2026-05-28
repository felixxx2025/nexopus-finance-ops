"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";

interface Company {
  id: string;
  name: string;
  cnpj: string;
  created_at: string;
}

interface CompanyContextValue {
  companies: Company[];
  selectedCompanyId: string | null;
  selectedYear: number;
  selectedCompany: Company | null;
  loading: boolean;
  error: string | null;
  setSelectedCompanyId: (id: string | null) => void;
  setSelectedYear: (year: number) => void;
  refreshCompanies: () => Promise<void>;
}

const CompanyContext = createContext<CompanyContextValue>({
  companies: [],
  selectedCompanyId: null,
  selectedYear: new Date().getFullYear(),
  selectedCompany: null,
  loading: true,
  error: null,
  setSelectedCompanyId: () => { },
  setSelectedYear: () => { },
  refreshCompanies: async () => { },
});

export function CompanyProvider({ children }: { children: React.ReactNode }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompanyId, setSelectedCompanyIdState] = useState<string | null>(
    null,
  );
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Load companies from API
  const fetchCompanies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const API_URL = "/api";
      const res = await fetch(`${API_URL}/companies`, {
        credentials: "include",
      });
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setCompanies(data.companies || []);

      // Restore selected company from localStorage
      const savedCompanyId = localStorage.getItem("nexopus_selected_company");
      if (savedCompanyId && data.companies?.find((c: Company) => c.id === savedCompanyId)) {
        setSelectedCompanyIdState(savedCompanyId);
      } else if (data.companies?.length > 0) {
        setSelectedCompanyIdState(data.companies[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar empresas");
      console.error("Error fetching companies:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  // Persist selected company
  const setSelectedCompanyId = useCallback((id: string | null) => {
    setSelectedCompanyIdState(id);
    if (id) {
      localStorage.setItem("nexopus_selected_company", id);
    } else {
      localStorage.removeItem("nexopus_selected_company");
    }
  }, []);

  // Persist selected year
  const setSelectedYearCallback = useCallback((year: number) => {
    setSelectedYear(year);
    localStorage.setItem("nexopus_selected_year", year.toString());
  }, []);

  // Restore year from localStorage
  useEffect(() => {
    const savedYear = localStorage.getItem("nexopus_selected_year");
    if (savedYear) {
      setSelectedYear(parseInt(savedYear, 10));
    }
  }, []);

  const selectedCompany =
    companies.find((c) => c.id === selectedCompanyId) || null;

  return (
    <CompanyContext.Provider
      value={{
        companies,
        selectedCompanyId,
        selectedYear,
        selectedCompany,
        loading,
        error,
        setSelectedCompanyId,
        setSelectedYear: setSelectedYearCallback,
        refreshCompanies: fetchCompanies,
      }}
    >
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  return useContext(CompanyContext);
}
