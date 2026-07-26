"""
Template Service — Gerenciamento de templates de relatórios e planos de contas.

Templates estruturados para DRE, Balanço e planos de contas por setor.
"""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from packages.db.models import AccountTemplate, ReportTemplate

logger = logging.getLogger(__name__)


# ── Templates de Relatórios ─────────────────────────────────────────────────────

_DRE_TEMPLATE_SERVICOS = {
    "name": "DRE Padrão — Serviços",
    "type": "dre",
    "sector": "servicos",
    "structure": {
        "receita_bruta": {
            "label": "Receita Bruta",
            "level": 1,
            "type": "debit",
        },
        "deducoes": {
            "label": "(-) Deduções (ISS, PIS, COFINS)",
            "level": 2,
            "type": "credit",
        },
        "receita_liquida": {
            "label": "(=) Receita Líquida",
            "level": 1,
            "type": "debit",
            "formula": "receita_bruta - deducoes",
        },
        "custo_servicos": {
            "label": "(-) Custo dos Serviços Prestados",
            "level": 2,
            "type": "credit",
        },
        "lucro_bruto": {
            "label": "(=) Lucro Bruto",
            "level": 1,
            "type": "debit",
            "formula": "receita_liquida - custo_servicos",
        },
        "despesas_operacionais": {
            "label": "(-) Despesas Operacionais",
            "level": 1,
            "type": "credit",
            "children": {
                "despesas_pessoal": {
                    "label": "Despesas com Pessoal",
                    "level": 2,
                },
                "despesas_aluguel": {
                    "label": "Aluguel",
                    "level": 2,
                },
                "despesas_marketing": {
                    "label": "Marketing e Vendas",
                    "level": 2,
                },
                "despesas_administrativas": {
                    "label": "Despesas Administrativas",
                    "level": 2,
                },
            },
        },
        "ebitda": {
            "label": "(=) EBITDA",
            "level": 1,
            "type": "debit",
            "formula": "lucro_bruto - despesas_operacionais",
        },
        "depreciacao": {
            "label": "(-) Depreciação e Amortização",
            "level": 2,
            "type": "credit",
        },
        "ebit": {
            "label": "(=) EBIT (Lucro Operacional)",
            "level": 1,
            "type": "debit",
            "formula": "ebitda - depreciacao",
        },
        "resultado_financeiro": {
            "label": "(+/-) Resultado Financeiro",
            "level": 2,
            "type": "debit",
        },
        "lair": {
            "label": "(=) LAIR (Lucro Antes do IR)",
            "level": 1,
            "type": "debit",
            "formula": "ebit + resultado_financeiro",
        },
        "ir_csll": {
            "label": "(-) IRPJ + CSLL (34%)",
            "level": 2,
            "type": "credit",
            "formula": "lair * 0.34",
        },
        "lucro_liquido": {
            "label": "(=) Lucro Líquido",
            "level": 1,
            "type": "debit",
            "formula": "lair - ir_csll",
        },
    },
    "formulas": {
        "margem_bruta": "lucro_bruto / receita_liquida",
        "margem_ebitda": "ebitda / receita_liquida",
        "margem_liquida": "lucro_liquido / receita_liquida",
    },
    "metadata": {
        "norma": "NBC TG 26",
        "versao": "1.0",
    },
}


_DRE_TEMPLATE_COMERCIO = {
    "name": "DRE Padrão — Comércio",
    "type": "dre",
    "sector": "comercio",
    "structure": {
        "receita_bruta": {
            "label": "Receita Bruta",
            "level": 1,
            "type": "debit",
        },
        "deducoes": {
            "label": "(-) Deduções (ICMS, PIS, COFINS, Devoluções)",
            "level": 2,
            "type": "credit",
        },
        "receita_liquida": {
            "label": "(=) Receita Líquida",
            "level": 1,
            "type": "debit",
            "formula": "receita_bruta - deducoes",
        },
        "cmv": {
            "label": "(-) CMV — Custo da Mercadoria Vendida",
            "level": 2,
            "type": "credit",
        },
        "lucro_bruto": {
            "label": "(=) Lucro Bruto",
            "level": 1,
            "type": "debit",
            "formula": "receita_liquida - cmv",
        },
        "despesas_operacionais": {
            "label": "(-) Despesas Operacionais",
            "level": 1,
            "type": "credit",
            "children": {
                "despesas_pessoal": {
                    "label": "Despesas com Pessoal",
                    "level": 2,
                },
                "despesas_aluguel": {
                    "label": "Aluguel",
                    "level": 2,
                },
                "despesas_marketing": {
                    "label": "Marketing e Vendas",
                    "level": 2,
                },
                "despesas_administrativas": {
                    "label": "Despesas Administrativas",
                    "level": 2,
                },
            },
        },
        "ebitda": {
            "label": "(=) EBITDA",
            "level": 1,
            "type": "debit",
            "formula": "lucro_bruto - despesas_operacionais",
        },
        "depreciacao": {
            "label": "(-) Depreciação e Amortização",
            "level": 2,
            "type": "credit",
        },
        "ebit": {
            "label": "(=) EBIT (Lucro Operacional)",
            "level": 1,
            "type": "debit",
            "formula": "ebitda - depreciacao",
        },
        "resultado_financeiro": {
            "label": "(+/-) Resultado Financeiro",
            "level": 2,
            "type": "debit",
        },
        "lair": {
            "label": "(=) LAIR (Lucro Antes do IR)",
            "level": 1,
            "type": "debit",
            "formula": "ebit + resultado_financeiro",
        },
        "ir_csll": {
            "label": "(-) IRPJ + CSLL (34%)",
            "level": 2,
            "type": "credit",
            "formula": "lair * 0.34",
        },
        "lucro_liquido": {
            "label": "(=) Lucro Líquido",
            "level": 1,
            "type": "debit",
            "formula": "lair - ir_csll",
        },
    },
    "formulas": {
        "margem_bruta": "lucro_bruto / receita_liquida",
        "margem_ebitda": "ebitda / receita_liquida",
        "margem_liquida": "lucro_liquido / receita_liquida",
        "giro_estoque": "cmv / estoque_medio",
    },
    "metadata": {
        "norma": "NBC TG 26",
        "versao": "1.0",
    },
}


