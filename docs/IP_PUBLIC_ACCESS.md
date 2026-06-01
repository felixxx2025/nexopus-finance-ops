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

## Configuração para Acesso Externo

### Opção 1: Criar arquivo .env.local
Crie o arquivo `.env.local` na raiz do projeto com:

```bash
NEXT_PUBLIC_API_URL=http://195.182.200.216:8000
```

### Opção 2: Passar variável no comando docker-compose
```bash
NEXT_PUBLIC_API_URL=http://195.182.200.216:8000 docker compose up -d web
```

### Opção 3: Usar localhost (acesso local)
Mantenha a configuração padrão para acesso local:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

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
