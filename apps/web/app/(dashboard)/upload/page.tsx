"use client";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useCompany } from "@/contexts/CompanyContext";
import { uploadDocument } from "@/lib/api";
import { AlertCircle, CheckCircle, FileText, Upload, X } from "lucide-react";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

export default function UploadPage() {
  const { selectedCompanyId } = useCompany();
  const [files, setFiles] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<Record<string, "success" | "error" | "uploading">>({});
  const [error, setError] = useState<string | null>(null);

  const ALLOWED_TYPES = [
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
  ];
  const MAX_SIZE = 50 * 1024 * 1024; // 50MB

  const onDrop = useCallback((acceptedFiles: File[], rejectedFiles: any[]) => {
    if (rejectedFiles.length > 0) {
      setError(`${rejectedFiles.length} arquivo(s) rejeitado(s). Verifique o tipo e tamanho.`);
      return;
    }

    setFiles((prev) => [...prev, ...acceptedFiles]);
    setError(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/pdf": [".pdf"],
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
      "text/plain": [".txt"],
    },
    maxSize: MAX_SIZE,
    multiple: true,
  });

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleUpload() {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);
    setUploadProgress(0);

    let successCount = 0;
    let errorCount = 0;

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!file) continue;
      setUploadStatus((prev) => ({ ...prev, [file.name]: "uploading" }));

      try {
        await uploadDocument(file, selectedCompanyId || "");
        setUploadStatus((prev) => ({ ...prev, [file.name]: "success" }));
        successCount++;
      } catch (err: unknown) {
        setUploadStatus((prev) => ({ ...prev, [file.name]: "error" }));
        errorCount++;
      }

      setUploadProgress(((i + 1) / files.length) * 100);
    }

    setUploading(false);
    setFiles([]);

    if (errorCount > 0) {
      setError(`${successCount} arquivo(s) enviado(s) com sucesso, ${errorCount} com erro.`);
    } else {
      setError(null);
    }
  }

  function getFileIcon(type: string) {
    if (type.includes("pdf")) return <FileText className="h-8 w-8 text-red-400" />;
    if (type.includes("sheet")) return <FileText className="h-8 w-8 text-green-400" />;
    return <FileText className="h-8 w-8 text-blue-400" />;
  }

  function getStatusIcon(status: string) {
    if (status === "success") return <CheckCircle className="h-5 w-5 text-green-400" />;
    if (status === "error") return <AlertCircle className="h-5 w-5 text-red-400" />;
    return null;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-white">Upload de Documentos</h1>
        <p className="text-gray-400 mt-1">
          Envie PDFs, Excel (.xlsx) ou SPED (.txt) para processamento
        </p>
      </div>

      {/* Drop Zone */}
      <Card className="bg-gray-900 border-gray-800">
        <CardContent className="p-6">
          <div
            {...getRootProps()}
            className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${isDragActive
              ? "border-indigo-500 bg-indigo-500/10"
              : "border-gray-700 hover:border-gray-600"
              }`}
          >
            <input {...getInputProps()} />
            <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-lg font-medium text-white mb-2">
              {isDragActive ? "Solte os arquivos aqui" : "Arraste e solte arquivos aqui"}
            </p>
            <p className="text-sm text-gray-400 mb-4">ou clique para selecionar</p>
            <p className="text-xs text-gray-500">
              PDF, Excel (.xlsx), SPED (.txt) • Máximo 50MB por arquivo
            </p>
          </div>
        </CardContent>
      </Card>

      {/* File List */}
      {files.length > 0 && (
        <Card className="bg-gray-900 border-gray-800">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-white">
                {files.length} arquivo(s) selecionado(s)
              </h3>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setFiles([])}
                disabled={uploading}
              >
                Limpar
              </Button>
            </div>

            <div className="space-y-3">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center gap-4 p-3 bg-gray-800 rounded-lg"
                >
                  {getFileIcon(file.type)}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">{file.name}</p>
                    <p className="text-xs text-gray-400">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                  {getStatusIcon(uploadStatus[file.name] || "")}
                  {!uploading && (
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => removeFile(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                </div>
              ))}
            </div>

            {uploading && (
              <div className="mt-4">
                <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-indigo-500 transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
                <p className="text-xs text-gray-400 mt-2 text-center">
                  {uploadProgress.toFixed(0)}% concluído
                </p>
              </div>
            )}

            <Button
              className="w-full mt-4"
              onClick={handleUpload}
              disabled={uploading}
            >
              {uploading ? "Enviando..." : "Enviar Todos"}
            </Button>
          </CardContent>
        </Card>
      )}

      {error && (
        <div className="bg-red-900/40 border border-red-500 rounded-lg p-4 text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