_DRE_TEMPLATE_INDUSTRIA = {
    "name": "DRE Padrão — Indústria",
    "type": "dre",
    "sector": "industria",
    "structure": {
        "receita_bruta": {
            "label": "Receita Bruta",
            "level": 1,
            "type": "debit",
        },
        "deducoes": {
            "label": "(-) Deduções (IPI, ICMS, PIS, COFINS)",
            "level": 2,
            "type": "credit",
        },
        "receita_liquida": {
            "label": "(=) Receita Líquida",
            "level": 1,
            "type": "debit",
            "formula": "receita_bruta - deducoes",
        },
        "cpv": {
            "label": "(-) CPV — Custo dos Produtos Vendidos",
            "level": 2,
            "type": "credit",
            "children": {
                "materia_prima": {
                    "label": "Matéria-Prima Consumida",
                    "level": 3,
                },
                "mao_obra_direta": {
                    "label": "Mão de Obra Direta",
                    "level": 3,
                },
                "cif": {
                    "label": "CIF — Custos Indiretos de Fabricação",
                    "level": 3,
                },
            },
        },
        "lucro_bruto": {
            "label": "(=) Lucro Bruto",
            "level": 1,
            "type": "debit",
            "formula": "receita_liquida - cpv",
        },
        "despesas_operacionais": {
            "label": "(-) Despesas Operacionais",
            "level": 1,
            "type": "credit",
            "children": {
                "despesas_pessoal": {
                    "label": "Despesas com Pessoal",
                    "level": 2,
                },
                "despesas_aluguel": {
                    "label": "Aluguel",
                    "level": 2,
                },
                "despesas_energia": {
                    "label": "Energia Elétrica",
                    "level": 2,
                },
                "despesas_manutencao": {
                    "label": "Manutenção Industrial",
                    "level": 2,
                },
                "despesas_administrativas": {
                    "label": "Despesas Administrativas",
                    "level": 2,
                },
            },
        },
        "ebitda": {
            "label": "(=) EBITDA",
            "level": 1,
            "type": "debit",
            "formula": "lucro_bruto - despesas_operacionais",
        },
        "depreciacao": {
            "label": "(-) Depreciação e Amortização",
            "level": 2,
            "type": "credit",
        },
        "ebit": {
            "label": "(=) EBIT (Lucro Operacional)",
            "level": 1,
            "type": "debit",
            "formula": "ebitda - depreciacao",
        },
        "resultado_financeiro": {
            "label": "(+/-) Resultado Financeiro",
            "level": 2,
            "type": "debit",
        },
        "lair": {
            "label": "(=) LAIR (Lucro Antes do IR)",
            "level": 1,
            "type": "debit",
            "formula": "ebit + resultado_financeiro",
        },
        "ir_csll": {
            "label": "(-) IRPJ + CSLL (34%)",
            "level": 2,
            "type": "credit",
            "formula": "lair * 0.34",
        },
        "lucro_liquido": {
            "label": "(=) Lucro Líquido",
            "level": 1,
            "type": "debit",
            "formula": "lair - ir_csll",
        },
    },
    "formulas": {
        "margem_bruta": "lucro_bruto / receita_liquida",
        "margem_ebitda": "ebitda / receita_liquida",
        "margem_liquida": "lucro_liquido / receita_liquida",
        "giro_estoque": "cpv / estoque_medio",
    },
    "metadata": {
        "norma": "NBC TG 26",
        "versao": "1.0",
    },
}


