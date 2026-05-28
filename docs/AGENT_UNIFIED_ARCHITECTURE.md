# Agente Unificado - Arquitetura 100% Local

**Data:** 27 de Maio de 2026  
**Objetivo:** Documentar a arquitetura do agente unificado 100% local e independente

---

## 1. Visão Geral

O Agente Unificado combina 6 capacidades principais em uma única interface, **100% local e independente de APIs externas**:

1. **Generativo** - Chat com streaming via RAG + Templates (sem LLM externo)
2. **Executor** - Execução de ferramentas e ações no sistema
3. **Preditivo** - Modelos de previsão financeira (simulação local)
4. **Criativo** - Geração de relatórios, insights e narrativas (templates locais)
5. **Multi Documentos** - Processamento em lote de múltiplos arquivos
6. **Multimodal** - Processamento de imagens, PDFs, planilhas e áudio

**Vantagens da arquitetura 100% local:**
- Zero dependência de APIs externas (OpenAI, Copilot, etc)
- Privacidade total (dados nunca saem do servidor)
- Zero custo de operação
- Performance consistente sem rate limits
- Funciona offline (exceto web search Wikipedia)

---

## 2. Arquitetura Modular

```
services/ai_engine/
├── agent_assistant_local.py    # Generativo (chat RAG + Templates)
├── agent_executor.py           # Executor (ferramentas)
├── agent_predictive.py         # Preditivo (modelos de previsão)
├── agent_creative_local.py     # Criativo (geração local)
├── agent_multidoc.py           # Multi Documentos (processamento em lote)
├── agent_multimodal.py         # Multimodal (processamento de mídia)
└── agent_unified.py            # Unificador (interface única)
```

**Arquivos removidos (dependência do Copilot):**
- `agent_assistant.py` - Substituído por `agent_assistant_local.py`
- `agent_creative.py` - Substituído por `agent_creative_local.py`

---

## 3. Capacidade Executor

### 3.1 Arquivo: `agent_executor.py`

**Ferramentas disponíveis:**

- **create_journal_entry** - Cria lançamento contábil (partida dobrada)
  - Parâmetros: account_debit, account_credit, amount, description, entry_date
  - Retorna: entry_id, detalhes do lançamento

- **calculate_tax** - Calcula imposto sobre um valor
  - Parâmetros: amount, tax_rate, tax_type
  - Retorna: tax_amount, total

- **generate_report** - Gera relatório financeiro
  - Parâmetros: report_type, start_date, end_date
  - Retorna: relatório gerado

### 3.2 ToolRegistry

Sistema de registro de ferramentas dinâmico:

```python
ToolRegistry.register(name, description, func)
ToolRegistry.get_tool(name)
ToolRegistry.list_tools()
```

### 3.3 Uso

```python
agent = await create_unified_agent(db)
result = await agent.execute_tool("calculate_tax", amount=10000, tax_rate=0.15)
```

---

## 4. Capacidade Preditiva

### 4.1 Arquivo: `agent_predictive.py`

**Modelos disponíveis:**

- **predict_cash_flow** - Previsão de fluxo de caixa
  - Parâmetros: days_ahead
  - Método: média móvel
  - Retorna: previsões diárias com confiança

- **predict_revenue** - Previsão de receitas
  - Parâmetros: months_ahead
  - Método: sazonalidade + tendência
  - Retorna: previsões mensais

- **detect_anomalies** - Detecção de anomalias
  - Parâmetros: metric, threshold
  - Método: z-score
  - Retorna: anomalias detectadas

- **analyze_trends** - Análise de tendências
  - Parâmetros: metric, period_days
  - Método: regressão linear
  - Retorna: direção, força, slope

### 4.2 Uso

```python
agent = await create_unified_agent(db)
cash_flow = await agent.predict("cash_flow", days_ahead=30)
revenue = await agent.predict("revenue", months_ahead=6)
```

---

## 5. Capacidade Criativa

### 5.1 Arquivo: `agent_creative_local.py`

**Tipos de geração (100% local):**

- **generate_financial_report_local** - Relatório financeiro detalhado
  - Parâmetros: data, report_type
  - Usa: Templates locais
  - Retorna: relatório completo formatado

