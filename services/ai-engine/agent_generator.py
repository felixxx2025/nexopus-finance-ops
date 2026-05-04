"""
Agent Generator — cria lançamentos contábeis (journal_entries + journal_items)
a partir dos dados classificados.

Princípio da Partida Dobrada: todo débito tem um crédito correspondente de igual valor.
"""
from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any


def generate_entries(data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Converte lançamentos classificados em pares de débito/crédito prontos
    para inserção nas tabelas journal_entries e journal_items.

    Args:
        data: Saída do agent_classifier com campo "lançamentos" classificados.

    Returns:
        Lista de dicts compatíveis com o schema journal_entries + journal_items.
    """
    entries = data.get("lançamentos", [])
    company_id = data.get("empresa", {}).get("cnpj", "")
    period_start = data.get("período", {}).get("data_inicio", "")

    journal_entries = []

    for item in entries:
        account = item.get("conta", "Conta desconhecida")
        tipo_conta = item.get("tipo_conta", "")
        valor = Decimal(str(item.get("valor", 0)))
        descricao = item.get("descrição", "")

        entry_id = str(uuid.uuid4())

        # Determina débito/crédito pela natureza da conta (convenção brasileira)
        debit_type, credit_type = _determine_dc(tipo_conta, valor)

        journal_entries.append({
            "journal_entry": {
                "id": entry_id,
                "company_id": company_id,
                "date": period_start,
                "description": descricao,
            },
            "items": [
                {
                    "id": str(uuid.uuid4()),
                    "entry_id": entry_id,
                    "account": account,
                    "type": debit_type,
                    "amount": str(abs(valor)),
                },
                {
                    "id": str(uuid.uuid4()),
                    "entry_id": entry_id,
                    "account": _contrapartida(tipo_conta),
                    "type": credit_type,
                    "amount": str(abs(valor)),
                },
            ],
        })

    return journal_entries


def _determine_dc(tipo_conta: str, valor: Decimal) -> tuple[str, str]:
    """
    Retorna (debit_side, credit_side) conforme natureza da conta.
    Contas de ativo e despesa têm natureza devedora; passivo, receita e PL, credora.
    """
    devedoras = {"ativo", "despesa"}
    if tipo_conta.lower() in devedoras:
        return ("debit", "credit")
    return ("credit", "debit")


def _contrapartida(tipo_conta: str) -> str:
    """Retorna conta de contrapartida padrão para o tipo informado."""
    mapa = {
        "receita": "Caixa / Bancos",
        "despesa": "Caixa / Bancos",
        "ativo": "Capital Social",
        "passivo": "Ativo Circulante",
        "pl": "Resultado do Exercício",
    }
    return mapa.get(tipo_conta.lower(), "Conta de Contrapartida")