_FLUXO_CAIXA_TEMPLATE = {
    "name": "Fluxo de Caixa Padrão",
    "type": "fluxo_caixa",
    "sector": None,
    "structure": {
        "atividades_operacionais": {
            "label": "ATIVIDADES OPERACIONAIS",
            "level": 1,
            "children": {
                "lucro_liquido": {
                    "label": "Lucro Líquido",
                    "level": 2,
                },
                "ajustes": {
                    "label": "(+) Ajustes",
                    "level": 2,
                    "children": {
                        "depreciacao": {"label": "Depreciação e Amortização", "level": 3},
                        "provisoes": {"label": "Provisões", "level": 3},
                    },
                },
                "variacoes_ativo": {
                    "label": "(-) Variações no Ativo",
                    "level": 2,
                    "children": {
                        "contas_receber": {"label": "Contas a Receber", "level": 3},
                        "estoques": {"label": "Estoques", "level": 3},
                    },
                },
                "variacoes_passivo": {
                    "label": "(+) Variações no Passivo",
                    "level": 2,
                    "children": {
                        "fornecedores": {"label": "Fornecedores", "level": 3},
                        "salarios": {"label": "Salários a Pagar", "level": 3},
                    },
                },
                "fluxo_operacional": {
                    "label": "(=) Fluxo de Caixa Operacional",
                    "level": 1,
                    "formula": "lucro_liquido + ajustes - variacoes_ativo + variacoes_passivo",
                },
            },
        },
        "atividades_investimento": {
            "label": "ATIVIDADES DE INVESTIMENTO",
            "level": 1,
            "children": {
                "compra_imobilizado": {
                    "label": "(-) Compra de Imobilizado",
                    "level": 2,
                },
                "venda_imobilizado": {
                    "label": "(+) Venda de Imobilizado",
                    "level": 2,
                },
                "fluxo_investimento": {
                    "label": "(=) Fluxo de Caixa de Investimento",
                    "level": 1,
                    "formula": "venda_imobilizado - compra_imobilizado",
                },
            },
        },
        "atividades_financiamento": {
            "label": "ATIVIDADES DE FINANCIAMENTO",
            "level": 1,
            "children": {
                "novo_emprestimo": {
                    "label": "(+) Novo Empréstimo",
                    "level": 2,
                },
                "pagamento_emprestimo": {
                    "label": "(-) Pagamento de Empréstimo",
                    "level": 2,
                },
                "capital_social": {
                    "label": "(+) Integralização de Capital",
                    "level": 2,
                },
                "dividendos": {
                    "label": "(-) Pagamento de Dividendos",
                    "level": 2,
                },
                "fluxo_financiamento": {
                    "label": "(=) Fluxo de Caixa de Financiamento",
                    "level": 1,
                    "formula": "novo_emprestimo + capital_social - pagamento_emprestimo - dividendos",
                },
            },
        },
        "variacao_caixa": {
            "label": "(=) Variação do Caixa",
            "level": 1,
            "formula": "fluxo_operacional + fluxo_investimento + fluxo_financiamento",
        },
        "caixa_inicial": {
            "label": "(+) Caixa Inicial",
            "level": 2,
        },
        "caixa_final": {
            "label": "(=) Caixa Final",
            "level": 1,
            "formula": "variacao_caixa + caixa_inicial",
        },
    },
    "formulas": {
        "fcf": "fluxo_operacional - compra_imobilizado",
        "liquidez_imediata": "caixa_final / passivo_circulante",
    },
    "metadata": {
        "norma": "CPC 03",
        "versao": "1.0",
    },
}


_BALANCO_TEMPLATE_PADRAO = {
    "name": "Balanço Patrimonial Padrão",
    "type": "balanco",
    "sector": None,
    "structure": {
        "ativo": {
            "label": "ATIVO",
            "level": 1,
            "children": {
                "ativo_circulante": {
                    "label": "Ativo Circulante",
                    "level": 2,
                    "children": {
                        "caixa": {"label": "Caixa e Equivalentes", "level": 3},
                        "contas_receber": {"label": "Contas a Receber", "level": 3},
                        "estoques": {"label": "Estoques", "level": 3},
                        "despesas_antecipadas": {"label": "Despesas Antecipadas", "level": 3},
                    },
                },
                "ativo_nao_circulante": {
                    "label": "Ativo Não Circulante",
                    "level": 2,
                    "children": {
                        "realizavel_longo_prazo": {
                            "label": "Realizável a Longo Prazo",
                            "level": 3,
                        },
                        "imobilizado": {"label": "Imobilizado", "level": 3},
                        "intangivel": {"label": "Intangível", "level": 3},
                    },
                },
            },
        },
        "passivo_pl": {
            "label": "PASSIVO + PATRIMÔNIO LÍQUIDO",
            "level": 1,
            "children": {
                "passivo_circulante": {
                    "label": "Passivo Circulante",
                    "level": 2,
                    "children": {
                        "fornecedores": {"label": "Fornecedores", "level": 3},
                        "emprestimos_curto": {"label": "Empréstimos CP", "level": 3},
                        "salarios": {"label": "Salários a Pagar", "level": 3},
                        "impostos": {"label": "Impostos a Recolher", "level": 3},
                    },
                },
                "passivo_nao_circulante": {
                    "label": "Passivo Não Circulante",
                    "level": 2,
                    "children": {
                        "emprestamentos_longo": {"label": "Empréstimos LP", "level": 3},
                        "provisoes": {"label": "Provisões", "level": 3},
                    },
                },
                "patrimonio_liquido": {
                    "label": "Patrimônio Líquido",
                    "level": 2,
                    "children": {
                        "capital_social": {"label": "Capital Social", "level": 3},
                        "reservas": {"label": "Reservas de Capital", "level": 3},
                        "lucros_acumulados": {"label": "Lucros Acumulados", "level": 3},
                    },
                },
            },
        },
    },
    "formulas": {
        "ativo_total": "ativo_circulante + ativo_nao_circulante",
        "passivo_total": "passivo_circulante + passivo_nao_circulante",
        "pl_total": "patrimonio_liquido",
        "liquidez_corrente": "ativo_circulante / passivo_circulante",
    },
    "metadata": {
        "norma": "Lei 6.404/76",
        "versao": "1.0",
    },
}


