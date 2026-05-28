"use client";

import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Building2, Plus, Edit, Trash2, Loader2 } from "lucide-react";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompany } from "@/contexts/CompanyContext";

const API_URL = "/api";

interface Company {
  id: string;
  name: string;
  cnpj: string;
  created_at: string;
}

export default function AdminCompaniesPage() {
  const { companies, selectedCompanyId, refreshCompanies } = useCompany();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const handleDeleteCompany = async (companyId: string) => {
    if (!confirm("Tem certeza que deseja excluir esta empresa? Esta ação não pode ser desfeita.")) {
      return;
    }

    try {
      const res = await fetch(`${API_URL}/companies/${companyId}`, {
        method: "DELETE",
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Refresh companies list after deletion
      refreshCompanies();
    } catch (err) {
      console.error("Error deleting company:", err);
      alert(err instanceof Error ? err.message : "Erro ao excluir empresa");
    }
  };

  const handleCreateCompany = () => {
    // Placeholder for create functionality - would open a modal
    alert("Funcionalidade de criação de empresa será implementada com modal de formulário.");
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Gestão de Empresas</h1>
          <p className="text-gray-400 mt-1">
            Gerencie as empresas cadastradas no sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={refreshCompanies} disabled={isLoading}>
            <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button onClick={handleCreateCompany}>
            <Plus className="h-4 w-4 mr-2" />
            Nova Empresa
          </Button>
        </div>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Building2 className="h-5 w-5 text-indigo-400" />
            {companies.length} empresas cadastradas
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={refreshCompanies} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : companies.length === 0 ? (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-gray-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-white mb-2">Nenhuma empresa cadastrada</h3>
              <p className="text-gray-400 mb-4">Comece adicionando sua primeira empresa</p>
              <Button onClick={handleCreateCompany}>
                <Plus className="h-4 w-4 mr-2" />
                Adicionar Empresa
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-400">Nome</TableHead>
                  <TableHead className="text-gray-400">CNPJ</TableHead>
                  <TableHead className="text-gray-400">Criado em</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {companies.map((company) => (
                  <TableRow key={company.id} className="border-gray-800">
                    <TableCell className="text-white font-medium">{company.name}</TableCell>
                    <TableCell className="text-gray-400 font-mono text-sm">
                      {company.cnpj}
                    </TableCell>
                    <TableCell className="text-gray-400">{formatDate(company.created_at)}</TableCell>
                    <TableCell>
                      <Badge
                        variant="outline"
                        className={
                          company.id === selectedCompanyId
                            ? "bg-green-900/40 text-green-400 border-green-700"
                            : "bg-gray-700 text-gray-300 border-gray-600"
                        }
                      >
                        {company.id === selectedCompanyId ? "Selecionada" : "Ativa"}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8"
                          onClick={() => alert(`Funcionalidade de edição para ${company.name} será implementada.`)}
                        >
                          <Edit className="h-4 w-4 mr-1" />
                          Editar
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-8 text-red-400"
                          onClick={() => handleDeleteCompany(company.id)}
                          disabled={company.id === selectedCompanyId}
                        >
                          <Trash2 className="h-4 w-4 mr-1" />
                          Excluir
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
