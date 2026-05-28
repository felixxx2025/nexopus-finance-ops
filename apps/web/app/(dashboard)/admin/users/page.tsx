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
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newUsername, setNewUsername] = useState("");
  const [newEmail, setNewEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

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
    const user = users.find(u => u.username === username);
    if (user) {
      setEditingUser(user);
      setNewUsername(user.username);
      setNewEmail(user.email || "");
      setNewPassword("");
      setShowEditModal(true);
    }
  };

  const handleUpdateUser = async () => {
    if (!editingUser || !newUsername.trim() || !newEmail.trim()) {
      alert("Por favor, preencha todos os campos.");
      return;
    }

    try {
      setIsEditing(true);
      const body: any = {
        username: newUsername,
        email: newEmail,
      };
      if (newPassword.trim()) {
        body.password = newPassword;
      }

      const res = await fetch(`${API_URL}/users/${editingUser.username}`, {
        method: "PATCH",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Reset form and close modal
      setNewUsername("");
      setNewEmail("");
      setNewPassword("");
      setEditingUser(null);
      setShowEditModal(false);
      loadUsers();
    } catch (err) {
      console.error("Error updating user:", err);
      alert(err instanceof Error ? err.message : "Erro ao atualizar usuário");
    } finally {
      setIsEditing(false);
    }
  };

  const handleCreateUser = async () => {
    if (!newUsername.trim() || !newEmail.trim() || !newPassword.trim()) {
      alert("Por favor, preencha todos os campos.");
      return;
    }

    try {
      setIsCreating(true);
      const res = await fetch(`${API_URL}/users`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: newUsername,
          email: newEmail,
          password: newPassword,
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Reset form and close modal
      setNewUsername("");
      setNewEmail("");
      setNewPassword("");
      setShowCreateModal(false);
      loadUsers();
    } catch (err) {
      console.error("Error creating user:", err);
      alert(err instanceof Error ? err.message : "Erro ao criar usuário");
    } finally {
      setIsCreating(false);
    }
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
          <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
            <DialogTrigger asChild>
              <Button>
                <UserPlus className="h-4 w-4 mr-2" />
                Novo Usuário
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-gray-900 border-gray-800 text-white">
              <DialogHeader>
                <DialogTitle>Criar Novo Usuário</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Preencha os dados para cadastrar um novo usuário no sistema.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Nome de Usuário</label>
                  <Input
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="Ex: joao.silva"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Email</label>
                  <Input
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="Ex: joao@empresa.com"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Senha</label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="••••••••"
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
                <Button onClick={handleCreateUser} disabled={isCreating}>
                  {isCreating ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Criando...
                    </>
                  ) : (
                    "Criar Usuário"
                  )}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={showEditModal} onOpenChange={setShowEditModal}>
            <DialogContent className="bg-gray-900 border-gray-800 text-white">
              <DialogHeader>
                <DialogTitle>Editar Usuário</DialogTitle>
                <DialogDescription className="text-gray-400">
                  Atualize os dados do usuário selecionado. Deixe a senha em branco para manter a atual.
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Nome de Usuário</label>
                  <Input
                    value={newUsername}
                    onChange={(e) => setNewUsername(e.target.value)}
                    placeholder="Ex: joao.silva"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Email</label>
                  <Input
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    placeholder="Ex: joao@empresa.com"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
                <div>
                  <label className="text-sm text-gray-400 block mb-1">Nova Senha (opcional)</label>
                  <Input
                    type="password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    placeholder="Deixe em branco para manter a senha atual"
                    className="bg-gray-800 border-gray-700 text-white"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={() => {
                    setShowEditModal(false);
                    setEditingUser(null);
                    setNewUsername("");
                    setNewEmail("");
                    setNewPassword("");
                  }}
                  disabled={isEditing}
                >
                  Cancelar
                </Button>
                <Button onClick={handleUpdateUser} disabled={isEditing}>
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