# ── Planos de Contas por Setor ──────────────────────────────────────────────────

_PLANO_CONTAS_SERVICOS = {
    "name": "Plano de Contas — Serviços",
    "sector": "servicos",
    "accounts": [
        # Ativo
        {"code": "1.1.01", "name": "Caixa", "type": "ativo", "parent": None},
        {"code": "1.1.02", "name": "Bancos Conta Movimento", "type": "ativo", "parent": None},
        {"code": "1.1.03", "name": "Aplicações Financeiras", "type": "ativo", "parent": None},
        {"code": "1.1.04", "name": "Contas a Receber", "type": "ativo", "parent": None},
        {"code": "1.1.05", "name": "Estoques", "type": "ativo", "parent": None},
        {"code": "1.2.01", "name": "Imobilizado", "type": "ativo", "parent": None},
        {"code": "1.2.02", "name": "Intangível", "type": "ativo", "parent": None},
        # Passivo
        {"code": "2.1.01", "name": "Fornecedores", "type": "passivo", "parent": None},
        {"code": "2.1.02", "name": "Salários a Pagar", "type": "passivo", "parent": None},
        {"code": "2.1.03", "name": "Impostos a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.04", "name": "Empréstimos CP", "type": "passivo", "parent": None},
        {"code": "2.2.01", "name": "Empréstimos LP", "type": "passivo", "parent": None},
        # PL
        {"code": "3.1.01", "name": "Capital Social", "type": "pl", "parent": None},
        {"code": "3.2.01", "name": "Reservas de Lucros", "type": "pl", "parent": None},
        {"code": "3.3.01", "name": "Lucros Acumulados", "type": "pl", "parent": None},
        # Receita
        {"code": "4.1.01", "name": "Receita de Serviços", "type": "receita", "parent": None},
        {"code": "4.1.02", "name": "Receita Financeira", "type": "receita", "parent": None},
        # Despesa
        {"code": "5.1.01", "name": "Custo dos Serviços", "type": "despesa", "parent": None},
        {"code": "5.2.01", "name": "Salários e Encargos", "type": "despesa", "parent": None},
        {"code": "5.2.02", "name": "Aluguel", "type": "despesa", "parent": None},
        {"code": "5.2.03", "name": "Marketing", "type": "despesa", "parent": None},
        {"code": "5.2.04", "name": "Despesas Administrativas", "type": "despesa", "parent": None},
        {"code": "5.2.05", "name": "Depreciação", "type": "despesa", "parent": None},
        {"code": "5.3.01", "name": "Despesa Financeira", "type": "despesa", "parent": None},
        {"code": "5.4.01", "name": "IRPJ e CSLL", "type": "despesa", "parent": None},
    ],
    "metadata": {
        "norma": "CFC 1.374/11",
        "versao": "1.0",
    },
}


_PLANO_CONTAS_COMERCIO = {
    "name": "Plano de Contas — Comércio",
    "sector": "comercio",
    "accounts": [
        # Ativo
        {"code": "1.1.01", "name": "Caixa", "type": "ativo", "parent": None},
        {"code": "1.1.02", "name": "Bancos", "type": "ativo", "parent": None},
        {"code": "1.1.03", "name": "Contas a Receber", "type": "ativo", "parent": None},
        {"code": "1.1.04", "name": "Estoques de Mercadorias", "type": "ativo", "parent": None},
        {"code": "1.1.05", "name": "ICMS a Recuperar", "type": "ativo", "parent": None},
        {"code": "1.2.01", "name": "Imobilizado", "type": "ativo", "parent": None},
        # Passivo
        {"code": "2.1.01", "name": "Fornecedores", "type": "passivo", "parent": None},
        {"code": "2.1.02", "name": "ICMS a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.03", "name": "Salários a Pagar", "type": "passivo", "parent": None},
        {"code": "2.1.04", "name": "Empréstimos CP", "type": "passivo", "parent": None},
        # PL
        {"code": "3.1.01", "name": "Capital Social", "type": "pl", "parent": None},
        {"code": "3.3.01", "name": "Lucros Acumulados", "type": "pl", "parent": None},
        # Receita
        {"code": "4.1.01", "name": "Venda de Mercadorias", "type": "receita", "parent": None},
        {"code": "4.1.02", "name": "Receita Financeira", "type": "receita", "parent": None},
        # Despesa
        {"code": "5.1.01", "name": "CMV — Custo da Mercadoria Vendida", "type": "despesa", "parent": None},
        {"code": "5.2.01", "name": "Salários e Encargos", "type": "despesa", "parent": None},
        {"code": "5.2.02", "name": "Aluguel", "type": "despesa", "parent": None},
        {"code": "5.2.03", "name": "Marketing", "type": "despesa", "parent": None},
        {"code": "5.2.04", "name": "Despesas Administrativas", "type": "despesa", "parent": None},
        {"code": "5.4.01", "name": "IRPJ e CSLL", "type": "despesa", "parent": None},
    ],
    "metadata": {
        "norma": "CFC 1.374/11",
        "versao": "1.0",
    },
}


