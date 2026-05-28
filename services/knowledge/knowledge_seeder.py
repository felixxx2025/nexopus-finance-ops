"""
Knowledge Seeder — Popula a base de conhecimento com conteúdo contábil inicial.

Normas brasileiras, glossário, conceitos e exemplos práticos.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from packages.db.models import (
    AccountTemplate,
    GlossaryTerm,
    KnowledgeArticle,
    KnowledgeEmbedding,
    ReportTemplate,
    UseCase,
)
from services.knowledge.embedding_service import generate_embedding, generate_embeddings_batch

logger = logging.getLogger(__name__)

# Usar função síncrona para embeddings (Sentence Transformers)
import asyncio
from concurrent.futures import ThreadPoolExecutor

_executor = ThreadPoolExecutor(max_workers=1)


async def _generate_embedding_async(text: str) -> list[float]:
    """Wrapper assíncrono para generate_embedding."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, generate_embedding, text)


async def _generate_embeddings_batch_async(texts: list[str]) -> list[list[float]]:
    """Wrapper assíncrono para generate_embeddings_batch."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, generate_embeddings_batch, texts)


# ── Normas Brasileiras ────────────────────────────────────────────────────────────

_NORMAS_BRASILEIRAS = [
    {
        "title": "NBC TG 26 R5 — Apresentação das Demonstrações Contábeis",
        "category": "norma",
        "subcategory": "demonstracoes",
        "content": """
A NBC TG 26 (R5) estabelece os critérios para apresentação das demonstrações contábeis.
Principais pontos:
- Demonstrações obrigatórias: Balanço Patrimonial, DRE, DFC, DMPL e Notas Explicativas
- Comparabilidade: informações comparativas do período anterior
- Materialidade: itens materiais devem ser apresentados separadamente
- Continuidade: premissa de que a entidade continuará em operação
- Regime de competência: reconhecimento quando ocorre o fato gerador
""",
        "source": "CFC — Conselho Federal de Contabilidade",
        "source_url": "https://www.cfc.org.br/",
        "tags": ["NBC TG 26", "demonstrações contábeis", "balanço", "DRE", "CFC"],
    },
    {
        "title": "CPC 04 R1 — Ativo Intangível",
        "category": "norma",
        "subcategory": "ativos",
        "content": """
O CPC 04 (R1) trata do reconhecimento, mensuração e divulgação de ativos intangíveis.
Definição: Ativo não monetário sem substância física.
Critérios de reconhecimento:
- Identificabilidade: pode ser separado ou surge de direitos contratuais
- Controle: entidade pode obter benefícios econômicos
- Benefícios econômicos futuros: geração de receitas ou redução de custos
Exemplos: Software, patentes, marcas, direitos de exploração.
""",
        "source": "CPC — Comitê de Pronunciamentos Contábeis",
        "source_url": "https://www.cpc.org.br/",
        "tags": ["CPC 04", "ativo intangível", "software", "patentes", "marcas"],
    },
    {
        "title": "Lei 6.404/76 — Lei das Sociedades por Ações",
        "category": "norma",
        "subcategory": "legislacao",
        "content": """
A Lei 6.404/76 é a base da contabilidade societária brasileira.
Art. 176: Demonstrações financeiras obrigatórias ao fim de cada exercício:
I - Balanço Patrimonial
II - Demonstração dos Lucros ou Prejuízos Acumulados
III - Demonstração do Resultado do Exercício
IV - Demonstração das Origens e Aplicações de Recursos
V - Demonstração das Mutações do Patrimônio Líquido
""",
        "source": "Presidência da República",
        "source_url": "http://www.planalto.gov.br/",
        "tags": ["Lei 6.404", "sociedades por ações", "demonstrações", "legislação"],
    },
    {
        "title": "IN RFB 1700/17 — Tributação IRPJ/CSLL",
        "category": "norma",
        "subcategory": "tributacao",
        "content": """
