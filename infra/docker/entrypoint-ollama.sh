#!/bin/bash
set -e

echo "🚀 Iniciando Ollama com modelos financeiros..."

# Iniciar servidor Ollama em background
echo "🤖 Iniciando servidor Ollama..."
ollama serve &
OLLAMA_PID=$!

# Esperar um pouco para o servidor iniciar
echo "⏳ Aguardando servidor Ollama iniciar..."
sleep 10

# Baixar modelo Qwen3:8b (multilíngue, inclui português)
echo "🔍 Verificando se modelo Qwen3:8b já existe..."
if ! ollama list | grep -q "qwen3:8b"; then
    echo "📥 Baixando modelo Qwen3:8b (pode levar vários minutos)..."
    ollama pull qwen3:8b
    echo "✅ Modelo Qwen3:8b baixado com sucesso!"
else
    echo "✅ Modelo Qwen3:8b já está disponível"
fi

# Manter servidor rodando
echo "🎉 Ollama está pronto e rodando!"
wait $OLLAMA_PID