_PLANO_CONTAS_INDUSTRIA = {
    "name": "Plano de Contas — Indústria",
    "sector": "industria",
    "accounts": [
        # Ativo
        {"code": "1.1.01", "name": "Caixa", "type": "ativo", "parent": None},
        {"code": "1.1.02", "name": "Bancos", "type": "ativo", "parent": None},
        {"code": "1.1.03", "name": "Contas a Receber", "type": "ativo", "parent": None},
        {"code": "1.1.04", "name": "Estoques de Matéria-Prima", "type": "ativo", "parent": None},
        {"code": "1.1.05", "name": "Estoques de Produtos Acabados", "type": "ativo", "parent": None},
        {"code": "1.1.06", "name": "IPI a Recuperar", "type": "ativo", "parent": None},
        {"code": "1.1.07", "name": "ICMS a Recuperar", "type": "ativo", "parent": None},
        {"code": "1.2.01", "name": "Imobilizado", "type": "ativo", "parent": None},
        {"code": "1.2.02", "name": "Imobilizado em Andamento", "type": "ativo", "parent": None},
        # Passivo
        {"code": "2.1.01", "name": "Fornecedores", "type": "passivo", "parent": None},
        {"code": "2.1.02", "name": "IPI a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.03", "name": "ICMS a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.04", "name": "Salários a Pagar", "type": "passivo", "parent": None},
        {"code": "2.1.05", "name": "Empréstimos CP", "type": "passivo", "parent": None},
        {"code": "2.2.01", "name": "Empréstimos LP", "type": "passivo", "parent": None},
        # PL
        {"code": "3.1.01", "name": "Capital Social", "type": "pl", "parent": None},
        {"code": "3.2.01", "name": "Reservas de Capital", "type": "pl", "parent": None},
        {"code": "3.3.01", "name": "Lucros Acumulados", "type": "pl", "parent": None},
        # Receita
        {"code": "4.1.01", "name": "Venda de Produtos", "type": "receita", "parent": None},
        {"code": "4.1.02", "name": "Receita Financeira", "type": "receita", "parent": None},
        # Despesa
        {"code": "5.1.01", "name": "Custo dos Produtos Vendidos", "type": "despesa", "parent": None},
        {"code": "5.1.02", "name": "Matéria-Prima Consumida", "type": "despesa", "parent": None},
        {"code": "5.1.03", "name": "Mão de Obra Direta", "type": "despesa", "parent": None},
        {"code": "5.1.04", "name": "CIF — Custos Indiretos de Fabricação", "type": "despesa", "parent": None},
        {"code": "5.2.01", "name": "Salários e Encargos", "type": "despesa", "parent": None},
        {"code": "5.2.02", "name": "Aluguel", "type": "despesa", "parent": None},
        {"code": "5.2.03", "name": "Energia Elétrica", "type": "despesa", "parent": None},
        {"code": "5.2.04", "name": "Manutenção Industrial", "type": "despesa", "parent": None},
        {"code": "5.2.05", "name": "Despesas Administrativas", "type": "despesa", "parent": None},
        {"code": "5.3.01", "name": "Despesa Financeira", "type": "despesa", "parent": None},
        {"code": "5.4.01", "name": "IRPJ e CSLL", "type": "despesa", "parent": None},
    ],
    "metadata": {
        "norma": "CFC 1.374/11",
        "versao": "1.0",
    },
}