A IN RFB 1700/17 estabelece normas para tributação do IRPJ e CSLL.
Alíquotas:
- IRPJ: 15% sobre lucro real + 10% sobre lucro excedente (lucro > R$ 20.000/mês)
- CSLL: 9% sobre lucro líquido ajustado
Base de cálculo: Lucro contábil ajustado pelas adições e exclusões previstas.
""",
        "source": "Receita Federal do Brasil",
        "source_url": "http://www.receita.fazenda.gov.br/",
        "tags": ["IN RFB 1700", "IRPJ", "CSLL", "tributação", "lucro real"],
    },
    {
        "title": "Resolução CFC 1.374/11 — Plano de Contas Referencial",
        "category": "norma",
        "subcategory": "plano_contas",
        "content": """
A Resolução CFC 1.374/11 institui o Plano de Contas Referencial.
Estrutura:
- 1.0 Ativo
- 2.0 Passivo
- 3.0 Patrimônio Líquido
- 4.0 Receitas
- 5.0 Despesas
Cada classe é subdividida em grupos e subgrupos para detalhamento.
""",
        "source": "CFC — Conselho Federal de Contabilidade",
        "source_url": "https://www.cfc.org.br/",
        "tags": ["CFC 1.374", "plano de contas", "referencial", "estrutura"],
    },
]


# ── Conceitos Contábeis ───────────────────────────────────────────────────────────

_CONCEITOS_CONTABEIS = [
    {
        "title": "Partida Dobrada",
        "category": "conceito",
        "subcategory": "fundamentos",
        "content": """
A partida dobrada é o princípio fundamental da contabilidade.
Para cada lançamento, o total de débitos deve igualar o total de créditos.
Equação: Ativo = Passivo + Patrimônio Líquido
Exemplo: Compra de mercadorias a vista:
- Débito: Estoque (Ativo)
- Crédito: Caixa (Ativo)
""",
        "source": "Fundamentos Contábeis",
        "tags": ["partida dobrada", "débito", "crédito", "equação patrimonial"],
    },
    {
        "title": "Equação Patrimonial",
        "category": "conceito",
        "subcategory": "fundamentos",
        "content": """
A equação patrimonial expressa a relação fundamental da contabilidade:
ATIVO = PASSIVO + PATRIMÔNIO LÍQUIDO
Onde:
- Ativo: Bens e direitos da empresa
- Passivo: Obrigações da empresa
- PL: Recursos dos proprietários
""",
        "source": "Fundamentos Contábeis",
        "tags": ["equação patrimonial", "ativo", "passivo", "patrimônio líquido"],
    },
    {
        "title": "DRE — Demonstração do Resultado do Exercício",
        "category": "conceito",
        "subcategory": "demonstracoes",
        "content": """
A DRE mostra o desempenho econômico da empresa em um período.
Estrutura básica:
(+) Receita Bruta
(-) Deduções (impostos, devoluções)
(=) Receita Líquida
(-) CPV (Custo dos Produtos Vendidos)
(=) Lucro Bruto
(-) Despesas Operacionais
(=) EBITDA
(-) Depreciação/Amortização
(=) EBIT (Lucro Operacional)
(+/-) Resultado Financeiro
(=) LAIR (Lucro Antes do IR)
(-) IR/CSLL
(=) Lucro Líquido
""",
        "source": "NBC TG 26",
        "tags": ["DRE", "demonstração resultado", "lucro", "EBITDA", "EBIT"],
    },
    {
        "title": "Balanço Patrimonial",
        "category": "conceito",
        "subcategory": "demonstracoes",
        "content": """
O Balanço Patrimonial mostra a posição financeira em uma data específica.
ATIVO (Aplicação de recursos):
- Ativo Circulante
- Ativo Não Circulante
PASSIVO + PL (Origem de recursos):
- Passivo Circulante
- Passivo Não Circulante
- Patrimônio Líquido
""",
        "source": "NBC TG 26",
        "tags": ["balanço patrimonial", "ativo", "passivo", "PL"],
    },
    {
        "title": "EBITDA — Earnings Before Interest, Taxes, Depreciation and Amortization",
        "category": "conceito",
        "subcategory": "indicadores",
        "content": """
