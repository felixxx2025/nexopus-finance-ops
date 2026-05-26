"""
Testes do motor contábil (AccountingEngine) — lógica pura sem banco de dados.
Usa mocks para a sessão async do SQLAlchemy.
"""
from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import sys
import os

# Garante que o root do projeto está no path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from services.accounting_core.engine import AccountingEngine


# ── Fixtures ───────────────────────────────────────────────────────────────────

def _mock_db_session(rows: list):
    """Cria um mock de AsyncSession que retorna `rows` ao executar queries."""
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)
    return session


# ── calculate_balance ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_calculate_balance_empty():
    """Sem lançamentos retorna dicionário vazio."""
    db = _mock_db_session([])
    engine = AccountingEngine(db)
    result = await engine.calculate_balance("00000000-0000-0000-0000-000000000001", 2025)
    assert result == {}


@pytest.mark.asyncio
async def test_calculate_balance_receita_credora():
    """Conta de receita (natureza credora): crédito aumenta o saldo."""
    import uuid
    acc_id = uuid.uuid4()
    # (account_id, account_name, account_type, item_type, total)
    rows = [(acc_id, "Receita de Vendas", "receita", "credit", Decimal("100000"))]
    db = _mock_db_session(rows)
    engine = AccountingEngine(db)
    result = await engine.calculate_balance(str(uuid.uuid4()), 2025)
    assert str(acc_id) in result
    assert result[str(acc_id)]["balance"] == Decimal("100000")
    assert result[str(acc_id)]["type"] == "receita"


@pytest.mark.asyncio
async def test_calculate_balance_ativo_devedor():
    """Conta de ativo (natureza devedora): débito aumenta o saldo."""
    import uuid
    acc_id = uuid.uuid4()
    rows = [(acc_id, "Caixa", "ativo", "debit", Decimal("50000"))]
    db = _mock_db_session(rows)
    engine = AccountingEngine(db)
    result = await engine.calculate_balance(str(uuid.uuid4()), 2025)
    assert result[str(acc_id)]["balance"] == Decimal("50000")


@pytest.mark.asyncio
async def test_calculate_balance_invalid_company_id():
    """company_id inválido deve levantar ValueError."""
    db = _mock_db_session([])
    engine = AccountingEngine(db)
    with pytest.raises(ValueError, match="company_id inválido"):
        await engine.calculate_balance("nao-e-um-uuid", 2025)


# ── generate_dre ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_generate_dre_structure():
    """DRE deve conter os campos esperados."""
    import uuid
    acc_receita = uuid.uuid4()
    acc_despesa = uuid.uuid4()
    rows = [
        (acc_receita, "Receita de Serviços", "receita", "credit", Decimal("200000")),
        (acc_despesa, "Despesas de Pessoal", "despesa",  "debit",  Decimal("80000")),
    ]
    db = _mock_db_session(rows)
    engine = AccountingEngine(db)
    dre = await engine.generate_dre(str(uuid.uuid4()), 2025)

    expected_keys = {
        "receita_bruta", "deducoes", "receita_liquida", "cmv",
        "lucro_bruto", "despesas_operacionais", "ebit",
        "resultado_financeiro", "lucro_antes_ir", "ir_csll",
        "lucro_liquido", "_meta",
    }
    assert expected_keys.issubset(dre.keys())


@pytest.mark.asyncio
async def test_generate_dre_receita_bruta():
    """DRE deve capturar a receita bruta corretamente."""
    import uuid
    acc_id = uuid.uuid4()
    rows = [(acc_id, "Receita de Vendas", "receita", "credit", Decimal("150000"))]
    db = _mock_db_session(rows)
    engine = AccountingEngine(db)
    dre = await engine.generate_dre(str(uuid.uuid4()), 2025)
    assert dre["receita_bruta"] == 150000.0


@pytest.mark.asyncio
async def test_generate_dre_zero_receita():
    """DRE sem receita deve ter lucro_liquido == 0."""
    import uuid
    db = _mock_db_session([])
    engine = AccountingEngine(db)
    dre = await engine.generate_dre(str(uuid.uuid4()), 2025)
    assert dre["receita_bruta"] == 0.0
    assert dre["lucro_liquido"] == 0.0


# ── generate_balance_sheet ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_balance_sheet_structure():
    """Balanço deve conter ativo, passivo, pl, totais e equacao_fecha."""
    import uuid
    db = _mock_db_session([])
    engine = AccountingEngine(db)
    bal = await engine.generate_balance_sheet(str(uuid.uuid4()), 2025)
    assert "ativo" in bal
    assert "passivo" in bal
    assert "pl" in bal
    assert "totais" in bal
    assert "equacao_fecha" in bal


@pytest.mark.asyncio
async def test_balance_sheet_equacao_fecha_vazio():
    """Balanço vazio (todos zeros) deve fechar a equação patrimonial."""
    import uuid
    db = _mock_db_session([])
    engine = AccountingEngine(db)
    bal = await engine.generate_balance_sheet(str(uuid.uuid4()), 2025)
    assert bal["equacao_fecha"] is True


@pytest.mark.asyncio
async def test_balance_sheet_equacao_fecha_com_dados():
    """Ativo == Passivo + PL deve ser verdadeiro com dados balanceados."""
    import uuid
    acc_ativo = uuid.uuid4()
    acc_passivo = uuid.uuid4()
    acc_pl = uuid.uuid4()
    rows = [
        (acc_ativo,  "Caixa",          "ativo",   "debit",  Decimal("100000")),
        (acc_passivo,"Fornecedores",   "passivo",  "credit", Decimal("60000")),
        (acc_pl,     "Capital Social", "pl",       "credit", Decimal("40000")),
    ]
    db = _mock_db_session(rows)
    engine = AccountingEngine(db)
    bal = await engine.generate_balance_sheet(str(uuid.uuid4()), 2025)
    assert bal["equacao_fecha"] is True
    assert bal["totais"]["ativo"] == 100000.0