- **generate_insights_local** - Insights profundos
  - Parâmetros: data, focus_area
  - Usa: Lógica financeira local
  - Retorna: insights com observação, causa, impacto, recomendação

- **generate_narrative_local** - Narrativa de dados
  - Parâmetros: data, audience
  - Usa: Templates locais
  - Retorna: narrativa adaptada ao público

- **generate_recommendations_local** - Recomendações acionáveis
  - Parâmetros: data, priority
  - Usa: Lógica de negócios local
  - Retorna: recomendações com benefício, esforço, timeline

### 5.2 Uso

```python
agent = await create_unified_agent(db)
report = await agent.create("report", data=financial_data, report_type="executive_summary")
insights = await agent.create("insights", data=financial_data, focus_area="lucratividade")
```

---

## 6. Capacidade Multi Documentos

### 6.1 Arquivo: `agent_multidoc.py`

**Funcionalidades:**

- **process_multiple_documents** - Processamento em lote
  - Parâmetros: file_paths, extract_content, generate_embeddings
  - Suporta: PDF, TXT, MD, CSV, XLSX
  - Retorna: resultados do processamento

- **combine_documents** - Combina múltiplos documentos
  - Parâmetros: document_ids, strategy
  - Estratégias: concatenate, summarize, merge
  - Retorna: documento combinado

- **compare_documents** - Compara documentos
  - Parâmetros: document_ids
  - Retorna: similaridades, diferenças

### 6.2 Uso

```python
agent = await create_unified_agent(db)
result = await agent.process_documents(
    file_paths=["doc1.pdf", "doc2.xlsx"],
    extract_content=True,
    generate_embeddings=True,
)
```

---

## 7. Capacidade Multimodal

### 7.1 Arquivo: `agent_multimodal.py`

**Tipos de arquivo suportados:**

- **process_image** - Imagens (faturas, recibos)
  - Parâmetros: image_path, extract_text, extract_tables
  - TODO: Implementar OCR (Tesseract, PaddleOCR)
  - Retorna: texto extraído, tabelas

- **process_pdf_document** - PDFs complexos
  - Parâmetros: pdf_path, extract_text, extract_tables, extract_images
  - TODO: Implementar pdfplumber, Camelot
  - Retorna: texto, tabelas, imagens

- **process_spreadsheet** - Planilhas
  - Parâmetros: spreadsheet_path, extract_all_sheets
  - TODO: Implementar openpyxl, pandas
  - Retorna: abas, linhas

- **process_audio** - Áudio
  - Parâmetros: audio_path, transcribe, language
  - TODO: Implementar Whisper
  - Retorna: transcrição

### 7.2 Uso

```python
agent = await create_unified_agent(db)
image = await agent.process_multimodal("invoice.jpg", "image", extract_text=True)
pdf = await agent.process_multimodal("nfse.pdf", "pdf", extract_tables=True)
sheet = await agent.process_multimodal("dre.xlsx", "spreadsheet")
```

---

## 8. Agente Unificado

### 8.1 Arquivo: `agent_unified.py`

**Classe UnifiedAgent:**

```python
class UnifiedAgent:
    def __init__(self, db: AsyncSession)
    
    async def chat(question, context, history) -> AsyncGenerator[str]
    async def execute_tool(tool_name, **kwargs) -> dict
    async def predict(prediction_type, **kwargs) -> dict
    async def create(creation_type, **kwargs) -> dict
    async def process_documents(file_paths, **kwargs) -> dict
    async def process_multimodal(file_path, file_type, **kwargs) -> dict
    async def list_capabilities() -> dict
    async def autonomous_task(task, context) -> AsyncGenerator[str]
```

### 8.2 Capacidades

```python
capabilities = {
    "generative": True,
    "executor": True,
    "predictive": True,
    "creative": True,
    "multidoc": True,
    "multimodal": True,
}
```

### 8.3 Uso

```python
agent = await create_unified_agent(db)

# Chat
async for chunk in agent.chat("Qual a situação financeira?", context):
    print(chunk)

# Executor
result = await agent.execute_tool("calculate_tax", amount=10000, tax_rate=0.15)

# Preditivo
cash_flow = await agent.predict("cash_flow", days_ahead=30)

# Criativo
report = await agent.create("report", data=financial_data)

# Multi Documentos
docs = await agent.process_documents(["doc1.pdf", "doc2.xlsx"])

# Multimodal
image = await agent.process_multimodal("invoice.jpg", "image")
```

