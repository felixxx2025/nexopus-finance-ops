"""
Motor Contábil — núcleo de cálculo financeiro.

Responsável por:
- Calcular saldos por conta (débito/crédito) conforme natureza contábil
- Gerar DRE (Demonstrativo de Resultado do Exercício)
- Gerar Balanço Patrimonial (Ativo = Passivo + PL)

Referências: Lei nº 6.404/1976 · NBC TG 26
"""
from __future__ import annotations

import uuid as uuid_mod
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

# Importação relativa tolerante ao PYTHONPATH do container
try:
    from packages.db.models import Account, JournalEntry, JournalItem  # type: ignore
except ModuleNotFoundError:
    from db.models import Account, JournalEntry, JournalItem  # type: ignore


# Contas com natureza devedora (saldo normal a débito)
_DEVEDORAS = {"ativo", "despesa"}
# Contas com natureza credora (saldo normal a crédito)
_CREDORAS = {"passivo", "receita", "pl"}

# Plano de contas padrão NBC TG — usado para seed inicial
PLANO_CONTAS_PADRAO: list[dict] = [
    # ATIVO
    {"code": "1",        "name": "ATIVO",                        "type": "ativo"},
    {"code": "1.1",      "name": "Ativo Circulante",              "type": "ativo"},
    {"code": "1.1.01",   "name": "Caixa e Equivalentes",          "type": "ativo"},
    {"code": "1.1.02",   "name": "Contas a Receber",              "type": "ativo"},
    {"code": "1.1.03",   "name": "Estoques",                      "type": "ativo"},
    {"code": "1.1.04",   "name": "Outros Ativos Circulantes",     "type": "ativo"},
    {"code": "1.2",      "name": "Ativo Não Circulante",          "type": "ativo"},
    {"code": "1.2.01",   "name": "Imobilizado",                   "type": "ativo"},
    {"code": "1.2.02",   "name": "Intangível",                    "type": "ativo"},
    {"code": "1.2.03",   "name": "Investimentos",                 "type": "ativo"},
    # PASSIVO
    {"code": "2",        "name": "PASSIVO",                       "type": "passivo"},
    {"code": "2.1",      "name": "Passivo Circulante",            "type": "passivo"},
    {"code": "2.1.01",   "name": "Fornecedores",                  "type": "passivo"},
    {"code": "2.1.02",   "name": "Salários e Encargos a Pagar",   "type": "passivo"},
    {"code": "2.1.03",   "name": "Obrigações Fiscais",             "type": "passivo"},
    {"code": "2.1.04",   "name": "Empréstimos CP",                "type": "passivo"},
    {"code": "2.2",      "name": "Passivo Não Circulante",        "type": "passivo"},
    {"code": "2.2.01",   "name": "Empréstimos LP",                "type": "passivo"},
    {"code": "2.2.02",   "name": "Debêntures",                    "type": "passivo"},
    # PL
    {"code": "3",        "name": "PATRIMÔNIO LÍQUIDO",            "type": "pl"},
    {"code": "3.1",      "name": "Capital Social",                "type": "pl"},
    {"code": "3.2",      "name": "Reservas de Capital",           "type": "pl"},
    {"code": "3.3",      "name": "Lucros/Prejuízos Acumulados",   "type": "pl"},
    # RECEITA
    {"code": "4",        "name": "RECEITAS",                      "type": "receita"},
    {"code": "4.1",      "name": "Receita Bruta de Vendas",       "type": "receita"},
    {"code": "4.2",      "name": "Receita de Serviços",           "type": "receita"},
    {"code": "4.3",      "name": "Receitas Financeiras",          "type": "receita"},
    {"code": "4.4",      "name": "Outras Receitas Operacionais",  "type": "receita"},
    # DESPESA
    {"code": "5",        "name": "DESPESAS",                      "type": "despesa"},
    {"code": "5.1",      "name": "Custo dos Produtos Vendidos",   "type": "despesa"},
    {"code": "5.2",      "name": "Despesas com Pessoal",          "type": "despesa"},
    {"code": "5.3",      "name": "Despesas Administrativas",      "type": "despesa"},
    {"code": "5.4",      "name": "Despesas Comerciais",           "type": "despesa"},
    {"code": "5.5",      "name": "Despesas Financeiras",          "type": "despesa"},
    {"code": "5.6",      "name": "Depreciação e Amortização",     "type": "despesa"},
    {"code": "5.7",      "name": "Impostos e Taxas",              "type": "despesa"},
]