_PLANO_CONTAS_TECNOLOGIA = {
    "name": "Plano de Contas — Tecnologia",
    "sector": "tecnologia",
    "accounts": [
        # Ativo
        {"code": "1.1.01", "name": "Caixa", "type": "ativo", "parent": None},
        {"code": "1.1.02", "name": "Bancos", "type": "ativo", "parent": None},
        {"code": "1.1.03", "name": "Contas a Receber", "type": "ativo", "parent": None},
        {"code": "1.1.04", "name": "Aplicações Financeiras", "type": "ativo", "parent": None},
        {"code": "1.2.01", "name": "Imobilizado", "type": "ativo", "parent": None},
        {"code": "1.2.02", "name": "Intangível — Software", "type": "ativo", "parent": None},
        {"code": "1.2.03", "name": "Intangível — Patentes", "type": "ativo", "parent": None},
        # Passivo
        {"code": "2.1.01", "name": "Fornecedores", "type": "passivo", "parent": None},
        {"code": "2.1.02", "name": "Salários a Pagar", "type": "passivo", "parent": None},
        {"code": "2.1.03", "name": "Impostos a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.04", "name": "Empréstimos CP", "type": "passivo", "parent": None},
        {"code": "2.2.01", "name": "Empréstimos LP", "type": "passivo", "parent": None},
        # PL
        {"code": "3.1.01", "name": "Capital Social", "type": "pl", "parent": None},
        {"code": "3.2.01", "name": "Reservas de Capital", "type": "pl", "parent": None},
        {"code": "3.3.01", "name": "Lucros Acumulados", "type": "pl", "parent": None},
        {"code": "3.3.02", "name": "Ajustes de Avaliação Patrimonial", "type": "pl", "parent": None},
        # Receita
        {"code": "4.1.01", "name": "Receita de Software/SaaS", "type": "receita", "parent": None},
        {"code": "4.1.02", "name": "Receita de Serviços de TI", "type": "receita", "parent": None},
        {"code": "4.1.03", "name": "Receita Financeira", "type": "receita", "parent": None},
        # Despesa
        {"code": "5.1.01", "name": "Custo de Serviços", "type": "despesa", "parent": None},
        {"code": "5.1.02", "name": "Custo de Infraestrutura Cloud", "type": "despesa", "parent": None},
        {"code": "5.2.01", "name": "Salários e Encargos — TI", "type": "despesa", "parent": None},
        {"code": "5.2.02", "name": "Salários e Encargos — Comercial", "type": "despesa", "parent": None},
        {"code": "5.2.03", "name": "Aluguel", "type": "despesa", "parent": None},
        {"code": "5.2.04", "name": "Marketing Digital", "type": "despesa", "parent": None},
        {"code": "5.2.05", "name": "Despesas Administrativas", "type": "despesa", "parent": None},
        {"code": "5.2.06", "name": "Licenças de Software", "type": "despesa", "parent": None},
        {"code": "5.3.01", "name": "Despesa Financeira", "type": "despesa", "parent": None},
        {"code": "5.4.01", "name": "IRPJ e CSLL", "type": "despesa", "parent": None},
    ],
    "metadata": {
        "norma": "CFC 1.374/11",
        "versao": "1.0",
    },
}


_PLANO_CONTAS_SAUDE = {
    "name": "Plano de Contas — Saúde",
    "sector": "saude",
    "accounts": [
        # Ativo
        {"code": "1.1.01", "name": "Caixa", "type": "ativo", "parent": None},
        {"code": "1.1.02", "name": "Bancos", "type": "ativo", "parent": None},
        {"code": "1.1.03", "name": "Contas a Receber — Convênios", "type": "ativo", "parent": None},
        {"code": "1.1.04", "name": "Contas a Receber — Particular", "type": "ativo", "parent": None},
        {"code": "1.1.05", "name": "Estoques — Medicamentos", "type": "ativo", "parent": None},
        {"code": "1.1.06", "name": "Estoques — Materiais Médicos", "type": "ativo", "parent": None},
        {"code": "1.2.01", "name": "Imobilizado — Equipamentos", "type": "ativo", "parent": None},
        {"code": "1.2.02", "name": "Imobilizado — Instalações", "type": "ativo", "parent": None},
        # Passivo
        {"code": "2.1.01", "name": "Fornecedores — Medicamentos", "type": "passivo", "parent": None},
        {"code": "2.1.02", "name": "Fornecedores — Materiais", "type": "passivo", "parent": None},
        {"code": "2.1.03", "name": "Salários a Pagar", "type": "passivo", "parent": None},
        {"code": "2.1.04", "name": "Impostos a Recolher", "type": "passivo", "parent": None},
        {"code": "2.1.05", "name": "Empréstimos CP", "type": "passivo", "parent": None},
        {"code": "2.2.01", "name": "Empréstimos LP", "type": "passivo", "parent": None},
        # PL
        {"code": "3.1.01", "name": "Capital Social", "type": "pl", "parent": None},
        {"code": "3.2.01", "name": "Reservas de Capital", "type": "pl", "parent": None},
        {"code": "3.3.01", "name": "Lucros Acumulados", "type": "pl", "parent": None},
        # Receita
        {"code": "4.1.01", "name": "Receita — Consultas", "type": "receita", "parent": None},
        {"code": "4.1.02", "name": "Receita — Exames", "type": "receita", "parent": None},
        {"code": "4.1.03", "name": "Receita — Procedimentos", "type": "receita", "parent": None},
        {"code": "4.1.04", "name": "Receita Financeira", "type": "receita", "parent": None},
        # Despesa
        {"code": "5.1.01", "name": "Custo — Medicamentos", "type": "despesa", "parent": None},
        {"code": "5.1.02", "name": "Custo — Materiais", "type": "despesa", "parent": None},
        {"code": "5.2.01", "name": "Salários — Médicos", "type": "despesa", "parent": None},
        {"code": "5.2.02", "name": "Salários — Enfermagem", "type": "despesa", "parent": None},
        {"code": "5.2.03", "name": "Salários — Administrativo", "type": "despesa", "parent": None},
        {"code": "5.2.04", "name": "Aluguel", "type": "despesa", "parent": None},
        {"code": "5.2.05", "name": "Despesas Administrativas", "type": "despesa", "parent": None},
        {"code": "5.3.01", "name": "Despesa Financeira", "type": "despesa", "parent": None},
        {"code": "5.4.01", "name": "IRPJ e CSLL", "type": "despesa", "parent": None},
    ],
    "metadata": {
        "norma": "CFC 1.374/11",
        "versao": "1.0",
    },
}