EBITDA é um indicador de capacidade operacional de geração de caixa.
Cálculo:
Lucro Operacional + Depreciação + Amortização
Uso: Comparação entre empresas e setores, independente de estrutura de capital.
Limitação: Não considera capex (investimentos em ativos fixos).
""",
        "source": "Análise Financeira",
        "tags": ["EBITDA", "indicador", "lucro operacional", "depreciação"],
    },
]


# ── Glossário Contábil ─────────────────────────────────────────────────────────────

_GLOSSARIO_TERMS = [
    {
        "term": "Ativo Circulante",
        "definition": "Bens e direitos realizáveis até o término do exercício seguinte.",
        "category": "ativo",
        "related_terms": ["Ativo Não Circulante", "Caixa", "Estoques", "Contas a Receber"],
        "examples": [
            "Caixa em banco",
            "Duplicatas a receber",
            "Estoques de mercadorias",
            "Aplicações financeiras de curto prazo",
        ],
    },
    {
        "term": "Passivo Circulante",
        "definition": "Obrigações exigíveis até o término do exercício seguinte.",
        "category": "passivo",
        "related_terms": ["Passivo Não Circulante", "Fornecedores", "Empréstimos", "Salários"],
        "examples": [
            "Fornecedores a pagar",
            "Empréstimos bancários de curto prazo",
            "Salários e encargos a pagar",
            "Impostos a recolher",
        ],
    },
    {
        "term": "Patrimônio Líquido",
        "definition": "Recursos dos proprietários, calculado como Ativo - Passivo.",
        "category": "PL",
        "related_terms": ["Capital Social", "Reservas", "Lucros Acumulados", "Ações em Tesouraria"],
        "examples": [
            "Capital social integralizado",
            "Reservas de lucros",
            "Lucros acumulados",
            "Ajustes de avaliação patrimonial",
        ],
    },
    {
        "term": "CPV — Custo dos Produtos Vendidos",
        "definition": "Custo direto dos produtos vendidos no período.",
        "category": "custo",
        "related_terms": ["DRE", "Lucro Bruto", "Estoques", "Margem Bruta"],
        "examples": [
            "Matéria-prima consumida",
            "Mão de obra direta",
            "Depreciação de máquinas de produção",
            "Embalagens",
        ],
    },
    {
        "term": "Provisão",
        "definition": "Estimativa de perda provável, registrada antes da ocorrência certa.",
        "category": "ajuste",
        "related_terms": ["Contingência", "Passivo", "DRE", "Prudência"],
        "examples": [
            "Provisão para devedores duvidosos",
            "Provisão para férias",
            "Provisão para 13º salário",
            "Provisão para contingências judiciais",
        ],
    },
]


# ── Casos de Uso ─────────────────────────────────────────────────────────────────

_USE_CASES = [
    {
        "title": "Abertura de Empresa — Plano de Contas Inicial",
        "description": "Configurar plano de contas para nova empresa de serviços.",
        "scenario": "Empresa de consultoria iniciando operações, precisa de estrutura contábil básica.",
        "steps": {
            "1": "Definir setor de atuação (serviços)",
            "2": "Criar contas de ativo (caixa, bancos, clientes)",
            "3": "Criar contas de passivo (fornecedores, salários)",
            "4": "Criar contas de PL (capital social)",
            "5": "Criar contas de receita (serviços prestados)",
            "6": "Criar contas de despesa (aluguel, pessoal, impostos)",
        },
        "expected_outcome": "Plano de contas funcional para lançamentos diários.",
        "category": "abertura",
        "complexity": "basic",
    },
    {
        "title": "Fechamento Mensal — DRE e Balanço",
        "description": "Gerar DRE e Balanço ao final de cada mês.",
        "scenario": "Empresa precisa gerar relatórios mensais para gestão.",
        "steps": {
            "1": "Conciliar lançamentos do mês",
            "2": "Registrar provisões (férias, 13º)",
            "3": "Calcular depreciação mensal",
            "4": "Gerar DRE do período",
            "5": "Gerar Balanço Patrimonial",
            "6": "Revisar e aprovar relatórios",
        },
        "expected_outcome": "DRE e Balanço aprovados para o mês.",
        "category": "relatorio",
        "complexity": "medium",
    },
    {
        "title": "Auditoria Interna — Verificação de Partida Dobrada",
        "description": "Verificar se todos os lançamentos obedecem à partida dobrada.",
        "scenario": "Auditoria interna para garantir integridade contábil.",
        "steps": {
            "1": "Extrair todos os lançamentos do período",
            "2": "Somar débitos e créditos por lançamento",
            "3": "Identificar lançamentos com soma diferente",
            "4": "Investigar causas das divergências",
            "5": "Corrigir lançamentos errados",
            "6": "Documentar correções",
        },
        "expected_outcome": "100% dos lançamentos com partida dobrada válida.",
        "category": "auditoria",
        "complexity": "medium",
    },
]


async def seed_knowledge_base(db: AsyncSession) -> dict[str, int]:
    """
    Popula a base de conhecimento com conteúdo inicial.

    Args:
        db: Sessão do banco de dados.

    Returns:
        Dicionário com contagem de registros criados.
    """
    stats = {
        "normas": 0,
        "conceitos": 0,
        "glossario": 0,
        "use_cases": 0,
        "embeddings": 0,
    }

    try:
        # 0. Limpar tabelas existentes (para evitar duplicatas)
        from sqlalchemy import text
        logger.info("Limpando tabelas existentes...")
        await db.execute(text("TRUNCATE TABLE knowledge_embeddings CASCADE"))
        await db.execute(text("TRUNCATE TABLE use_cases CASCADE"))
        await db.execute(text("TRUNCATE TABLE glossary_terms CASCADE"))
        await db.execute(text("TRUNCATE TABLE knowledge_articles CASCADE"))
        await db.commit()

        # 1. Seed normas
        for norma in _NORMAS_BRASILEIRAS:
            article = KnowledgeArticle(
                title=norma["title"],
                content=norma["content"],
                category=norma["category"],
                subcategory=norma.get("subcategory"),
                tags=norma["tags"],
                source=norma["source"],
                source_url=norma.get("source_url"),
                language="pt-BR",
            )
            db.add(article)
            stats["normas"] += 1

        # 2. Seed conceitos
        for conceito in _CONCEITOS_CONTABEIS:
            article = KnowledgeArticle(
                title=conceito["title"],
                content=conceito["content"],
                category=conceito["category"],
                subcategory=conceito.get("subcategory"),
                tags=conceito["tags"],
                source=conceito["source"],
                language="pt-BR",
            )
            db.add(article)
            stats["conceitos"] += 1

        await db.commit()

        # 3. Seed glossário
        for term_data in _GLOSSARIO_TERMS:
            term = GlossaryTerm(
                term=term_data["term"],
                definition=term_data["definition"],
                category=term_data["category"],
                related_terms=term_data["related_terms"],
                examples=term_data["examples"],
                language="pt-BR",
            )
            db.add(term)
            stats["glossario"] += 1

        # 4. Seed use cases
        for uc_data in _USE_CASES:
            use_case = UseCase(
                title=uc_data["title"],
                description=uc_data["description"],
                scenario=uc_data["scenario"],
                steps=uc_data["steps"],
                expected_outcome=uc_data.get("expected_outcome"),
                category=uc_data["category"],
                complexity=uc_data["complexity"],
            )
            db.add(use_case)
            stats["use_cases"] += 1

        await db.commit()

        # 5. Gerar embeddings para artigos
        result = await db.execute(select(KnowledgeArticle))
        articles = result.scalars().all()

        texts = [f"{a.title}\n\n{a.content}" for a in articles]
        embeddings = await _generate_embeddings_batch_async(texts)

        for article, embedding in zip(articles, embeddings):
            emb_record = KnowledgeEmbedding(
                article_id=article.id,
                embedding=embedding,
                model="paraphrase-multilingual-MiniLM-L12-v2",
            )
            db.add(emb_record)
            stats["embeddings"] += 1

        await db.commit()

        logger.info("Base de conhecimento populada com sucesso: %s", stats)
        return stats

    except Exception as e:
        logger.error("Erro ao popular base de conhecimento: %s", e)
        await db.rollback()
        raise
