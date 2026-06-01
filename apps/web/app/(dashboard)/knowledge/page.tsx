"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  createKnowledgeArticle,
  deleteKnowledgeArticle,
  fetchAccountTemplates,
  fetchKnowledgeArticle,
  fetchKnowledgeArticles,
  fetchReportTemplates,
  searchKnowledge,
  updateKnowledgeArticle,
  uploadKnowledgePDF,
} from "@/lib/api";
import { BookOpen, FileText, Lightbulb, Loader2, Pencil, Plus, Search, Trash2, Upload, X } from "lucide-react";
import { useEffect, useState } from "react";

interface Article {
  id: string;
  title: string;
  category: string;
  subcategory?: string;
  content: string;
  tags: string[];
  source?: string;
  source_url?: string;
  created_at: string;
}

interface Template {
  id: string;
  name: string;
  category: string;
  description: string;
}

export default function KnowledgePage() {
  const [articles, setArticles] = useState<Article[]>([]);
  const [reportTemplates, setReportTemplates] = useState<Template[]>([]);
  const [accountTemplates, setAccountTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingArticle, setEditingArticle] = useState<Article | null>(null);
  const [formData, setFormData] = useState({
    title: "",
    content: "",
    category: "conceito",
    subcategory: "",
    tags: "",
    source: "",
    source_url: "",
  });
  const [isUploading, setIsUploading] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);

  useEffect(() => {
    loadKnowledge();
  }, []);

  const loadKnowledge = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const [articlesData, reportsData, accountsData] = await Promise.all([
        fetchKnowledgeArticles({ limit: 100 }),
        fetchReportTemplates(),
        fetchAccountTemplates(),
      ]);
      setArticles(articlesData.articles);
      setReportTemplates(reportsData.templates);
      setAccountTemplates(accountsData.templates);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar base de conhecimento");
      console.error("Error loading knowledge:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadKnowledge();
      return;
    }
    try {
      const results = await searchKnowledge(searchQuery);
      // Convert search results to article format
      setArticles(
        results.results.map((r) => ({
          id: r.id,
          title: r.title,
          category: r.category,
          content: r.snippet,
          tags: [],
          created_at: "",
        }))
      );
    } catch (err) {
      console.error("Error searching knowledge:", err);
    }
  };

  const handleCreate = async () => {
    try {
      setIsLoading(true);
      const tags = formData.tags.split(",").map(t => t.trim()).filter(t => t);
      await createKnowledgeArticle({
        title: formData.title,
        content: formData.content,
        category: formData.category,
        subcategory: formData.subcategory || undefined,
        tags: tags.length > 0 ? tags : undefined,
        source: formData.source || undefined,
        source_url: formData.source_url || undefined,
      });
      setIsModalOpen(false);
      resetForm();
      loadKnowledge();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar artigo");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!editingArticle) return;
    try {
      setIsLoading(true);
      const tags = formData.tags.split(",").map(t => t.trim()).filter(t => t);
      await updateKnowledgeArticle(editingArticle.id, {
        title: formData.title,
        content: formData.content,
        category: formData.category,
        subcategory: formData.subcategory || undefined,
        tags: tags.length > 0 ? tags : undefined,
        source: formData.source || undefined,
        source_url: formData.source_url || undefined,
      });
      setIsModalOpen(false);
      resetForm();
      loadKnowledge();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar artigo");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("Tem certeza que deseja excluir este artigo?")) return;
    try {
      setIsLoading(true);
      await deleteKnowledgeArticle(id);
      loadKnowledge();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao excluir artigo");
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = async (article: Article) => {
    try {
      const fullArticle = await fetchKnowledgeArticle(article.id);
      setEditingArticle(article);
      setFormData({
        title: fullArticle.title,
        content: fullArticle.content,
        category: fullArticle.category,
        subcategory: fullArticle.subcategory || "",
        tags: fullArticle.tags?.join(", ") || "",
        source: fullArticle.source || "",
        source_url: fullArticle.source_url || "",
      });
      setIsModalOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar artigo");
    }
  };

  const handleUploadPDF = async () => {
    if (!uploadFile) return;
    try {
      setIsUploading(true);
      await uploadKnowledgePDF(uploadFile, formData.title || uploadFile.name, formData.category);
      setIsModalOpen(false);
      resetForm();
      loadKnowledge();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao fazer upload de PDF");
    } finally {
      setIsUploading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      content: "",
      category: "conceito",
      subcategory: "",
      tags: "",
      source: "",
      source_url: "",
    });
    setEditingArticle(null);
    setUploadFile(null);
  };

  const openModal = () => {
    resetForm();
    setIsModalOpen(true);
  };

  const filteredArticles = articles.filter((article) => {
    const matchesCategory =
      selectedCategory === "all" || article.category === selectedCategory;
    return matchesCategory;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Base de Conhecimento</h1>
          <p className="text-gray-400 mt-1">
            Artigos, templates e documentação do sistema
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadKnowledge}>
            <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
            Atualizar
          </Button>
          <Button variant="default" size="sm" onClick={openModal}>
            <Plus className="h-4 w-4 mr-2" />
            Novo Artigo
          </Button>
        </div>
      </div>

      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                placeholder="Buscar artigos..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="bg-gray-800 border-gray-700 text-white pl-10"
              />
            </div>
            <Button onClick={handleSearch}>Buscar</Button>
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
              <Button variant="outline" size="sm" onClick={loadKnowledge} className="mt-4">
                Tentar novamente
              </Button>
            </div>
          ) : (
            <Tabs defaultValue="articles" className="space-y-4">
              <TabsList className="bg-gray-800 border-gray-700">
                <TabsTrigger value="articles" className="data-[state=active]:bg-gray-700">
                  <BookOpen className="h-4 w-4 mr-2" />
                  Artigos
                </TabsTrigger>
                <TabsTrigger value="templates" className="data-[state=active]:bg-gray-700">
                  <FileText className="h-4 w-4 mr-2" />
                  Templates
                </TabsTrigger>
                <TabsTrigger value="tips" className="data-[state=active]:bg-gray-700">
                  <Lightbulb className="h-4 w-4 mr-2" />
                  Dicas
                </TabsTrigger>
              </TabsList>

              <TabsContent value="articles">
                <div className="space-y-3">
                  {filteredArticles.length === 0 ? (
                    <p className="text-gray-400 text-center py-4">Nenhum artigo encontrado</p>
                  ) : (
                    filteredArticles.map((article) => (
                      <Card key={article.id} className="bg-gray-800 border-gray-700 hover:border-gray-600 transition-colors">
                        <CardHeader>
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1">
                              <CardTitle className="text-white text-lg">{article.title}</CardTitle>
                              <div className="flex items-center gap-2 mt-2">
                                <Badge variant="outline" className="border-indigo-700 text-indigo-400">
                                  {article.category}
                                </Badge>
                                {article.tags.map((tag) => (
                                  <Badge key={tag} variant="outline" className="border-gray-700 text-gray-400 text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                            <div className="flex gap-2">
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(article)}>
                                <Pencil className="h-4 w-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(article.id)}>
                                <Trash2 className="h-4 w-4 text-red-400" />
                              </Button>
                            </div>
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-gray-400 text-sm">{article.content}</p>
                        </CardContent>
                      </Card>
                    ))
                  )}
                </div>
              </TabsContent>

              <TabsContent value="templates">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...reportTemplates, ...accountTemplates].map((template) => (
                    <Card key={template.id} className="bg-gray-800 border-gray-700">
                      <CardHeader>
                        <CardTitle className="text-white">{template.name}</CardTitle>
                        <Badge variant="outline" className="w-fit border-indigo-700 text-indigo-400">
                          {template.category}
                        </Badge>
                      </CardHeader>
                      <CardContent>
                        <p className="text-gray-400 text-sm mb-4">{template.description}</p>
                        <Button variant="outline" size="sm" className="w-full">
                          Usar Template
                        </Button>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </TabsContent>

              <TabsContent value="tips">
                <Card className="bg-gray-800 border-gray-700">
                  <CardContent className="p-6">
                    <div className="text-center text-gray-400">
                      <Lightbulb className="h-12 w-12 mx-auto mb-4 text-yellow-400" />
                      <p>Dicas e melhores práticas em breve</p>
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            </Tabs>
          )}
        </CardContent>
      </Card>

      {/* Modal for Create/Edit/Upload */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <Card className="bg-gray-900 border-gray-800 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">
                  {editingArticle ? "Editar Artigo" : "Novo Artigo"}
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setIsModalOpen(false)}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <Tabs defaultValue="manual" className="w-full">
                <TabsList className="bg-gray-800 border-gray-700 w-full">
                  <TabsTrigger value="manual" className="data-[state=active]:bg-gray-700 flex-1">
                    Manual
                  </TabsTrigger>
                  <TabsTrigger value="upload" className="data-[state=active]:bg-gray-700 flex-1">
                    <Upload className="h-4 w-4 mr-2" />
                    Upload PDF
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="manual" className="space-y-4 mt-4">
                  <div>
                    <Label className="text-gray-300">Título</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Categoria</Label>
                    <Input
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                      placeholder="conceito, norma, glossario, etc."
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Subcategoria (opcional)</Label>
                    <Input
                      value={formData.subcategory}
                      onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Conteúdo</Label>
                    <textarea
                      value={formData.content}
                      onChange={(e) => setFormData({ ...formData, content: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1 min-h-[200px] w-full rounded-lg p-3"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Tags (separadas por vírgula)</Label>
                    <Input
                      value={formData.tags}
                      onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Fonte (opcional)</Label>
                    <Input
                      value={formData.source}
                      onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">URL da Fonte (opcional)</Label>
                    <Input
                      value={formData.source_url}
                      onChange={(e) => setFormData({ ...formData, source_url: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-4">
                    <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                      Cancelar
                    </Button>
                    <Button onClick={editingArticle ? handleUpdate : handleCreate} disabled={isLoading}>
                      {isLoading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      {editingArticle ? "Atualizar" : "Criar"}
                    </Button>
                  </div>
                </TabsContent>

                <TabsContent value="upload" className="space-y-4 mt-4">
                  <div>
                    <Label className="text-gray-300">Arquivo PDF</Label>
                    <Input
                      type="file"
                      accept=".pdf"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Título (opcional)</Label>
                    <Input
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                      placeholder="Usará nome do arquivo se vazio"
                    />
                  </div>
                  <div>
                    <Label className="text-gray-300">Categoria</Label>
                    <Input
                      value={formData.category}
                      onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                      className="bg-gray-800 border-gray-700 text-white mt-1"
                      placeholder="conceito, norma, glossario, etc."
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-4">
                    <Button variant="outline" onClick={() => setIsModalOpen(false)}>
                      Cancelar
                    </Button>
                    <Button onClick={handleUploadPDF} disabled={!uploadFile || isUploading}>
                      {isUploading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : null}
                      Upload
                    </Button>
                  </div>
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