async def seed_templates(db: AsyncSession) -> dict[str, int]:
    """
    Popula templates de relatórios e planos de contas.

    Args:
        db: Sessão do banco de dados.

    Returns:
        Dicionário com contagem de registros criados.
    """
    stats = {
        "report_templates": 0,
        "account_templates": 0,
    }

    try:
        # 1. Seed report templates
        dre_servicos = ReportTemplate(
            name=_DRE_TEMPLATE_SERVICOS["name"],
            type=_DRE_TEMPLATE_SERVICOS["type"],
            sector=_DRE_TEMPLATE_SERVICOS["sector"],
            structure=_DRE_TEMPLATE_SERVICOS["structure"],
            formulas=_DRE_TEMPLATE_SERVICOS["formulas"],
            metadata_=_DRE_TEMPLATE_SERVICOS["metadata"],
            is_default=True,
        )
        db.add(dre_servicos)
        stats["report_templates"] += 1

        dre_comercio = ReportTemplate(
            name=_DRE_TEMPLATE_COMERCIO["name"],
            type=_DRE_TEMPLATE_COMERCIO["type"],
            sector=_DRE_TEMPLATE_COMERCIO["sector"],
            structure=_DRE_TEMPLATE_COMERCIO["structure"],
            formulas=_DRE_TEMPLATE_COMERCIO["formulas"],
            metadata_=_DRE_TEMPLATE_COMERCIO["metadata"],
            is_default=True,
        )
        db.add(dre_comercio)
        stats["report_templates"] += 1

        dre_industria = ReportTemplate(
            name=_DRE_TEMPLATE_INDUSTRIA["name"],
            type=_DRE_TEMPLATE_INDUSTRIA["type"],
            sector=_DRE_TEMPLATE_INDUSTRIA["sector"],
            structure=_DRE_TEMPLATE_INDUSTRIA["structure"],
            formulas=_DRE_TEMPLATE_INDUSTRIA["formulas"],
            metadata_=_DRE_TEMPLATE_INDUSTRIA["metadata"],
            is_default=True,
        )
        db.add(dre_industria)
        stats["report_templates"] += 1

        balanco_template = ReportTemplate(
            name=_BALANCO_TEMPLATE_PADRAO["name"],
            type=_BALANCO_TEMPLATE_PADRAO["type"],
            sector=_BALANCO_TEMPLATE_PADRAO["sector"],
            structure=_BALANCO_TEMPLATE_PADRAO["structure"],
            formulas=_BALANCO_TEMPLATE_PADRAO["formulas"],
            metadata_=_BALANCO_TEMPLATE_PADRAO["metadata"],
            is_default=True,
        )
        db.add(balanco_template)
        stats["report_templates"] += 1

        fluxo_caixa = ReportTemplate(
            name=_FLUXO_CAIXA_TEMPLATE["name"],
            type=_FLUXO_CAIXA_TEMPLATE["type"],
            sector=_FLUXO_CAIXA_TEMPLATE["sector"],
            structure=_FLUXO_CAIXA_TEMPLATE["structure"],
            formulas=_FLUXO_CAIXA_TEMPLATE["formulas"],
            metadata_=_FLUXO_CAIXA_TEMPLATE["metadata"],
            is_default=True,
        )
        db.add(fluxo_caixa)
        stats["report_templates"] += 1

        # 2. Seed account templates
        plano_servicos = AccountTemplate(
            name=_PLANO_CONTAS_SERVICOS["name"],
            sector=_PLANO_CONTAS_SERVICOS["sector"],
            accounts=_PLANO_CONTAS_SERVICOS["accounts"],
            metadata_=_PLANO_CONTAS_SERVICOS["metadata"],
            is_default=True,
        )
        db.add(plano_servicos)
        stats["account_templates"] += 1

        plano_comercio = AccountTemplate(
            name=_PLANO_CONTAS_COMERCIO["name"],
            sector=_PLANO_CONTAS_COMERCIO["sector"],
            accounts=_PLANO_CONTAS_COMERCIO["accounts"],
            metadata_=_PLANO_CONTAS_COMERCIO["metadata"],
            is_default=True,
        )
        db.add(plano_comercio)
        stats["account_templates"] += 1

        plano_industria = AccountTemplate(
            name=_PLANO_CONTAS_INDUSTRIA["name"],
            sector=_PLANO_CONTAS_INDUSTRIA["sector"],
            accounts=_PLANO_CONTAS_INDUSTRIA["accounts"],
            metadata_=_PLANO_CONTAS_INDUSTRIA["metadata"],
            is_default=True,
        )
        db.add(plano_industria)
        stats["account_templates"] += 1

        plano_tecnologia = AccountTemplate(
            name=_PLANO_CONTAS_TECNOLOGIA["name"],
            sector=_PLANO_CONTAS_TECNOLOGIA["sector"],
            accounts=_PLANO_CONTAS_TECNOLOGIA["accounts"],
            metadata_=_PLANO_CONTAS_TECNOLOGIA["metadata"],
            is_default=True,
        )
        db.add(plano_tecnologia)
        stats["account_templates"] += 1

        plano_saude = AccountTemplate(
            name=_PLANO_CONTAS_SAUDE["name"],
            sector=_PLANO_CONTAS_SAUDE["sector"],
            accounts=_PLANO_CONTAS_SAUDE["accounts"],
            metadata_=_PLANO_CONTAS_SAUDE["metadata"],
            is_default=True,
        )
        db.add(plano_saude)
        stats["account_templates"] += 1

        await db.commit()

        logger.info("Templates populados com sucesso: %s", stats)
        return stats

    except Exception as e:
        logger.error("Erro ao popular templates: %s", e)
        await db.rollback()
        raise


