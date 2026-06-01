# Acesso via IP Público - Configuração

## IP Público do Servidor
**195.182.200.216**

## ⚠️ Limitação Importante: Login via IP Público Requer SSL/HTTPS

O login via IP público **NÃO funciona com HTTP** devido a restrições de segurança do navegador:
- Cookies com `SameSite=Lax` não funcionam em contextos cross-site sem HTTPS
- Cookies com `SameSite=None` requerem `Secure=True`, que só funciona com HTTPS
- Navegadores modernos bloqueiam cookies cross-site em HTTP por segurança

## Solução: Use Localhost para Acesso Local

Para desenvolvimento/teste local, **use sempre localhost**:

```bash
docker compose up -d
```

Acesse: **http://localhost:3000**

## Para Acesso Externo: Configure SSL/HTTPS

Para acesso externo funcional, é **obrigatório** configurar SSL/HTTPS:

### Opção 1: Cloudflare (Recomendado)
1. Registrar domínio via Cloudflare Registrar
2. Configurar DNS para apontar para o IP público
3. Ativar SSL/TLS no Cloudflare (modo Full)
4. Usar URLs HTTPS: https://seu-dominio.com

### Opção 2: Let's Encrypt Direto
1. Configurar certbot no servidor
2. Gerar certificados SSL
3. Configurar nginx/traefik como proxy reverso
4. Usar URLs HTTPS

## Configuração Atual

### Local (Funciona com Login)
- **Frontend:** http://localhost:3000
- **API:** http://localhost:8000
- **Login:** ✓ Funciona

### Externo (Sem SSL - Login NÃO funciona)
- **Frontend:** http://195.182.200.216:3000
- **API:** http://195.182.200.216:8000
- **Login:** ✗ Não funciona (requer HTTPS)

## Script de Configuração

O script `start-with-public-ip.sh` está disponível, mas **não resolve o problema de login** sem SSL:

```bash
./scripts/start-with-public-ip.sh
```

Use este script apenas se você já tiver SSL/HTTPS configurado.

## Próximos Passos Recomendados

1. **Imediato:** Use http://localhost:3000 para acesso local
2. **Para produção:** Configure domínio + SSL/HTTPS via Cloudflare
3. **Segurança:** Configure firewall para restringir acesso externo
4. **Monitoramento:** Configure rate limiting e backup automático
