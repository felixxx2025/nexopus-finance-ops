"use client";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  ColumnDef,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  SortingState,
  useReactTable,
} from "@tanstack/react-table";
import { Download, FileText, MoreVertical, Trash2 } from "lucide-react";
import { useState } from "react";

interface Document {
  id: string;
  name: string;
  type: "pdf" | "excel" | "sped";
  status: "uploaded" | "processing" | "parsed" | "error";
  size: number;
  uploadedAt: Date;
}

const MOCK_DOCUMENTS: Document[] = [
  {
    id: "1",
    name: "SPED_Fiscal_2026.txt",
    type: "sped",
    status: "parsed",
    size: 2450000,
    uploadedAt: new Date(Date.now() - 1000 * 60 * 30),
  },
  {
    id: "2",
    name: "DRE_Abril_2026.xlsx",
    type: "excel",
    status: "processing",
    size: 125000,
    uploadedAt: new Date(Date.now() - 1000 * 60 * 15),
  },
  {
    id: "3",
    name: "Nota_Fiscal_001.pdf",
    type: "pdf",
    status: "uploaded",
    size: 890000,
    uploadedAt: new Date(Date.now() - 1000 * 60 * 5),
  },
  {
    id: "4",
    name: "Balanco_2025.pdf",
    type: "pdf",
    status: "parsed",
    size: 3200000,
    uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 24),
  },
  {
    id: "5",
    name: "Lancamentos_Mar.xlsx",
    type: "excel",
    status: "error",
    size: 45000,
    uploadedAt: new Date(Date.now() - 1000 * 60 * 60 * 48),
  },
];

const STATUS_CONFIG = {
  uploaded: { label: "Enviado", color: "bg-blue-900/20 text-blue-400 border-blue-700" },
  processing: { label: "Processando", color: "bg-yellow-900/20 text-yellow-400 border-yellow-700" },
  parsed: { label: "Processado", color: "bg-green-900/20 text-green-400 border-green-700" },
  error: { label: "Erro", color: "bg-red-900/20 text-red-400 border-red-700" },
};

const TYPE_CONFIG = {
  pdf: { label: "PDF", color: "text-red-400" },
  excel: { label: "Excel", color: "text-green-400" },
  sped: { label: "SPED", color: "text-blue-400" },
};

export function DocumentList() {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [documents] = useState<Document[]>(MOCK_DOCUMENTS);

  const columns: ColumnDef<Document>[] = [
    {
      accessorKey: "name",
      header: "Nome",
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-gray-400" />
          <span className="font-medium text-white">{row.original.name}</span>
        </div>
      ),
    },
    {
      accessorKey: "type",
      header: "Tipo",
      cell: ({ row }) => {
        const config = TYPE_CONFIG[row.original.type];
        return <span className={`text-sm ${config.color}`}>{config.label}</span>;
      },
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: ({ row }) => {
        const config = STATUS_CONFIG[row.original.status];
        return (
          <Badge variant="outline" className={config.color}>
            {config.label}
          </Badge>
        );
      },
    },
    {
      accessorKey: "size",
      header: "Tamanho",
      cell: ({ row }) => (
        <span className="text-sm text-gray-400">
          {(row.original.size / 1024 / 1024).toFixed(2)} MB
        </span>
      ),
    },
    {
      accessorKey: "uploadedAt",
      header: "Enviado em",
      cell: ({ row }) => (
        <span className="text-sm text-gray-400">
          {row.original.uploadedAt.toLocaleDateString("pt-BR")}
        </span>
      ),
    },
    {
      id: "actions",
      cell: ({ row }) => (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon">
              <MoreVertical className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="bg-gray-800 border-gray-700">
            <DropdownMenuItem className="text-white hover:bg-gray-700">
              <Download className="h-4 w-4 mr-2" />
              Baixar
            </DropdownMenuItem>
            <DropdownMenuItem className="text-white hover:bg-gray-700">
              <FileText className="h-4 w-4 mr-2" />
              Visualizar
            </DropdownMenuItem>
            <DropdownMenuItem className="text-red-400 hover:bg-gray-700">
              <Trash2 className="h-4 w-4 mr-2" />
              Excluir
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      ),
    },
  ];

  const table = useReactTable({
    data: documents,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: setSorting,
    state: {
      sorting,
    },
  });

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader>
        <CardTitle className="text-lg text-white">Documentos</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border border-gray-700">
          <table className="w-full">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider"
                    >
                      {header.isPlaceholder
                        ? null
                        : header.column.columnDef.header as string}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-t border-gray-800 hover:bg-gray-800/50">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3">
                      {cell.getValue() as React.ReactNode}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="flex items-center justify-between mt-4">
          <p className="text-sm text-gray-400">
            Mostrando {table.getRowModel().rows.length} de {documents.length} documentos
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
            >
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="bg-gray-800 border-gray-700 text-white hover:bg-gray-700"
            >
              Próximo
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
