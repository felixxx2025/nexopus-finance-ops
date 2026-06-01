# Acesso via IP Público - Configuração

## IP Público do Servidor
**195.182.200.216**

## Acesso Atual
- **Frontend:** http://195.182.200.216:3000
- **API:** http://195.182.200.216:8000

## Testes Realizados
✓ API acessível via IP público (porta 8000)
✓ Frontend acessível via IP público (porta 3000)
✓ CORS configurado para permitir IP público
✓ Login via API funcionando com IP público

## Configuração para Acesso Externo

### Opção 1: Usar script automatizado (RECOMENDADO)
```bash
./scripts/start-with-public-ip.sh
```

Este script:
- Detecta automaticamente o IP público
- Configura a variável de ambiente
- Inicia os containers com a configuração correta

### Opção 2: Passar variável no comando docker-compose
```bash
NEXT_PUBLIC_API_URL=http://195.182.200.216:8000 docker compose up -d --build web
```

### Opção 3: Usar localhost (acesso local)
Mantenha a configuração padrão para acesso local:
```bash
docker compose up -d
```

## Importante: Persistência da Configuração

A variável `NEXT_PUBLIC_API_URL` precisa ser definida a cada reinício do container web. Use o script `start-with-public-ip.sh` para garantir que a configuração seja aplicada sempre.

## Notas Importantes

1. **Firewall:** As portas 3000 e 8000 já estão expostas no Docker
2. **CORS:** A API já está configurada para aceitar requisições do IP público
3. **SSL:** Recomendado configurar SSL/HTTPS para produção
4. **Segurança:** Considere configurar autenticação adicional para acesso externo

## URLs de Acesso

### Local (Dentro do servidor)
- Frontend: http://localhost:3000
- API: http://localhost:8000

### Externo (Fora do servidor)
- Frontend: http://195.182.200.216:3000
- API: http://195.182.200.216:8000

## Próximos Passos Recomendados

1. Configurar domínio (via Cloudflare ou outro provedor)
2. Configurar SSL/HTTPS (Let's Encrypt via Cloudflare)
3. Configurar firewall para restringir acesso
4. Configurar rate limiting
5. Configurar backup automático