async def get_report_template(
    db: AsyncSession,
    template_type: str,
    sector: str | None = None,
) -> dict[str, Any] | None:
    """
    Recupera template de relatório por tipo e setor.

    Args:
        db: Sessão do banco de dados.
        template_type: Tipo do template (dre, balanco, etc).
        sector: Setor (opcional).

    Returns:
        Dicionário com dados do template ou None.
    """
    try:
        stmt = select(ReportTemplate).where(ReportTemplate.type == template_type)

        if sector:
            stmt = stmt.where(ReportTemplate.sector == sector)
        else:
            stmt = stmt.where(ReportTemplate.sector.is_(None))

        stmt = stmt.where(ReportTemplate.is_default == True).limit(1)

        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            return None

        return {
            "id": str(template.id),
            "name": template.name,
            "type": template.type,
            "sector": template.sector,
            "structure": template.structure,
            "formulas": template.formulas,
            "metadata": template.metadata_,
        }

    except Exception as e:
        logger.error("Erro ao recuperar template de relatório: %s", e)
        return None


async def get_account_template(
    db: AsyncSession,
    sector: str,
) -> dict[str, Any] | None:
    """
    Recupera plano de contas por setor.

    Args:
        db: Sessão do banco de dados.
        sector: Setor (servicos, comercio, industria, etc).

    Returns:
        Dicionário com dados do template ou None.
    """
    try:
        stmt = (
            select(AccountTemplate)
            .where(AccountTemplate.sector == sector)
            .where(AccountTemplate.is_default == True)
            .limit(1)
        )

        result = await db.execute(stmt)
        template = result.scalar_one_or_none()

        if not template:
            return None

        return {
            "id": str(template.id),
            "name": template.name,
            "sector": template.sector,
            "accounts": template.accounts,
            "metadata": template.metadata_,
        }

    except Exception as e:
        logger.error("Erro ao recuperar plano de contas: %s", e)
        return None


async def list_all_report_templates(
    db: AsyncSession,
    template_type: str | None = None,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    """
    Lista todos os templates de relatórios disponíveis.

    Args:
        db: Sessão do banco de dados.
        template_type: Filtro por tipo (opcional).
        sector: Filtro por setor (opcional).

    Returns:
        Lista de templates.
    """
    try:
        stmt = select(ReportTemplate)

        if template_type:
            stmt = stmt.where(ReportTemplate.type == template_type)
        if sector:
            stmt = stmt.where(ReportTemplate.sector == sector)

        stmt = stmt.order_by(ReportTemplate.type, ReportTemplate.sector)

        result = await db.execute(stmt)
        templates = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "name": t.name,
                "type": t.type,
                "sector": t.sector,
                "structure": t.structure,
                "formulas": t.formulas,
                "metadata": t.metadata_,
                "is_default": t.is_default,
            }
            for t in templates
        ]

    except Exception as e:
        logger.error("Erro ao listar templates de relatórios: %s", e)
        return []


async def list_all_account_templates(
    db: AsyncSession,
    sector: str | None = None,
) -> list[dict[str, Any]]:
    """
    Lista todos os planos de contas disponíveis.

    Args:
        db: Sessão do banco de dados.
        sector: Filtro por setor (opcional).

    Returns:
        Lista de templates.
    """
    try:
        stmt = select(AccountTemplate)

        if sector:
            stmt = stmt.where(AccountTemplate.sector == sector)

        stmt = stmt.order_by(AccountTemplate.sector)

        result = await db.execute(stmt)
        templates = result.scalars().all()

        return [
            {
                "id": str(t.id),
                "name": t.name,
                "sector": t.sector,
                "accounts": t.accounts,
                "metadata": t.metadata_,
                "is_default": t.is_default,
            }
            for t in templates
        ]

    except Exception as e:
        logger.error("Erro ao listar planos de contas: %s", e)
        return []
