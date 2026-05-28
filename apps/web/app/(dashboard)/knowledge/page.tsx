"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  fetchAccountTemplates,
  fetchKnowledgeArticles,
  fetchReportTemplates,
  searchKnowledge,
} from "@/lib/api";
import { BookOpen, FileText, Lightbulb, Loader2, Search } from "lucide-react";
import { useEffect, useState } from "react";

interface Article {
  id: string;
  title: string;
  category: string;
  content: string;
  tags: string[];
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
        <Button variant="outline" size="sm" onClick={loadKnowledge}>
          <Loader2 className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Atualizar
        </Button>
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
                          </div>
                        </CardHeader>
                        <CardContent>
                          <p className="text-gray-400 text-sm">{article.content}</p>
                          <Button variant="outline" size="sm" className="mt-3">
                            Ler mais
                          </Button>
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
    </div>
  );
}
