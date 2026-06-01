"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useCompany } from "@/contexts/CompanyContext";
import {
  createDocument,
  deleteDocument,
  fetchDocument,
  fetchDocuments,
  updateDocument,
} from "@/lib/api";
import { Download, Eye, FilePlus, FileSpreadsheet, FileText, Image as ImageIcon, Loader2, Pencil, Search, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Document {
  id: string;
  filename: string;
  type: string;
  status: string;
  parsed: boolean;
  error_message: string | null;
  ai_confidence: number | null;
  created_at: string;
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
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingDocument, setEditingDocument] = useState<Document | null>(null);
  const [formData, setFormData] = useState({
    file_url: "",
    original_filename: "",
    type: "pdf",
    status: "uploaded",
  });

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
      doc.filename.toLowerCase().includes(searchQuery.toLowerCase());
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

  const handleCreate = async () => {
    if (!selectedCompanyId) {
      setError("Selecione uma empresa primeiro");
      return;
    }
    try {
      setIsLoading(true);
      await createDocument({
        company_id: selectedCompanyId,
        file_url: formData.file_url,
        original_filename: formData.original_filename,
        type: formData.type,
        status: formData.status,
      });
      setIsModalOpen(false);
      resetForm();
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar documento");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingDocument) return;
    try {
      setIsLoading(true);
      await updateDocument(editingDocument.id, {
        status: formData.status,
      });
      setIsModalOpen(false);
      resetForm();
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar documento");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Tem certeza que deseja excluir este documento?")) return;
    try {
      setIsLoading(true);
      await deleteDocument(id);
      loadDocuments();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir documento");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = async (doc: Document) => {
    try {
      const fullDoc = await fetchDocument(doc.id);
      setEditingDocument(doc);
      setFormData({
        file_url: fullDoc.file_url,
        original_filename: fullDoc.filename,
        type: fullDoc.type,
        status: fullDoc.status,
      });
      setIsModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar documento");
    }
  };

  const resetForm = () => {
    setFormData({
      file_url: "",
      original_filename: "",
      type: "pdf",
      status: "uploaded",
    });
    setEditingDocument(null);
  };

  const openModal = () => {
    resetForm();
    setIsModalOpen(true);
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
          <Button onClick={openModal}>
            <FilePlus className="h-4 w-4 mr-2" />
            Novo Documento
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
                  <TableHead className="text-gray-400">Processado</TableHead>
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
                          {doc.filename}
                        </TableCell>
                        <TableCell className="text-gray-300 uppercase text-xs">
                          {doc.type}
                        </TableCell>
                        <TableCell className="text-gray-400">-</TableCell>
                        <TableCell className="text-gray-400">{formatDate(doc.created_at)}</TableCell>
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
                              onClick={() => handleDownload(doc.id, doc.filename)}
                              title="Baixar"
                            >
                              <Download className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleEdit(doc)}
                              title="Editar"
                            >
                              <Pencil className="h-4 w-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-8 w-8"
                              onClick={() => handleDelete(doc.id)}
                              title="Excluir"
                            >
                              <Trash2 className="h-4 w-4 text-red-400" />
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

      {/* Modal for Create/Edit */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="bg-gray-900 border-gray-800 w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">
                  {editingDocument ? "Editar Documento" : "Novo Documento"}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label className="text-gray-300">URL do Arquivo</Label>
                <Input
                  value={formData.file_url}
                  onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-white mt-1"
                  placeholder="http://minio:9000/arquivo.pdf"
                />
              </div>
              <div>
                <Label className="text-gray-300">Nome do Arquivo</Label>
                <Input
                  value={formData.original_filename}
                  onChange={(e) => setFormData({ ...formData, original_filename: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-white mt-1"
                  placeholder="documento.pdf"
                />
              </div>
              <div>
                <Label className="text-gray-300">Tipo</Label>
                <select
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-white mt-1 w-full rounded-lg px-3 py-2"
                >
                  <option value="pdf">PDF</option>
                  <option value="excel">Excel</option>
                  <option value="sped">SPED</option>
                </select>
              </div>
              <div>
                <Label className="text-gray-300">Status</Label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="bg-gray-800 border-gray-700 text-white mt-1 w-full rounded-lg px-3 py-2"
                >
                  <option value="uploaded">Enviado</option>
                  <option value="processing">Processando</option>
                  <option value="processed">Processado</option>
                  <option value="failed">Falhou</option>
                </select>
              </div>
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                  Cancelar
                </Button>
                <Button onClick={editingDocument ? handleUpdate : handleCreate} disabled={isLoading}>
                  {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                  {editingDocument ? "Atualizar" : "Criar"}
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
