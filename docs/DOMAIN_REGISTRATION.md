# Registro de Domínio via API - Análise e Limitações

## Conclusão: Não existe API pública para registro de domínio 100% grátis

Após investigação detalhada, **não há serviços de domínio 100% grátis que ofereçam API pública para registro automatizado**. Todos os serviços grátis exigem registro manual inicial.

---

## Opções Disponíveis

### 1. DuckDNS (Recomendado para desenvolvimento)
- **Tipo:** Subdomínio grátis (ex: `nexopus-finance.duckdns.org`)
- **Registro:** Manual via site (https://www.duckdns.org)
- **API:** Disponível apenas para ATUALIZAÇÃO DDNS (não registro)
- **Custo:** 100% grátis
- **Vantagens:** Fácil, estável, suporta DDNS automático
- **Limitações:** Apenas subdomínios, registro inicial manual

#### Processo:
1. Acessar https://www.duckdns.org
2. Fazer login (GitHub, Google, Twitter, Reddit, Email)
3. Criar subdomínio manualmente
4. Usar script `scripts/duckdns-update.py` para atualização DDNS automática

#### Exemplo de uso do script:
```bash
# Atualizar com detecção automática de IP
python scripts/duckdns-update.py nexopus-finance SEU_TOKEN

# Atualizar com IP específico
python scripts/duckdns-update.py nexopus-finance SEU_TOKEN 192.168.1.100
```

---

### 2. EU.org
- **Tipo:** Subdomínio grátis (ex: `nexopus-finance.eu.org`)
- **Registro:** Manual via formulário (https://nic.eu.org/register.html)
- **API:** Não disponível
- **Custo:** 100% grátis
- **Vantagens:** Domínio mais "profissional"
- **Limitações:** Processo manual, aprovação pode demorar, sem API

---

### 3. Domínio Próprio com API (Recomendado para produção)
- **Tipo:** Domínio completo (ex: `nexopus-finance.com`)
- **Registro:** Via API (automatizado)
- **API:** Completamente disponível
- **Custo:** ~$10-15/ano
- **Vantagens:** Controle total, API completa, profissional
- **Provedores com API:**
  - **NameSilo:** API gratuita, domínios baratos (~$8-10/ano)
  - **Cloudflare Registrar:** API gratuita, preço de custo
  - **DNSimple:** API completa, mais caro

#### Exemplo com NameSilo API:
```python
import requests

# Registro automatizado via API
api_key = "YOUR_API_KEY"
domain = "nexopus-finance.com"

response = requests.post(
    "https://www.namesilo.com/api/registerDomain",
    params={
        "key": api_key,
        "domain": domain,
        "years": 1,
        "auto_renew": 1
    }
)
```

---

## Recomendação

### Para Desenvolvimento/Teste:
**Use DuckDNS**
- Registro manual inicial (5 minutos)
- Script Python para atualização DDNS automática
- 100% grátis
- Adequado para ambiente de desenvolvimento

### Para Produção:
**Compre um domínio próprio**
- Custo: ~$10/ano (menos de $1/mês)
- API completa para automação
- Aparência profissional
- Controle total do DNS

---

## Script DuckDNS Criado

Já criei o script `scripts/duckdns-update.py` para atualização DDNS automática via API do DuckDNS.

**Uso:**
```bash
python scripts/duckdns-update.py <subdomain> <token> [ip] [ipv6]
```

**Exemplo:**
```bash
python scripts/duckdns-update.py nexopus-finance abc123def456
```

---

## Próximos Passos

### Opção A: DuckDNS (Grátis)
1. Acessar https://www.duckdns.org
2. Fazer login e criar subdomínio
3. Obter token
4. Usar script para atualização DDNS
5. Configurar cron job ou container para atualização automática

### Opção B: Domínio Próprio (Pago)
1. Criar conta em NameSilo/Cloudflare
2. Obter API key
3. Usar API para registrar domínio
4. Configurar DNS para apontar para servidor
5. Configurar SSL (Let's Encrypt)

---

## Configuração DDNS Automática (DuckDNS)

Para atualização automática do IP, você pode:

### 1. Cron Job (Linux)
```bash
# Adicionar ao crontab
*/5 * * * * /usr/bin/python3 /path/to/duckdns-update.py nexopus-finance SEU_TOKEN
```

### 2. Container Docker
Adicionar ao docker-compose.yml:
```yaml
services:
  duckdns-update:
    image: python:3-slim
    command: python /app/duckdns-update.py nexopus-finance ${DUCKDNS_TOKEN}
    volumes:
      - ./scripts:/app
    environment:
      - DUCKDNS_TOKEN=${DUCKDNS_TOKEN}
    restart: unless-stopped
```

---

## Conclusão

Infelizmente, **não é possível registrar um domínio 100% grátis via API**. Os serviços grátis exigem registro manual inicial.

Para automação completa, a única opção é comprar um domínio próprio (~$10/ano) e usar a API do registrador.

Para desenvolvimento, recomendo DuckDNS com registro manual inicial e atualização DDNS via API.
