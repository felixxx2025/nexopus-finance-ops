# Registro de Domínio via Cloudflare Registrar API

## Visão Geral

O **Cloudflare Registrar** oferece uma API completa para registro de domínios com as seguintes características:

- **Preço:** Custo de atacado (sem markup)
- **API:** Completamente disponível e gratuita
- **Privacidade WHOIS:** Incluída gratuitamente
- **Auto-renovação:** Configurável
- **Integração:** Total com Cloudflare DNS

---

## Requisitos

### 1. Conta Cloudflare
- Criar conta em https://dash.cloudflare.com/sign-up
- Ativar Cloudflare Registrar (pode requerer aprovação)

### 2. API Token
- Acessar: https://dash.cloudflare.com/profile/api-tokens
- Criar token com permissões:
  - **Account** > **Registrar** > **Edit**
- Copiar o token gerado

### 3. Account ID
- Acessar: https://dash.cloudflare.com
- URL mostrará: `https://dash.cloudflare.com/<ACCOUNT_ID>/...`
- Copiar o `<ACCOUNT_ID>`

### 4. Método de Pagamento
- Configurar cartão de crédito na conta Cloudflare
- Necessário para cobrança automática

---

## Preços (Custo de Atacado)

| TLD | Registro | Renovação |
|-----|----------|-----------|
| .com | $8.57 | $8.57 |
| .dev | $10.11 | $10.11 |
| .app | $11.00 | $11.00 |
| .io | $32.99 | $32.99 |
| .ai | $89.99 | $89.99 |

*Preços aproximados, sujeitos a alterações*

---

## Script Python Criado

**Arquivo:** `scripts/cloudflare-register.py`

Script completo para interagir com a API do Cloudflare Registrar.

### Funcionalidades

1. **Search** - Busca sugestões de domínios
2. **Check** - Verifica disponibilidade em tempo real
3. **Register** - Registra domínio automaticamente

---

## Uso do Script

### 1. Buscar Sugestões de Domínios

```bash
python scripts/cloudflare-register.py <API_TOKEN> <ACCOUNT_ID> search "nexopus finance"
```

**Exemplo de saída:**
```
Buscando domínios para: nexopus finance

================================================================================
DOMÍNIOS ENCONTRADOS
================================================================================

1. nexopusfinance.com
   Status: ✓ Disponível
   Tipo: standard
   Registro: USD $8.57
   Renovação: USD $8.57

2. nexopus-finance.dev
   Status: ✓ Disponível
   Tipo: standard
   Registro: USD $10.11
   Renovação: USD $10.11

3. nexopusfinance.app
   Status: ✓ Disponível
   Tipo: standard
   Registro: USD $11.00
   Renovação: USD $11.00
```

### 2. Verificar Disponibilidade

```bash
python scripts/cloudflare-register.py <API_TOKEN> <ACCOUNT_ID> check nexopus-finance.dev
```

**Exemplo de saída:**
```
Verificando disponibilidade: nexopus-finance.dev

================================================================================
DISPONIBILIDADE ATUAL
================================================================================

nexopus-finance.dev
   Status: ✓ Disponível
   Preço: USD $10.11
```

### 3. Registrar Domínio

```bash
python scripts/cloudflare-register.py <API_TOKEN> <ACCOUNT_ID> register nexopus-finance.dev
```

**Exemplo de saída:**
```
Verificando disponibilidade: nexopus-finance.dev

nexopus-finance.dev
   Status: ✓ Disponível
   Preço: USD $10.11

Preço de registro: USD $10.11

Confirmar registro de nexopus-finance.dev? (s/n): s

Registrando nexopus-finance.dev...
✓ Domínio nexopus-finance.dev registrado com sucesso!

Detalhes:
  Expira em: 2027-06-01T10:00:00Z
  Auto-renovação: Sim
  Privacidade WHOIS: Ativada
```

---

## Fluxo Completo de Registro

### Passo 1: Buscar Sugestões
```bash
python scripts/cloudflare-register.py TOKEN ACCOUNT search "nexopus finance"
```

### Passo 2: Verificar Disponibilidade
```bash
python scripts/cloudflare-register.py TOKEN ACCOUNT check nexopus-finance.dev
```

### Passo 3: Registrar Domínio
```bash
python scripts/cloudflare-register.py TOKEN ACCOUNT register nexopus-finance.dev
```

---

## Configuração DNS Após Registro

Após registrar o domínio, configure os registros DNS:

### Via Dashboard Cloudflare
1. Acessar: https://dash.cloudflare.com
2. Selecionar o domínio registrado
3. Adicionar registros DNS:
   - **A:** `@` → `SEU_IP_SERVIDOR`
   - **A:** `www` → `SEU_IP_SERVIDOR`
   - **CNAME:** `api` → `SEU_IP_SERVIDOR` (se necessário)

### Via API Cloudflare
```python
import requests

headers = {
    "Authorization": "Bearer YOUR_API_TOKEN",
    "Content-Type": "application/json"
}

# Adicionar registro A
data = {
    "type": "A",
    "name": "@",
    "content": "SEU_IP_SERVIDOR",
    "ttl": 1,
    "proxied": True
}

response = requests.post(
    f"https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_records",
    headers=headers,
    json=data
)
```

---

## Configuração SSL (Let's Encrypt)

O Cloudflare oferece SSL gratuito automaticamente:

1. Ativar **SSL/TLS** no dashboard
2. Modo: **Full** ou **Full (Strict)**
3. Certificado Let's Encrypt gerado automaticamente

---

## Variáveis de Ambiente

Para facilitar o uso, configure variáveis de ambiente:

```bash
# Linux/Mac
export CLOUDFLARE_API_TOKEN="seu_token_aqui"
export CLOUDFLARE_ACCOUNT_ID="seu_account_id_aqui"

# Windows (PowerShell)
$env:CLOUDFLARE_API_TOKEN="seu_token_aqui"
$env:CLOUDFLARE_ACCOUNT_ID="seu_account_id_aqui"
```

Uso simplificado:
```bash
python scripts/cloudflare-register.py $CLOUDFLARE_API_TOKEN $CLOUDFLARE_ACCOUNT_ID search "nexopus finance"
```

---

## Atualização da Aplicação

Após registrar o domínio, atualize as configurações:

### 1. docker-compose.yml
```yaml
web:
  environment:
    NEXT_PUBLIC_API_URL: https://api.nexopus-finance.dev
    API_INTERNAL_URL: http://api:8000
```

### 2. apps/api/config.py
```python
allowed_origins: str = "https://nexopus-finance.dev,https://api.nexopus-finance.dev"
```

### 3. apps/web/lib/api.ts
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://api.nexopus-finance.dev";
```

---

## Vantagens do Cloudflare Registrar

1. **Preço de Custo:** Sem markup, paga apenas o preço de registro
2. **API Completa:** Registro, renovação, DNS tudo via API
3. **Privacidade Gratuita:** WHOIS privacy incluído
4. **Integração DNS:** Gerenciamento DNS unificado
5. **SSL Grátis:** Let's Encrypt automático
6. **Segurança:** Proteção DDoS, WAF incluído
7. **Performance:** CDN global

---

## Limitações

- **Disponibilidade:** Cloudflare Registrar pode não estar disponível em todos os países
- **Aprovação:** Pode requerer aprovação manual da conta
- **TLDs:** Nem todas as extensões estão disponíveis
- **Não Reembolsável:** Registros de domínio não são reembolsáveis

---

## Alternativas com API

Se Cloudflare Registrar não estiver disponível:

### NameSilo
- **Preço:** ~$8-10/ano para .com
- **API:** Gratuita e completa
- **Site:** https://www.namesilo.com/

### DNSimple
- **Preço:** ~$15/ano para .com
- **API:** Completa e bem documentada
- **Site:** https://dnsimple.com/

---

## Exemplo de Integração com Docker

Adicionar serviço para atualização DNS:

```yaml
services:
  cloudflare-ddns:
    image: python:3-slim
    command: python /app/cloudflare-ddns.py
    volumes:
      - ./scripts:/app
    environment:
      - CLOUDFLARE_API_TOKEN=${CLOUDFLARE_API_TOKEN}
      - CLOUDFLARE_ZONE_ID=${CLOUDFLARE_ZONE_ID}
      - DOMAIN=nexopus-finance.dev
    restart: unless-stopped
```

---

## Conclusão

O **Cloudflare Registrar** é a melhor opção para registro de domínio via API devido a:

- Preço de atacado (mais barato que concorrentes)
- API completa e gratuita
- Integração nativa com DNS e SSL
- Privacidade WHOIS gratuita
- Performance e segurança incluídas

Para o projeto Nexopus Finance, recomendo registrar um domínio `.dev` ou `.com` via Cloudflare Registrar API usando o script fornecido.
