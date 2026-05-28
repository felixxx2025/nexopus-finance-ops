"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompany } from "@/contexts/CompanyContext";
import { fetchDocuments } from "@/lib/api";
import { Download, Eye, FileSpreadsheet, FileText, Image as ImageIcon, Loader2, Search } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = "/api";

interface Document {
  id: string;
  name: string;
  type: string;
  size: string;
  uploaded_at: string;
  status: string;
  company_id?: string;
}

const FILE_ICONS = {
  pdf: FileText,
  xlsx: FileSpreadsheet,
  image: ImageIcon,
};

const STATUS_COLORS = {
  processed: "bg-green-900/40 text-green-400 border-green-700",
  processing: "bg-yellow-900/40 text-yellow-400 border-yellow-700",
  failed: "bg-red-900/40 text-red-400 border-red-700",
};

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const { selectedCompanyId } = useCompany();

  useEffect(() => {
    loadDocuments();
  }, [selectedCompanyId]);

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const data = await fetchDocuments({
        limit: 100,
        company_id: selectedCompanyId || undefined,
      });
      setDocuments(data.documents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar documentos");
      console.error("Error loading documents:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch =
      doc.name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus =
      selectedStatus === "all" || doc.status === selectedStatus;
    return matchesSearch && matchesStatus;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString("pt-BR");
  };

  const handleDownload = async (docId: string, docName: string) => {
    try {
      const res = await fetch(`${API_URL}/documents/${docId}/download`, {
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Download the file
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = docName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error("Error downloading document:", err);
      alert(err instanceof Error ? err.message : "Erro ao baixar documento");
    }
  };

  const handleView = async (docId: string) => {
    try {
      const res = await fetch(`${API_URL}/documents/${docId}/view`, {
        credentials: "include",
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Erro ${res.status}`);
      }

      // Open in new tab
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      window.open(url, "_blank");
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Error viewing document:", err);
      alert(err instanceof Error ? err.message : "Erro ao visualizar documento");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Documentos</h1>
          <p className="text-gray-400 mt-1">
            Gerencie e visualize todos os documentos do sistema
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={loadDocuments}>
            <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button>
            <Download className="h-4 w-4 mr-2" />
            Upload Novo
          </Button>
        </div>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 flex-1">
              <Search className="h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar documentos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="bg-gray-800 border-gray-700 text-white"
              />
            </div>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-gray-800 border-gray-700 text-white rounded-lg px-3 py-2 text-sm"
            >
              <option value="all">Todos os Status</option>
              <option value="processed">Processado</option>
              <option value="processing">Processando</option>
              <option value="failed">Falhou</option>
            </select>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : error ? (
            <div className="text-center py-8">
              <p className="text-red-400">{error}</p>
              <Button variant="outline" size="sm" onClick={loadDocuments} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="border-gray-700">
                  <TableHead className="text-gray-400">Nome</TableHead>
                  <TableHead className="text-gray-400">Tipo</TableHead>
                  <TableHead className="text-gray-400">Tamanho</TableHead>
                  <TableHead className="text-gray-400">Upload</TableHead>
                  <TableHead className="text-gray-400">Status</TableHead>
                  <TableHead className="text-gray-400">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDocs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center text-gray-400 py-8">
                      Nenhum documento encontrado
                    </TableCell>
                  </TableRow>
                ) : (
                  filteredDocs.map((doc) => {
                    const Icon = FILE_ICONS[doc.type as keyof typeof FILE_ICONS] || FileText;
                    return (
                      <TableRow key={doc.id} className="border-gray-800">
                        <TableCell className="text-white font-medium flex items-center gap-2">
                          <Icon className="h-4 w-4 text-gray-400" />
                          {doc.name}
                        </TableCell>
                        <TableCell className="text-gray-300 uppercase text-xs">
                          {doc.type}
                        </TableCell>
                        <TableCell className="text-gray-400">{doc.size}</TableCell>
                        <TableCell className="text-gray-400">{formatDate(doc.uploaded_at)}</TableCell>
                        <TableCell>
                          <Badge
                            variant="outline"
                            className={`border ${STATUS_COLORS[doc.status as keyof typeof STATUS_COLORS]}`}
                          >
                            {doc.status}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-2">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleView(doc.id)}
                              title="Visualizar"
                            >
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDownload(doc.id, doc.name)}
                              title="Baixar"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    );
                  })
                )}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
