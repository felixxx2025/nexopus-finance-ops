# Secrets Manager Configuration Guide

## Overview

This guide explains how to configure a secrets manager for the Nexopus Finance Ops application to securely manage sensitive credentials and configuration.

## Recommended Solution: HashiCorp Vault

HashiCorp Vault is the recommended secrets manager for production deployments.

### Architecture

```
┌─────────────────┐
│   Application   │
│  (API, Web, etc)│
└────────┬────────┘
         │
         │ Fetch secrets
         │
┌────────▼────────┐
│   Vault Agent   │
│  (sidecar)      │
└────────┬────────┘
         │
         │ Authenticate
         │
┌────────▼────────┐
│  Vault Server   │
│  (centralized)  │
└─────────────────┘
```

### Installation

#### 1. Install Vault Server

```bash
# Using Docker
docker run -d \
  --name vault \
  --cap-add=IPC_LOCK \
  -p 8200:8200 \
  -e 'VAULT_DEV_ROOT_TOKEN_ID=myroot' \
  -e 'VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200' \
  hashicorp/vault:latest
```

#### 2. Initialize Vault (Production)

```bash
# Initialize Vault
vault operator init

# Unseal Vault (requires 3 of 5 keys)
vault operator unseal <key1>
vault operator unseal <key2>
vault operator unseal <key3>

# Login
vault login <root_token>
```

#### 3. Enable Secrets Engines

```bash
# Enable KV secrets engine
vault secrets enable -path=secret kv-v2

# Enable database secrets engine (for PostgreSQL)
vault secrets enable database

# Configure PostgreSQL
vault write database/config/postgresql \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@postgres:5432/${POSTGRES_DB}" \
    allowed_roles="nexopus-role"

# Create role
vault write database/roles/nexopus-role \
    db_name=postgresql \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}';" \
    default_ttl="1h" \
    max_ttl="24h"
```

#### 4. Store Application Secrets

```bash
# Store API secrets
vault kv put secret/nexopus/api \
    secret_key="${SECRET_KEY}" \
    github_ai_token="${GITHUB_AI_TOKEN}" \
    azure_inference_token="${AZURE_INFERENCE_TOKEN}" \
    redis_password="${REDIS_PASSWORD}"

# Store database credentials
vault kv put secret/nexopus/database \
    postgres_user="${POSTGRES_USER}" \
    postgres_password="${POSTGRES_PASSWORD}" \
    postgres_db="${POSTGRES_DB}"

# Store MinIO credentials
vault kv put secret/nexopus/minio \
    minio_root_user="${MINIO_ROOT_USER}" \
    minio_root_password="${MINIO_ROOT_PASSWORD}"

# Store RabbitMQ credentials
vault kv put secret/nexopus/rabbitmq \
    rabbitmq_user="${RABBITMQ_DEFAULT_USER}" \
    rabbitmq_password="${RABBITMQ_DEFAULT_PASS}"

# Store Grafana credentials
vault kv put secret/nexopus/grafana \
    grafana_user="${GRAFANA_USER}" \
    grafana_password="${GRAFANA_PASSWORD}"
```

### Integration with Docker Compose

#### 1. Add Vault to docker-compose.prod.yml

```yaml
vault:
  image: hashicorp/vault:latest
  cap_add:
    - IPC_LOCK
  ports:
    - "8200:8200"
  environment:
    VAULT_ADDR: "http://0.0.0.0:8200"
    VAULT_API_ADDR: "http://0.0.0.0:8200"
  volumes:
    - vault-data:/vault/data
    - ./infra/vault/config:/vault/config
  command: server
  networks:
    - nexopus-internal
  restart: unless-stopped
```

#### 2. Configure Vault Agent for Each Service

Create `infra/vault/config/api.hcl`:

```hcl
pid_file = "./pidfile"

auto_auth {
  method "kubernetes" {
    mount_path = "auth/kubernetes"
    config = {
      role = "nexopus-api"
    }
  }

  sink "file" {
    config = {
      path = "/vault/token"
    }
  }
}

template {
  source      = "/vault/config/api.ctmpl"
  destination = "/vault/secrets/.env"
  command     = "pkill -HUP uvicorn"
}
```

Create template file `infra/vault/config/api.ctmpl`:

```
{{ with secret "secret/nexopus/api" }}
SECRET_KEY="{{ .Data.data.secret_key }}"
GITHUB_AI_TOKEN="{{ .Data.data.github_ai_token }}"
AZURE_INFERENCE_TOKEN="{{ .Data.data.azure_inference_token }}"
{{ end }}

{{ with secret "secret/nexopus/database" }}
DATABASE_URL="postgresql+asyncpg://{{ .Data.data.postgres_user }}:{{ .Data.data.postgres_password }}@postgres:5432/{{ .Data.data.postgres_db }}"
SYNC_DATABASE_URL="postgresql://{{ .Data.data.postgres_user }}:{{ .Data.data.postgres_password }}@postgres:5432/{{ .Data.data.postgres_db }}"
{{ end }}

{{ with secret "secret/nexopus/redis" }}
REDIS_URL="redis://:{{ .Data.data.redis_password }}@redis:6379/0"
{{ end }}

{{ with secret "secret/nexopus/minio" }}
S3_ENDPOINT="http://minio:9000"
S3_ACCESS_KEY="{{ .Data.data.minio_root_user }}"
S3_SECRET_KEY="{{ .Data.data.minio_root_password }}"
{{ end }}
```

