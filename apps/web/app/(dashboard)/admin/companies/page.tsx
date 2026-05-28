"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompany } from "@/contexts/CompanyContext";
import { Building2, Edit, Loader2, Plus, Trash2 } from "lucide-react";
import { useState } from "react";

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
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingCompany, setEditingCompany] = useState<Company | null>(null);
  const [newCompanyName, setNewCompanyName] = useState("");
  const [newCompanyCNPJ, setNewCompanyCNPJ] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

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

  const handleCreateCompany = async () => {
    if (!newCompanyName.trim() || !newCompanyCNPJ.trim()) {
      alert("Por favor, preencha todos os campos.");
      return;
    }

    try {
      setIsCreating(true);
      const res = await fetch(`${API_URL}/companies`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCompanyName,
          cnpj: newCompanyCNPJ,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Reset form and close modal
      setNewCompanyName("");
      setNewCompanyCNPJ("");
      setShowCreateModal(false);
      refreshCompanies();
    } catch (err) {
      console.error("Error creating company:", err);
      alert(err instanceof Error ? err.message : "Erro ao criar empresa");
    } finally {
      setIsCreating(false);
    }
  };

  const handleEditCompany = async () => {
    if (!editingCompany || !newCompanyName.trim() || !newCompanyCNPJ.trim()) {
      alert("Por favor, preencha todos os campos.");
      return;
    }

    try {
      setIsEditing(true);
      const res = await fetch(`${API_URL}/companies/${editingCompany.id}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newCompanyName,
          cnpj: newCompanyCNPJ,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Reset form and close modal
      setNewCompanyName("");
      setNewCompanyCNPJ("");
      setEditingCompany(null);
      setShowEditModal(false);
      refreshCompanies();
    } catch (err) {
      console.error("Error editing company:", err);
      alert(err instanceof Error ? err.message : "Erro ao editar empresa");
    } finally {
      setIsEditing(false);
    }
  };

  const openEditModal = (company: Company) => {
    setEditingCompany(company);
    setNewCompanyName(company.name);
    setNewCompanyCNPJ(company.cnpj);
    setShowEditModal(true);
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
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Nova Empresa
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-gray-900 border-gray-800 text-white">
              <DialogHeader>
                <DialogTitle>Criar Nova Empresa</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Preencha os dados para cadastrar uma nova empresa no sistema.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Nome da Empresa</label>
                  <Input
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                    placeholder="Ex: Empresa ABC Ltda"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">CNPJ</label>
                  <Input
                    value={newCompanyCNPJ}
                    onChange={(e) => setNewCompanyCNPJ(e.target.value)}
                    placeholder="00.000.000/0000-00"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => setShowCreateModal(false)}
                  disabled={isCreating}
                >
                  Cancelar
                </Button>
                <Button onClick={handleCreateCompany} disabled={isCreating}>
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Criando...
                    </>
                  ) : (
                    "Criar Empresa"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
            <DialogContent className="bg-gray-900 border-gray-800 text-white">
              <DialogHeader>
                <DialogTitle>Editar Empresa</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Atualize os dados da empresa selecionada.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Nome da Empresa</label>
                  <Input
                    value={newCompanyName}
                    onChange={(e) => setNewCompanyName(e.target.value)}
                    placeholder="Ex: Empresa ABC Ltda"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">CNPJ</label>
                  <Input
                    value={newCompanyCNPJ}
                    onChange={(e) => setNewCompanyCNPJ(e.target.value)}
                    placeholder="00.000.000/0000-00"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingCompany(null);
                    setNewCompanyName("");
                    setNewCompanyCNPJ("");
                  }}
                  disabled={isEditing}
                >
                  Cancelar
                </Button>
                <Button onClick={handleEditCompany} disabled={isEditing}>
                  {isEditing ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Salvando...
                    </>
                  ) : (
                    "Salvar Alterações"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
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
                          onClick={() => openEditModal(company)}
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
