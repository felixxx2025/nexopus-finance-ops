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
        dre_template = ReportTemplate(
            name=_DRE_TEMPLATE_SERVICOS["name"],
            type=_DRE_TEMPLATE_SERVICOS["type"],
            sector=_DRE_TEMPLATE_SERVICOS["sector"],
            structure=_DRE_TEMPLATE_SERVICOS["structure"],
            formulas=_DRE_TEMPLATE_SERVICOS["formulas"],
            metadata_=_DRE_TEMPLATE_SERVICOS["metadata"],
            is_default=True,
        )
        db.add(dre_template)
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
