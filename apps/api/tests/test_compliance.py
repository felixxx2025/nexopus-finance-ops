"""
Testes de compliance — validação de regras contábeis brasileiras.
"""
import pytest
from decimal import Decimal
from services.compliance.rules import (
    validate_balance,
    validate_double_entry,
    validate_cnpj,
    ComplianceError,
)


# ── validate_cnpj ──────────────────────────────────────────────────────────────

def test_cnpj_valido():
    """CNPJ válido da Petrobras deve passar."""
    assert validate_cnpj("33000167000101") is True


def test_cnpj_invalido():
    """CNPJ inválido deve retornar False."""
    assert validate_cnpj("00000000000000") is False


def test_cnpj_com_formatacao():
    """CNPJ com pontuação deve ser normalizado e validado."""
    assert validate_cnpj("33.000.167/0001-01") is True


def test_cnpj_muito_curto():
    """CNPJ com menos de 14 dígitos deve retornar False."""
    assert validate_cnpj("1234567") is False


# ── validate_double_entry ──────────────────────────────────────────────────────

def test_partida_dobrada_valida():
    """Débito == Crédito deve retornar True."""
    items = [
        {"type": "debit",  "amount": "1000.00"},
        {"type": "credit", "amount": "1000.00"},
    ]
    assert validate_double_entry(items) is True


def test_partida_dobrada_invalida():
    """Débito != Crédito deve levantar ComplianceError."""
    items = [
        {"type": "debit",  "amount": "1000.00"},
        {"type": "credit", "amount": "900.00"},
    ]
    with pytest.raises(ComplianceError, match="desequilibrado"):
        validate_double_entry(items)


def test_partida_dobrada_multiplas_contas():
    """Múltiplas contas balanceadas devem passar."""
    items = [
        {"type": "debit",  "amount": "500.00"},
        {"type": "debit",  "amount": "500.00"},
        {"type": "credit", "amount": "1000.00"},
    ]
    assert validate_double_entry(items) is True


def test_partida_dobrada_lista_vazia():
    """Lista vazia deve retornar True (sem desequilíbrio)."""
    assert validate_double_entry([]) is True


# ── validate_balance ───────────────────────────────────────────────────────────

def test_equacao_patrimonial_valida():
    """Ativo == Passivo + PL deve retornar True."""
    assert validate_balance({"ativo": "100000", "passivo": "60000", "pl": "40000"}) is True


def test_equacao_patrimonial_invalida():
    """Ativo != Passivo + PL deve levantar ComplianceError."""
    with pytest.raises(ComplianceError, match="não fecha"):
        validate_balance({"ativo": "100000", "passivo": "60000", "pl": "30000"})


def test_equacao_patrimonial_zeros():
    """Todos zeros deve fechar."""
    assert validate_balance({"ativo": "0", "passivo": "0", "pl": "0"}) is True