class AccountingEngine:
    """
    Motor contábil principal.

    Recebe uma sessão de banco de dados (SQLAlchemy AsyncSession)
    e executa os cálculos financeiros conforme a Lei nº 6.404/1976.
    """

    def __init__(self, db_session: AsyncSession) -> None:
        self.db = db_session

    # ── Saldos ─────────────────────────────────────────────────────────────────

    async def calculate_balance(
        self, company_id: str, year: int
    ) -> dict[str, dict[str, Any]]:
        """
        Soma débitos e créditos de cada conta para o ano informado.

        Regra:
        - Contas devedoras (ativo, despesa): saldo = Σdébitos − Σcréditos
        - Contas credoras (passivo, receita, pl): saldo = Σcréditos − Σdébitos

        Returns:
            { account_id: {"name": str, "type": str, "balance": Decimal} }
        """
        try:
            company_uuid = uuid_mod.UUID(company_id)
        except ValueError as exc:
            raise ValueError(f"company_id inválido: {company_id}") from exc

        stmt = (
            select(
                JournalItem.account_id,
                Account.name.label("account_name"),
                Account.type.label("account_type"),
                Account.code.label("account_code"),
                JournalItem.type.label("item_type"),
                func.sum(JournalItem.amount).label("total"),
            )
            .join(JournalEntry, JournalItem.entry_id == JournalEntry.id)
            .join(Account, JournalItem.account_id == Account.id)
            .where(JournalEntry.company_id == company_uuid)
            .where(func.extract("year", JournalEntry.date) == year)
            .where(JournalEntry.status == "approved")  # somente lançamentos aprovados
            .group_by(
                JournalItem.account_id,
                Account.name,
                Account.type,
                Account.code,
                JournalItem.type,
            )
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        balances: dict[str, dict[str, Any]] = {}
        for account_id, account_name, account_type, account_code, item_type, total in rows:
            key = str(account_id)
            if key not in balances:
                balances[key] = {
                    "name": account_name,
                    "type": account_type,
                    "code": account_code or "",
                    "balance": Decimal("0"),
                }
            amount = Decimal(str(total))
            if account_type in _DEVEDORAS:
                balances[key]["balance"] += amount if item_type == "debit" else -amount
            else:
                balances[key]["balance"] += amount if item_type == "credit" else -amount

        return balances

    # ── DRE ────────────────────────────────────────────────────────────────────

    async def generate_dre(self, company_id: str, year: int) -> dict[str, Any]:
        """
        Gera DRE: Receita Bruta − Deduções − CMV − Despesas = Lucro Líquido.

        Simplificação: IR/CSLL calculado como 34% do lucro antes do IR (se positivo).

        Returns:
            Estrutura da DRE pronta para armazenamento em JSONB.
        """
        balances = await self.calculate_balance(company_id, year)

        receita_total = Decimal("0")
        despesa_total = Decimal("0")

        for info in balances.values():
            if info["type"] == "receita":
                receita_total += info["balance"]
            elif info["type"] == "despesa":
                despesa_total += info["balance"]

        # Estimativas baseadas em percentuais típicos de uma empresa brasileira
        deducoes = -(receita_total * Decimal("0.06")).quantize(Decimal("0.01"))
        receita_liquida = receita_total + deducoes
        cmv = -(receita_liquida * Decimal("0.34")).quantize(Decimal("0.01"))
        lucro_bruto = receita_liquida + cmv
        despesas_operacionais = -despesa_total
        ebit = lucro_bruto + despesas_operacionais
        resultado_financeiro = Decimal("0")  # sem dados de RF no schema atual
        lucro_antes_ir = ebit + resultado_financeiro
        ir_csll = (
            -(lucro_antes_ir * Decimal("0.34")).quantize(Decimal("0.01"))
            if lucro_antes_ir > 0
            else Decimal("0")
        )
        lucro_liquido = lucro_antes_ir + ir_csll

        # Breakdown por conta
        receitas_detalhe = {
            info["name"]: float(info["balance"])
            for info in balances.values() if info["type"] == "receita" and info["balance"] > 0
        }
        despesas_detalhe = {
            info["name"]: float(info["balance"])
            for info in balances.values() if info["type"] == "despesa" and info["balance"] > 0
        }

        return {
            "receita_bruta": float(receita_total),
            "deducoes": float(deducoes),
            "receita_liquida": float(receita_liquida),
            "cmv": float(cmv),
            "lucro_bruto": float(lucro_bruto),
            "despesas_operacionais": float(despesas_operacionais),
            "ebit": float(ebit),
            "resultado_financeiro": float(resultado_financeiro),
            "lucro_antes_ir": float(lucro_antes_ir),
            "ir_csll": float(ir_csll),
            "lucro_liquido": float(lucro_liquido),
            "receitas_detalhe": receitas_detalhe,
            "despesas_detalhe": despesas_detalhe,
            "_meta": {
                "company_id": company_id,
                "year": year,
                "total_contas": len(balances),
                "metodo": "NBC TG 26",
                "apenas_aprovados": True,
            },
        }

    # ── Balanço Patrimonial ────────────────────────────────────────────────────

    async def generate_balance_sheet(
        self, company_id: str, year: int
    ) -> dict[str, Any]:
        """
        Gera Balanço Patrimonial.

        Valida equação contábil: Ativo == Passivo + Patrimônio Líquido.

        Returns:
            { "ativo": {contas...}, "passivo": {contas...}, "pl": {contas...},
              "totais": {"ativo": float, "passivo": float, "pl": float},
              "equacao_fecha": bool }
        """
        balances = await self.calculate_balance(company_id, year)

        ativo: dict[str, float] = {}
        passivo: dict[str, float] = {}
        pl: dict[str, float] = {}

        for acc_id, info in balances.items():
            val = float(info["balance"])
            name = info["name"]
            if info["type"] == "ativo":
                ativo[name] = val
            elif info["type"] == "passivo":
                passivo[name] = val
            elif info["type"] == "pl":
                pl[name] = val

        total_ativo = Decimal(str(sum(ativo.values())))
        total_passivo = Decimal(str(sum(passivo.values())))
        total_pl = Decimal(str(sum(pl.values())))

        equacao_fecha = total_ativo == (total_passivo + total_pl)

        diferenca = total_ativo - (total_passivo + total_pl)

        return {
            "ativo": ativo,
            "passivo": passivo,
            "pl": pl,
            "totais": {
                "ativo": float(total_ativo),
                "passivo": float(total_passivo),
                "pl": float(total_pl),
            },
            "equacao_fecha": equacao_fecha,
            "_meta": {
                "company_id": company_id,
                "year": year,
                "diferenca": float(diferenca),
                "lei_ref": "Lei 6.404/1976",
                "apenas_aprovados": True,
            },
        }

    async def seed_plano_de_contas(self, company_id: str) -> int:
        """
        Insere o plano de contas padrão NBC TG para a empresa, se ainda não existir.

        Returns:
            Número de contas inseridas (0 se já existiam).
        """
        try:
            company_uuid = uuid_mod.UUID(company_id)
        except ValueError as exc:
            raise ValueError(f"company_id inválido: {company_id}") from exc

        # Verifica se já há contas
        existing = await self.db.execute(
            select(func.count(Account.id)).where(Account.company_id == company_uuid)
        )
        count = existing.scalar_one()
        if count > 0:
            return 0

        inserted = 0
        for item in PLANO_CONTAS_PADRAO:
            acc = Account(
                company_id=company_uuid,
                code=item["code"],
                name=item["name"],
                type=item["type"],
            )
            self.db.add(acc)
            inserted += 1

        await self.db.commit()
        return inserted

