"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useCompany } from "@/contexts/CompanyContext";

export function CompanySelector() {
  const {
    companies,
    selectedCompanyId,
    selectedYear,
    setSelectedCompanyId,
    setSelectedYear,
    loading,
  } = useCompany();

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  if (loading) {
    return (
      <div className="flex gap-2">
        <div className="h-9 w-48 bg-gray-200 rounded animate-pulse" />
        <div className="h-9 w-24 bg-gray-200 rounded animate-pulse" />
      </div>
    );
  }

  return (
    <div className="flex gap-2 items-center">
      <Select
        value={selectedCompanyId || ""}
        onValueChange={setSelectedCompanyId}
      >
        <SelectTrigger className="w-48">
          <SelectValue placeholder="Selecione a empresa" />
        </SelectTrigger>
        <SelectContent>
          {companies.map((company) => (
            <SelectItem key={company.id} value={company.id}>
              {company.name}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={selectedYear.toString()} onValueChange={(v) => setSelectedYear(parseInt(v, 10))}>
        <SelectTrigger className="w-24">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {years.map((year) => (
            <SelectItem key={year} value={year.toString()}>
              {year}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