---

## 9. Integração com RAG

O agente unificado integra-se com o RAG existente:

- **Web Search:** Ativado automaticamente quando resultados locais insuficientes (Wikipedia API)
- **Embeddings Locais:** Sentence Transformers para busca semântica
- **Busca Lexical:** PostgreSQL tsvector para full-text search
- **Filtragem Inteligente:** Exclusão de resultados irrelevantes
- **Chat Generativo:** Usa RAG para buscar conhecimento relevante + templates para gerar respostas

---

## 10. Status de Implementação

### 10.1 Implementado ✅

- ✅ Executor: 3 ferramentas funcionando
- ✅ Preditivo: 4 modelos implementados (simulação local)
- ✅ Criativo: 4 tipos de geração (100% local com templates)
- ✅ Generativo: Chat com RAG + Templates (100% local)
- ✅ Multi Documentos: Processamento em lote implementado
- ✅ Multimodal: 4 tipos de arquivo (framework pronto)
- ✅ Unificação: Interface única funcionando
- ✅ Independência: Zero dependência de APIs externas

### 10.2 Pendente 🔧

- 🔧 OCR real (Tesseract/PaddleOCR) para imagens
- 🔧 Extração real de PDF (pdfplumber/Camelot)
- 🔧 Extração real de planilhas (openpyxl/pandas)
- 🔧 Transcrição real de áudio (Whisper)
- 🔧 Modelos preditivos reais (atualmente simulação)

### 10.3 Próximos Passos

- [ ] Implementar OCR com Tesseract
- [ ] Implementar extração de PDF com pdfplumber
- [ ] Implementar extração de planilhas com openpyxl
- [ ] Implementar transcrição com Whisper
- [ ] Treinar modelos preditivos com dados reais
- [ ] Implementar orquestração autônoma de tarefas
- [ ] Adicionar cache de resultados

---

## 11. Performance

### 11.1 Tempos Estimados

- **Executor:** ~10ms por operação
- **Preditivo:** ~50ms por previsão (simulação)
- **Criativo:** ~100ms por geração (templates locais)
- **Generativo:** ~200ms por resposta (RAG + templates)
- **Multi Documentos:** ~100ms por documento
- **Multimodal:** ~500ms-2s (depende do tipo)

### 11.2 Escalabilidade

- Processamento em lote para múltiplos documentos
- Async/await para operações I/O bound
- Cache de embeddings para reutilização
- Streaming para respostas longas

---

## 12. Segurança

### 12.1 Validação

- Validação de tipos de arquivo
- Validação de parâmetros
- Tratamento de erros robusto
- Logs de todas as operações

### 12.2 Permissões

- Acesso controlado ao banco de dados
- Validação de caminhos de arquivo
- Sanitização de inputs do usuário
- Rate limiting para APIs externas

---

## 13. Conclusão

O Agente Unificado fornece uma interface poderosa e flexível para operações financeiras avançadas, combinando capacidades generativas, executoras, preditivas, criativas, multi-documentos e multimodais em uma única arquitetura modular **100% local e independente**.

**Vantagens:**
- Interface unificada simples
- Capacidades modulares e extensíveis
- Integração com RAG existente
- Suporte a múltiplos tipos de mídia
- Processamento em lote eficiente
- **Zero dependência de APIs externas**
- **Privacidade total**
- **Zero custo de operação**

**Arquivos Principais:**
- `services/ai_engine/agent_unified.py` - Interface principal
- `services/ai_engine/agent_assistant_local.py` - Chat generativo (RAG + Templates)
- `services/ai_engine/agent_executor.py` - Ferramentas
- `services/ai_engine/agent_predictive.py` - Previsões
- `services/ai_engine/agent_creative_local.py` - Geração criativa local
- `services/ai_engine/agent_multidoc.py` - Multi documentos
- `services/ai_engine/agent_multimodal.py` - Multimodal

**Dependências:**
- sentence-transformers (embeddings locais)
- transformers (opcional, para modelos futuros)
- numpy (cálculos preditivos)
- pdfplumber (extração de PDF)
- openpyxl (extração de planilhas)
