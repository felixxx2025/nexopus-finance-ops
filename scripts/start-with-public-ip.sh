#!/bin/bash
# Script para iniciar o Nexopus Finance com IP público configurado

# Obter IP público
PUBLIC_IP=$(curl -s ifconfig.me)
echo "IP Público detectado: $PUBLIC_IP"

# Definir variável de ambiente
export NEXT_PUBLIC_API_URL="http://${PUBLIC_IP}:8000"

# Iniciar containers
echo "Iniciando containers com NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL"
docker compose up -d

echo ""
echo "Serviços iniciados:"
echo "  Frontend: http://${PUBLIC_IP}:3000"
echo "  API: http://${PUBLIC_IP}:8000"