#### 3. Update Docker Compose Services

```yaml
api:
  image: ${REGISTRY:-ghcr.io}/${IMAGE_PREFIX:-nexopus}/api:${IMAGE_TAG:-latest}
  volumes:
    - ./infra/vault/config:/vault/config:ro
    - vault-secrets:/vault/secrets
  environment:
    VAULT_ADDR: "http://vault:8200"
  depends_on:
    vault:
      condition: service_started
```

### Alternative: AWS Secrets Manager

If using AWS, replace Vault with AWS Secrets Manager:

```bash
# Store secrets
aws secretsmanager create-secret \
  --name nexopus/api \
  --secret-string '{"SECRET_KEY":"...","GITHUB_AI_TOKEN":"..."}'

# Retrieve in application
import boto3

client = boto3.client('secretsmanager')
response = client.get_secret_value(SecretId='nexopus/api')
secrets = json.loads(response['SecretString'])
```

### Alternative: Azure Key Vault

If using Azure:

```bash
# Store secrets
az keyvault secret set \
  --vault-name nexopus-kv \
  --name SECRET_KEY \
  --value "your-secret-key"

# Retrieve in application
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

credential = DefaultAzureCredential()
client = SecretClient(vault_url="https://nexopus-kv.vault.azure.net", credential=credential)
secret = client.get_secret("SECRET_KEY")
```

### Environment Variables Migration

#### Before (Current - .env file):

```env
SECRET_KEY=your-secret-key-here
GITHUB_AI_TOKEN=your-github-token
POSTGRES_USER=nexopus
POSTGRES_PASSWORD=your-password
# ... more secrets
```

#### After (With Vault):

```env
# Only non-sensitive config
VAULT_ADDR=http://vault:8200
VAULT_ROLE=nexopus-api
API_URL=https://api.nexopus.com
```

### CI/CD Integration

Update `.github/workflows/ci.yml`:

```yaml
- name: Fetch secrets from Vault
  uses: hashicorp/vault-action@v2
  with:
    url: ${{ secrets.VAULT_ADDR }}
    method: github
    githubToken: ${{ secrets.GITHUB_TOKEN }}
    secrets: |
      secret/data/nexopus/api | SECRET_KEY ;
      secret/data/nexopus/api | GITHUB_AI_TOKEN ;
      secret/data/nexopus/database | POSTGRES_PASSWORD
```

### Security Best Practices

1. **Never commit secrets to git** - Use `.env.example` with placeholder values
2. **Rotate secrets regularly** - Configure automatic rotation in Vault
3. **Use least privilege** - Each service should only access required secrets
4. **Audit access** - Enable Vault audit logs
5. **Encrypt at rest** - Vault encrypts all secrets by default
6. **Use short TTLs** - Database credentials should auto-expire
7. **Backup Vault** - Regular backups of Vault storage

### Monitoring

Enable Vault monitoring:

```yaml
# Add to docker-compose.prod.yml
vault-exporter:
  image: prometheus-vault-exporter:latest
  environment:
    VAULT_ADDR: "http://vault:8200"
    VAULT_TOKEN: "${VAULT_TOKEN}"
  ports:
    - "9100:9100"
  networks:
    - nexopus-internal
```

### Rollback Plan

If Vault fails, services should fall back to environment variables:

```python
import os
import hvac

def get_secret(key: str, default: str = None) -> str:
    # Try Vault first
    try:
        client = hvac.Client(url=os.getenv('VAULT_ADDR'))
        secret = client.kv.v2.read_secret_version(path='nexopus/api')
        return secret['data']['data'][key]
    except:
        # Fallback to environment variable
        return os.getenv(key, default)
```

### Cost Considerations

- **Vault Open Source**: Free, self-hosted
- **Vault Enterprise**: Paid, additional features
- **AWS Secrets Manager**: $0.40 per secret/month + $0.05 per 10,000 API calls
- **Azure Key Vault**: Free for 5,000 operations/month, then $0.03/10,000 operations

### Next Steps

1. Install Vault server in your infrastructure
2. Initialize and unseal Vault
3. Enable required secrets engines
4. Store application secrets
5. Configure Vault agents for each service
6. Update CI/CD pipeline
7. Test secret rotation
8. Enable audit logging
9. Set up monitoring
10. Document recovery procedures

---

**Status**: 📝 Configuration guide created
**Implementation Required**: Yes - depends on infrastructure choice
**Priority**: High for production deployment
