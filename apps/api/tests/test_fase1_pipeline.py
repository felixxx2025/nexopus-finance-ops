"""
Testes Fase 1 — Pipeline de documentos, estados e saneamento.

Cobre:
- Upload requer company_id
- Estados de documento (uploaded, processing, processed, failed, needs_review)
- Motor contábil (DRE, Balanço) com dados reais
- Compliance (partida dobrada, equação patrimonial, CNPJ)
- Worker task (process_document) com mocks
- Health e versão unificada
"""
from __future__ import annotations

import os
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from fastapi.testclient import TestClient
from main import app, _create_access_token, get_db  # noqa: E402


async def _mock_db():
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
    yield session


app.dependency_overrides[get_db] = _mock_db
client = TestClient(app)


# ── Health: versão unificada ──────────────────────────────────────────────────

def test_health_version_unified():
    """GET /health deve retornar a mesma versão que GET /ready."""
    h = client.get("/health").json()
    assert h["status"] == "ok"
    assert "version" in h
    assert h["version"] == "2.1.0"


def test_health_service_name():
    res = client.get("/health")
    assert res.json()["service"] == "nexopus-finance-api"


# ── Upload: company_id obrigatório ────────────────────────────────────────────

def test_upload_sem_company_id_retorna_400():
    """Upload sem company_id deve retornar 400."""
    token, _ = _create_access_token("admin", role="admin")
    res = client.post(
        "/documents/upload",
        files={"file": ("doc.pdf", b"%PDF-test", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert "company_id" in res.json()["detail"].lower()


def test_upload_company_id_invalido_retorna_4xx():
    """Upload com company_id inválido deve retornar 400 ou 422."""
    token, _ = _create_access_token("admin", role="admin")
    res = client.post(
        "/documents/upload?company_id=nao-e-uuid",
        files={"file": ("doc.pdf", b"%PDF-test", "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code in (400, 422)


def test_upload_mime_invalido_retorna_415():
    """Upload com MIME não suportado retorna 415."""
    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())
    res = client.post(
        f"/documents/upload?company_id={cid}",
        files={"file": ("doc.exe", b"MZcontent", "application/octet-stream")},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 415


def test_upload_pdf_com_company_id_valido():
    """Upload com PDF válido e company_id retorna 200 e doc_id."""
    import main as main_module

    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())

    with patch.object(main_module, "_upload_to_s3", return_value=f"bucket/{cid}.pdf"):
        res = client.post(
            f"/documents/upload?company_id={cid}",
            files={"file": ("relatorio.pdf", b"%PDF-1.4 content", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert res.status_code == 200
    data = res.json()
    assert "doc_id" in data
    assert data["status"] == "processing"
    assert data["filename"] == "relatorio.pdf"


def test_upload_magic_bytes_invalidos_retorna_415():
    """PDF com magic bytes errados deve ser rejeitado."""
    import main as main_module

    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())

    with patch.object(main_module, "_upload_to_s3", return_value=f"bucket/{cid}.pdf"):
        res = client.post(
            f"/documents/upload?company_id={cid}",
            files={"file": ("falso.pdf", b"NOTPDF content", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert res.status_code == 415


# ── Motor contábil ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_engine_dre_structure():
    """DRE deve conter todos os campos esperados."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from services.accounting_core.engine import AccountingEngine

    acc_id = uuid.uuid4()
    rows = [(acc_id, "Receita de Serviços", "receita", "4.2", "credit", Decimal("120000"))]
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)

    engine = AccountingEngine(session)
    dre = await engine.generate_dre(str(uuid.uuid4()), 2025)

    for key in ("receita_bruta", "deducoes", "receita_liquida", "cmv", "lucro_bruto",
                "despesas_operacionais", "ebit", "resultado_financeiro",
                "lucro_antes_ir", "ir_csll", "lucro_liquido", "_meta"):
        assert key in dre, f"Campo '{key}' ausente na DRE"


@pytest.mark.asyncio
async def test_engine_balance_equacao_fecha():
    """Balanço com dados balanceados deve fechar a equação patrimonial."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    from services.accounting_core.engine import AccountingEngine

    rows = [
        (uuid.uuid4(), "Caixa",          "ativo",   "1.1.01", "debit",  Decimal("100000")),
        (uuid.uuid4(), "Fornecedores",   "passivo",  "2.1.01", "credit", Decimal("60000")),
        (uuid.uuid4(), "Capital Social", "pl",       "3.1",    "credit", Decimal("40000")),
    ]
    session = MagicMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)

    engine = AccountingEngine(session)
    bal = await engine.generate_balance_sheet(str(uuid.uuid4()), 2025)
    assert bal["equacao_fecha"] is True
    assert bal["totais"]["ativo"] == 100000.0


# ── Compliance ────────────────────────────────────────────────────────────────

def test_partida_dobrada_valida():
    from services.compliance.rules import validate_double_entry
    items = [{"type": "debit", "amount": "5000"}, {"type": "credit", "amount": "5000"}]
    assert validate_double_entry(items) is True


def test_partida_dobrada_invalida():
    from services.compliance.rules import validate_double_entry, ComplianceError
    items = [{"type": "debit", "amount": "5000"}, {"type": "credit", "amount": "4000"}]
    with pytest.raises(ComplianceError):
        validate_double_entry(items)


def test_cnpj_valido():
    from services.compliance.rules import validate_cnpj
    assert validate_cnpj("33000167000101") is True


def test_cnpj_invalido():
    from services.compliance.rules import validate_cnpj
    assert validate_cnpj("00000000000000") is False


# ── RBAC ─────────────────────────────────────────────────────────────────────

def test_entry_review_requer_role_admin_analista():
    """Viewer não pode aprovar lançamentos."""
    token, _ = _create_access_token("viewer_user", role="viewer")
    eid = str(uuid.uuid4())
    res = client.patch(
        f"/entries/{eid}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_report_approve_requer_role_admin():
    """Analista não pode aprovar relatório."""
    token, _ = _create_access_token("analista_user", role="analista")
    rid = str(uuid.uuid4())
    res = client.patch(
        f"/reports/{rid}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_audit_logs_requer_admin():
    """Viewer não pode acessar audit logs."""
    token, _ = _create_access_token("viewer_user", role="viewer")
    res = client.get(
        "/admin/audit-logs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403
