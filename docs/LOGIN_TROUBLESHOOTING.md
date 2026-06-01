# Troubleshooting - Erro de Login "Failed to fetch"

## Diagnóstico

Se você está vendo "Failed to fetch" ao tentar fazer login, siga estes passos:

## 1. Verifique qual URL você está usando

**IMPORTANTE:** Você DEVE acessar via **localhost**, não via IP público.

### ✓ Correto (Funciona)
```
http://localhost:3000
```

### ✗ Incorreto (Não funciona sem SSL)
```
http://195.182.200.216:3000
```

## 2. Limpe Cookies e Cache do Navegador

### Chrome/Edge
1. Pressione `F12` para abrir DevTools
2. Vá para `Application` > `Storage` > `Clear site data`
3. Ou pressione `Ctrl+Shift+Delete` e limpe cookies para localhost

### Firefox
1. Pressione `F12` para abrir DevTools
2. Vá para `Storage` > `Cookies` > `http://localhost:3000`
3. Clique com botão direito > `Delete All`
4. Ou pressione `Ctrl+Shift+Delete` e limpe cookies para localhost

## 3. Verifique Console do Navegador

1. Pressione `F12` para abrir DevTools
2. Vá para a aba `Console`
3. Tente fazer login
4. Copie qualquer erro vermelho que aparecer

## 4. Verifique Network Tab

1. Pressione `F12` para abrir DevTools
2. Vá para a aba `Network`
3. Tente fazer login
4. Procure pela requisição `/auth/token`
5. Clique nela e verifique:
   - Status code (deve ser 200)
   - Response tab (deve ter o token)
   - Headers > Response Headers (deve ter `set-cookie`)

## 5. Verifique se a API está respondendo

No terminal, execute:
```bash
curl http://localhost:8000/health
```

Deve retornar: `{"status":"ok"}`

## 6. Teste login via curl

No terminal, execute:
```bash
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/json" \
  -H "Origin: http://localhost:3000" \
  -d '{"username": "admin", "password": "admin123"}'
```

Deve retornar um JSON com `access_token`.

## Soluções Comuns

### Problema: Acessando via IP público
**Solução:** Acesse http://localhost:3000 em vez de http://195.182.200.216:3000

### Problema: Cookies antigos
**Solução:** Limpe cookies do navegador para localhost

### Problema: API não está rodando
**Solução:** Execute `docker compose up -d` e verifique os logs

### Problema: Porta já em uso
**Solução:** Verifique se outra aplicação está usando as portas 3000 ou 8000

## Se Nada Funcionar

Por favor, forneça:
1. URL que você está acessando no navegador
2. Erro exato que aparece no console do navegador (F12 > Console)
3. Erro que aparece na aba Network (F12 > Network > /auth/token)
4. Saída do comando `docker ps`
5. Saída do comando `docker logs nexopusfinanceops-web-1 --tail 50`
