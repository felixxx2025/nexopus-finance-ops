"""
Compliance Engine — validação de regras contábeis e fiscais brasileiras.

Referências:
- Lei nº 6.404/1976 (Lei das S.A.)
- NBC TG 26 (Apresentação das Demonstrações Contábeis)
- Plano de Contas Referencial da RFB
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any


class ComplianceError(Exception):
    """Levantado quando uma regra contábil é violada."""


def validate_balance(balance: dict[str, Any]) -> bool:
    """
    Valida a equação patrimonial fundamental:
        Ativo = Passivo + Patrimônio Líquido

    Args:
        balance: {
            "ativo": Decimal,
            "passivo": Decimal,
            "pl": Decimal
        }

    Returns:
        True se a equação for satisfeita.

    Raises:
        ComplianceError: Se o balanço não fechar.
    """
    ativo = Decimal(str(balance.get("ativo", 0)))
    passivo = Decimal(str(balance.get("passivo", 0)))
    pl = Decimal(str(balance.get("pl", 0)))

    if ativo != passivo + pl:
        diff = ativo - (passivo + pl)
        raise ComplianceError(
            f"Balanço não fecha. Ativo={ativo}, Passivo+PL={passivo + pl}, "
            f"Diferença={diff}"
        )
    return True


def validate_double_entry(entries: list[dict[str, Any]]) -> bool:
    """
    Valida o princípio da Partida Dobrada:
    para cada lançamento, total de débitos == total de créditos.

    Args:
        entries: Lista de journal_items do mesmo journal_entry.

    Returns:
        True se débitos == créditos.

    Raises:
        ComplianceError: Se o lançamento não estiver balanceado.
    """
    total_debit = sum(
        Decimal(str(i["amount"])) for i in entries if i.get("type") == "debit"
    )
    total_credit = sum(
        Decimal(str(i["amount"])) for i in entries if i.get("type") == "credit"
    )

    if total_debit != total_credit:
        raise ComplianceError(
            f"Lançamento desequilibrado. Débito={total_debit}, Crédito={total_credit}"
        )
    return True


def validate_cnpj(cnpj: str) -> bool:
    """
    Valida CNPJ conforme algoritmo da RFB.

    Args:
        cnpj: String com 14 dígitos (sem formatação).

    Returns:
        True se válido.
    """
    cnpj = "".join(filter(str.isdigit, cnpj))

    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False

    def _calc_digit(cnpj_digits: list[int], weights: list[int]) -> int:
        total = sum(d * w for d, w in zip(cnpj_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    digits = [int(c) for c in cnpj]
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    d1 = _calc_digit(digits[:12], weights1)
    d2 = _calc_digit(digits[:13], weights2)

    return digits[12] == d1 and digits[13] == d2
