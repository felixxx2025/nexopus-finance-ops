"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fetchUsers } from "@/lib/api";
import { Ban, Edit, Loader2, Shield, UserPlus } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "/api";

interface User {
  username: string;
  email?: string;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export default function AdminUsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchUsers({ limit: 100 });
      setUsers(data.users);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar usuários");
      console.error("Error loading users:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const handleDeactivateUser = async (username: string) => {
    if (!confirm(`Tem certeza que deseja desativar o usuário ${username}?`)) {
      return;
    }

    try {
      const res = await fetch(`${API_URL}/users/${username}/deactivate`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Reload users after deactivation
      loadUsers();
    } catch (err) {
      console.error("Error deactivating user:", err);
      alert(err instanceof Error ? err.message : "Erro ao desativar usuário");
    }
  };

  const handleEditUser = (username: string) => {
    // Placeholder for edit functionality - would open a modal or navigate to edit page
    alert(`Funcionalidade de edição para usuário ${username} será implementada com modal de edição.`);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Gestão de Usuários</h1>
          <p className="text-gray-400 mt-1">
            Gerencie usuários do sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadUsers}>
            <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button>
            <UserPlus className="h-4 w-4 mr-2" />
            Novo Usuário
          </Button>
        </div>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Shield className="h-5 w-5 text-indigo-400" />
            {users.length} usuários cadastrados
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
              <Button variant="outline" size="sm" onClick={loadUsers} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-400">Usuário</TableHead>
                  <TableHead className="text-gray-400">Email</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Criado em</TableHead>
                  <TableHead className="text-gray-400">Último Login</TableHead>
                  <TableHead className="text-gray-400">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {users.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-gray-400 py-8">
                      Nenhum usuário encontrado
                    </TableCell>
                  </TableRow>
                ) : (
                  users.map((user) => (
                    <TableRow key={user.username} className="border-gray-800">
                      <TableCell className="text-white font-medium">{user.username}</TableCell>
                      <TableCell className="text-gray-400">{user.email || "-"}</TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={`border ${user.is_active
                            ? "bg-green-900/40 text-green-400 border-green-700"
                            : "bg-red-900/40 text-red-400 border-red-700"
                            }`}
                        >
                          {user.is_active ? "Ativo" : "Inativo"}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-gray-400">{formatDate(user.created_at)}</TableCell>
                      <TableCell className="text-gray-400">
                        {user.last_login ? formatDate(user.last_login) : "Nunca"}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8"
                            onClick={() => handleEditUser(user.username)}
                          >
                            <Edit className="h-4 w-4 mr-1" />
                            Editar
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-8 text-red-400"
                            onClick={() => handleDeactivateUser(user.username)}
                            disabled={!user.is_active}
                          >
                            <Ban className="h-4 w-4 mr-1" />
                            Desativar
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
