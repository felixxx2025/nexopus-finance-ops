"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Settings, User, Bell, Shield, Database, Palette } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export default function SettingsPage() {
  const { user } = useAuth();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Configurações</h1>
        <p className="text-gray-400 mt-1">
          Gerencie suas preferências e configurações do sistema
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Perfil do Usuário */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <User className="h-5 w-5 text-indigo-400" />
              Perfil do Usuário
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-gray-400 block mb-1">Usuário</label>
              <div className="text-white font-medium">{user || "Não logado"}</div>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Email</label>
              <div className="text-white">admin@nexopus.com</div>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Status</label>
              <Badge className="bg-green-900/40 text-green-400 border-green-700">
                Ativo
              </Badge>
            </div>
            <Button variant="outline" className="w-full mt-4">
              Editar Perfil
            </Button>
          </CardContent>
        </Card>

        {/* Notificações */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Bell className="h-5 w-5 text-indigo-400" />
              Notificações
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Notificações por Email</div>
                <div className="text-sm text-gray-400">Receba alertas por email</div>
              </div>
              <div className="w-12 h-6 bg-indigo-600 rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Alertas de Compliance</div>
                <div className="text-sm text-gray-400">Notificações de não conformidade</div>
              </div>
              <div className="w-12 h-6 bg-indigo-600 rounded-full relative cursor-pointer">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded-full" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-white font-medium">Relatórios Semanais</div>
                <div className="text-sm text-gray-400">Resumo semanal por email</div>
              </div>
              <div className="w-12 h-6 bg-gray-700 rounded-full relative cursor-pointer">
                <div className="absolute left-1 top-1 w-4 h-4 bg-gray-400 rounded-full" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Segurança */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Shield className="h-5 w-5 text-indigo-400" />
              Segurança
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="text-white font-medium">Alterar Senha</div>
              <div className="text-sm text-gray-400 mb-2">Última alteração: 30 dias atrás</div>
              <Button variant="outline" size="sm">
                Alterar Senha
              </Button>
            </div>
            <div className="pt-4 border-t border-gray-800">
              <div className="text-white font-medium">Autenticação em Dois Fatores</div>
              <div className="text-sm text-gray-400 mb-2">Proteção adicional para sua conta</div>
              <Badge className="bg-gray-700 text-gray-300 border-gray-600">
                Não configurado
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Preferências do Sistema */}
        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Palette className="h-5 w-5 text-indigo-400" />
              Preferências
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm text-gray-400 block mb-1">Idioma</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option>Português (Brasil)</option>
                <option>English</option>
                <option>Español</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Fuso Horário</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option>America/São Paulo (UTC-3)</option>
                <option>America/New_York (UTC-5)</option>
                <option>Europe/London (UTC+0)</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-gray-400 block mb-1">Formato de Data</label>
              <select className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white">
                <option>DD/MM/YYYY</option>
                <option>MM/DD/YYYY</option>
                <option>YYYY-MM-DD</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Dados e Integrações */}
        <Card className="bg-gray-900 border-gray-800 md:col-span-2">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Database className="h-5 w-5 text-indigo-400" />
              Dados e Integrações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-gray-800 rounded-lg">
                <div className="text-white font-medium mb-1">Exportar Dados</div>
                <div className="text-sm text-gray-400 mb-3">Exporte todos os dados da empresa</div>
                <Button variant="outline" size="sm" className="w-full">
                  Exportar
                </Button>
              </div>
              <div className="p-4 bg-gray-800 rounded-lg">
                <div className="text-white font-medium mb-1">Integrações</div>
                <div className="text-sm text-gray-400 mb-3">Configure integrações externas</div>
                <Button variant="outline" size="sm" className="w-full">
                  Configurar
                </Button>
              </div>
              <div className="p-4 bg-gray-800 rounded-lg">
                <div className="text-white font-medium mb-1">API Keys</div>
                <div className="text-sm text-gray-400 mb-3">Gerencie chaves de API</div>
                <Button variant="outline" size="sm" className="w-full">
                  Gerenciar
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
