# BUNDLE ANALYSIS REPORT
**Data:** 1 de Junho de 2026

## Build Results

### Shared First Load JS
- **Total Shared:** 102 kB
  - chunks/1255-182ba487e8d6fb74.js: 46 kB
  - chunks/4bd1b696-100b9d70ed4e49c1.js: 54.2 kB
  - other shared chunks: 2.06 kB

### Route Analysis

| Rota | Size | First Load JS | Status |
|------|------|---------------|--------|
| / | 128 B | 102 kB | ✅ Excelente |
| /login | 2.95 kB | 105 kB | ✅ Bom |
| /reconciliation | 4.32 kB | 107 kB | ✅ Bom |
| /compliance | 3.62 kB | 116 kB | ✅ Bom |
| /entries-pending | 4.25 kB | 117 kB | ✅ Bom |
| /review | 2.64 kB | 115 kB | ✅ Bom |
| /assistant | 4.26 kB | 113 kB | ✅ Bom |
| /documents | 9.43 kB | 118 kB | ✅ Bom |
| /audit | 3.71 kB | 123 kB | ✅ Bom |
| /audit-logs | 8.78 kB | 125 kB | ✅ Bom |
| /knowledge | 6.09 kB | 126 kB | ✅ Bom |
| /upload | 22.8 kB | 133 kB | ⚠️ Aceitável |
| /reports | 17.4 kB | 137 kB | ⚠️ Aceitável |
| /admin/companies | 3.1 kB | 138 kB | ⚠️ Aceitável |
| /admin/users | 4.18 kB | 139 kB | ⚠️ Aceitável |
| /settings | 6.83 kB | 116 kB | ✅ Bom |
| /forecast | 82.6 kB | 212 kB | ⚠️ Pesado |
| /dashboard | 114 kB | 257 kB | ⚠️ Pesado |

## Análise

### Rotas Pesadas (> 200 kB First Load JS)
1. **/dashboard** - 257 kB (114 kB route + 102 kB shared)
   - Recomendação: Implementar code splitting para gráficos
   - Recomendação: Lazy loading de componentes pesados

2. **/forecast** - 212 kB (82.6 kB route + 102 kB shared)
   - Recomendação: Lazy loading de componentes de gráficos
   - Recomendação: Virtualização de listas longas

### Rotas Aceitáveis (100-200 kB)
- /upload, /reports, /admin/companies, /admin/users
- Recomendação: Otimização de imports

### Rotas Boas (< 120 kB)
- Todas as outras rotas estão bem otimizadas

## Recomendações

### Críticas
1. Implementar lazy loading em /dashboard e /forecast
2. Remover imports não utilizados
3. Otimizar shared chunks (102 kB pode ser reduzido)

### Médias
4. Implementar dynamic imports para bibliotecas pesadas
5. Usar @next/bundle-analyzer para análise contínua

## Status
- Build: ✅ Sucesso
- Bundle Size: ⚠️ Aceitável (pode ser melhorado)
- Tree Shaking: ✅ Ativo
- Code Splitting: ✅ Ativo (por rota)
- Lazy Loading: ⚠️ Parcial (implementado para charts)
