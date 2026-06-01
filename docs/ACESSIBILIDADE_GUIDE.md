# Guia de Acessibilidade - Nexopus Finance Ops

## Visão Geral

Este guia documenta as melhorias de acessibilidade implementadas e as práticas recomendadas para garantir que o Nexopus Finance Ops seja acessível a todos os usuários, incluindo aqueles com deficiências.

## Status Atual

### Implementado ✅

- **HTML Semântico**: Uso de tags HTML5 apropriadas (header, nav, main, footer)
- **Labels em Formulários**: Todos os inputs têm labels associados
- **ARIA Básico**: Atributos ARIA em componentes interativos
- **Navegação por Teclado**: Suporte básico para navegação
- **Contraste de Cores**: Cores com contraste WCAG AA
- **Botões com aria-label**: Ícones têm descrições acessíveis
- **Modais com role="dialog"**: Modais acessíveis
- **Tabelas com scope**: Headers de tabela apropriados

### Pendente ⚠️

- **ARIA Avançado**: Live regions, landmarks, estados dinâmicos
- **Screen Reader Testing**: Testes com NVDA, JAWS, VoiceOver
- **Skip Links**: Links para pular navegação
- **Focus Management**: Gestão avançada de foco
- **Keyboard Shortcuts**: Atalhos de teclado personalizados

## Melhorias Implementadas

### 1. Componentes de Botão

Todos os botões têm:
- `aria-label` para ícones sem texto
- `aria-expanded` para menus dropdown
- `aria-pressed` para botões toggle
- Estados de foco visíveis

```tsx
<Button
  aria-label="Fechar notificações"
  aria-expanded={isOpen}
  aria-haspopup="true"
>
  <Bell aria-hidden="true" />
</Button>
```

### 2. Formulários

Todos os formulários têm:
- Labels associadas via `htmlFor`
- Descrições de erro com `aria-describedby`
- Estados de validação com `aria-invalid`
- Feedback visual e auditivo

```tsx
<label htmlFor="username" className="text-sm">
  Nome de Usuário
</label>
<Input
  id="username"
  aria-describedby="username-error"
  aria-invalid={hasError}
/>
{hasError && (
  <p id="username-error" className="text-red-400" role="alert">
    {errorMessage}
  </p>
)}
```

### 3. Tabelas

Todas as tabelas têm:
- `caption` ou título descritivo
- `scope` em headers
- `aria-label` em tabelas sem caption
- Ordenação de colunas indicada

```tsx
<Table aria-label="Lista de usuários">
  <TableHeader>
    <TableRow>
      <TableHead scope="col">Usuário</TableHead>
      <TableHead scope="col">Email</TableHead>
    </TableRow>
  </TableHeader>
</Table>
```

### 4. Modais

Todos os modais têm:
- `role="dialog"`
- `aria-modal="true"`
- `aria-label` descritivo
- Trapping de foco
- Fechamento com ESC

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent
    role="dialog"
    aria-modal="true"
    aria-label="Criar novo usuário"
  >
    {/* Conteúdo */}
  </DialogContent>
</Dialog>
```

### 5. Notificações

Notificações têm:
- `role="alert"` para mensagens importantes
- `role="status"` para mensagens informativas
- `aria-live="polite"` para atualizações não críticas
- `aria-live="assertive"` para erros críticos

```tsx
<div role="alert" aria-live="assertive">
  <p className="text-red-400">Erro ao salvar</p>
</div>
```

## Práticas Recomendadas

### 1. Cores e Contraste

- **Contraste Mínimo**: 4.5:1 para texto normal (WCAG AA)
- **Contraste Grande**: 3:1 para texto grande (>18pt)
- **Independência de Cor**: Informações não devem depender apenas de cor
- **Modo Escuro**: Suporte para tema escuro com contraste adequado

### 2. Tamanho de Fonte

- **Mínimo**: 16px para texto de corpo
- **Escalável**: Suporte para zoom até 200%
- **Linear**: Layout que não quebra com zoom
- **Unidades Relativas**: Usar `rem` em vez de `px`

### 3. Foco Visível

- **Indicador de Foco**: Sempre visível e claro
- **Cor de Foco**: Contraste de pelo menos 3:1
- **Espessura**: Mínimo de 2px
- **Consistente**: Mesmo estilo em toda aplicação

```css
*:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}
```

### 4. Skip Links

Adicionar links para pular navegação:

```tsx
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4"
>
  Pular para conteúdo principal
</a>
<main id="main-content">
  {/* Conteúdo */}
</main>
```

### 5. Landmarks

Usar landmarks ARIA para navegação:

```tsx
<header role="banner">
  <nav aria-label="Navegação principal">
    {/* Menu */}
  </nav>
</header>
<main role="main">
  {/* Conteúdo principal */}
</main>
<aside aria-label="Informações adicionais">
  {/* Sidebar */}
</aside>
<footer role="contentinfo">
  {/* Rodapé */}
</footer>
```

### 6. Imagens

Todas as imagens devem ter:
- `alt` descritivo ou `alt=""` para decorativas
- Texto alternativo para gráficos complexos
- Descrições longas via `aria-describedby` se necessário

```tsx
<img
  src="/logo.png"
  alt="Logo da Nexopus Finance Ops"
/>
<img
  src="/decorative.png"
  alt=""
  role="presentation"
/>
```

## Testes de Acessibilidade

### Ferramentas Recomendadas

1. **Lighthouse**: Auditoria automatizada no Chrome DevTools
2. **axe DevTools**: Extensão do Chrome para testes manuais
3. **WAVE**: Ferramenta online para avaliação visual
4. **NVDA**: Screen reader gratuito para Windows
5. **VoiceOver**: Screen reader nativo do macOS
6. **JAWS**: Screen reader comercial para Windows

### Checklist de Testes

- [ ] Navegação completa por teclado (Tab, Shift+Tab, Enter, Esc)
- [ ] Foco visível em todos os elementos interativos
- [ ] Leitura com screen reader (NVDA, VoiceOver)
- [ ] Contraste de cores (Lighthouse)
- [ ] Labels em todos os inputs
- [ ] Alt text em todas as imagens
- [ ] ARIA labels em ícones sem texto
- [ ] Modais com trapping de foco
- [ ] Notificações com aria-live
- [ ] Tabelas com headers apropriados

## Recursos

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Inclusive Components](https://inclusive-components.design/)

---

**Status**: 📝 Guia criado
**Implementação Parcial**: Básico implementado, avançado pendente
**Prioridade**: Baixa - melhorias contínuas
