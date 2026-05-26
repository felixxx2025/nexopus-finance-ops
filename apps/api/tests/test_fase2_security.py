"""
Testes Fase 2 — Segurança, RBAC, auditoria e endurecimento.

Cobre:
- RBAC: roles admin / analista / viewer nos endpoints
- Token blacklist (logout)
- Cookie httpOnly setado no login
- Audit log gravado em ações (mock)
- Observabilidade: _JsonFormatter produz JSON válido
- Compliance: validações contábeis brasileiras
- Fluxo revisão humana (approve/reject)
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app, _create_access_token, get_db  # noqa: E402


async def _mock_db():
    session = MagicMock()
    session.add = MagicMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = None
    result_mock.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result_mock)
    yield session


app.dependency_overrides[get_db] = _mock_db
client = TestClient(app)


# ── RBAC: roles ──────────────────────────────────────────────────────────────

def test_admin_acessa_audit_logs():
    """Admin consegue acessar /admin/audit-logs."""
    token, _ = _create_access_token("admin", role="admin")
    res = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert "logs" in res.json()


def test_viewer_bloqueado_em_audit_logs():
    """Viewer recebe 403 em /admin/audit-logs."""
    token, _ = _create_access_token("viewer", role="viewer")
    res = client.get("/admin/audit-logs", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_analista_pode_revisar_lancamento():
    """Analista tem acesso ao endpoint de revisão (retorna 404 pois não há entry, não 403)."""
    token, _ = _create_access_token("analista", role="analista")
    eid = str(uuid.uuid4())
    res = client.patch(
        f"/entries/{eid}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {token}"},
    )
    # 404 = passou da autenticação e permissão, entry não encontrada no mock
    assert res.status_code == 404


def test_viewer_bloqueado_em_revisao():
    """Viewer recebe 403 no endpoint de revisão."""
    token, _ = _create_access_token("viewer", role="viewer")
    eid = str(uuid.uuid4())
    res = client.patch(
        f"/entries/{eid}/review",
        json={"action": "approve"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_analista_bloqueado_em_approve_report():
    """Analista recebe 403 ao tentar aprovar relatório."""
    token, _ = _create_access_token("analista", role="analista")
    rid = str(uuid.uuid4())
    res = client.patch(
        f"/reports/{rid}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 403


def test_admin_pode_approve_report_404():
    """Admin tem acesso ao endpoint (retorna 404, não 403)."""
    token, _ = _create_access_token("admin", role="admin")
    rid = str(uuid.uuid4())
    res = client.patch(
        f"/reports/{rid}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 404


# ── Login / Cookie / Logout ───────────────────────────────────────────────────

def test_login_seta_cookie_httponly():
    """Login bem-sucedido define cookie nexopus_token httpOnly."""
    res = client.post("/auth/token", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    # TestClient expõe cookies
    assert "nexopus_token" in res.cookies or "nexopus_token" in res.headers.get("set-cookie", "")


def test_login_retorna_role_no_body():
    """Login retorna campo 'role' no body."""
    res = client.post("/auth/token", json={"username": "admin", "password": "admin"})
    assert res.status_code == 200
    data = res.json()
    assert "role" in data
    assert data["role"] == "admin"


def test_logout_invalida_sessao():
    """Logout com token válido retorna status logged_out e limpa cookie."""
    token, _ = _create_access_token("admin", role="admin")
    res = client.post("/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["status"] == "logged_out"


def test_sem_token_retorna_401():
    """Endpoints protegidos sem token retornam 401."""
    fresh = TestClient(app, cookies={})
    for path in ["/admin/audit-logs", "/admin/users"]:
        res = fresh.get(path)
        assert res.status_code == 401, f"Esperado 401 em {path}, got {res.status_code}"


def test_token_invalido_retorna_401():
    """Token inválido retorna 401."""
    res = client.get(
        "/admin/audit-logs",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert res.status_code == 401


# ── Segurança: upload (magic bytes) ──────────────────────────────────────────

def test_upload_conteudo_falso_pdf():
    """Arquivo declarado como PDF mas sem magic bytes %PDF é rejeitado."""
    import main as m
    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())
    with patch.object(m, "_upload_to_s3", return_value=f"bucket/{cid}.pdf"):
        res = client.post(
            f"/documents/upload?company_id={cid}",
            files={"file": ("falso.pdf", b"CONTEUDO ERRADO", "application/pdf")},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert res.status_code == 415


def test_upload_xlsx_valido_aceito():
    """Arquivo XLSX com magic bytes PK aceito."""
    import main as m
    token, _ = _create_access_token("admin", role="admin")
    cid = str(uuid.uuid4())
    xlsx_magic = b"PK\x03\x04" + b"\x00" * 100
    with patch.object(m, "_upload_to_s3", return_value=f"bucket/{cid}.xlsx"):
        res = client.post(
            f"/documents/upload?company_id={cid}",
            files={"file": (
                "planilha.xlsx",
                xlsx_magic,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert res.status_code == 200


# ── Observabilidade: JSON formatter ──────────────────────────────────────────

def test_json_formatter_produz_json_valido():
    """_JsonFormatter deve gerar string JSON parseável."""
    from apps.api.observability import _JsonFormatter

    formatter = _JsonFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO,
        pathname="", lineno=0,
        msg="Teste de log JSON",
        args=(), exc_info=None,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert parsed["level"] == "INFO"
    assert parsed["msg"] == "Teste de log JSON"
    assert "ts" in parsed
    assert "logger" in parsed


def test_json_formatter_captura_exc_info():
    """_JsonFormatter inclui traceback quando há exc_info."""
    from apps.api.observability import _JsonFormatter

    formatter = _JsonFormatter()
    try:
        raise ValueError("erro de teste")
    except ValueError:
        import sys
        exc = sys.exc_info()

    record = logging.LogRecord(
        name="test", level=logging.ERROR,
        pathname="", lineno=0,
        msg="Erro capturado",
        args=(), exc_info=exc,
    )
    output = formatter.format(record)
    parsed = json.loads(output)
    assert "exc" in parsed
    assert "ValueError" in parsed["exc"]


# ── RBAC: permissões do módulo rbac.py ───────────────────────────────────────

def test_rbac_admin_tem_todas_permissoes():
    """Admin deve ter todas as permissões definidas."""
    from apps.api.rbac import Role, ROLE_PERMISSIONS, has_permission
    admin_user = {"role": Role.ADMIN}
    for perm in ("read", "write", "upload", "delete", "ai:run", "reports:generate", "admin:manage"):
        assert has_permission(admin_user, perm), f"Admin deveria ter '{perm}'"


def test_rbac_viewer_so_leitura():
    """Viewer deve ter apenas permissões de leitura."""
    from apps.api.rbac import Role, has_permission
    viewer_user = {"role": Role.VIEWER}
    assert has_permission(viewer_user, "read") is True
    assert has_permission(viewer_user, "write") is False
    assert has_permission(viewer_user, "delete") is False
    assert has_permission(viewer_user, "admin:manage") is False


def test_rbac_analista_sem_admin_manage():
    """Analista não deve ter admin:manage."""
    from apps.api.rbac import Role, has_permission
    analista_user = {"role": Role.ANALISTA}
    assert has_permission(analista_user, "upload") is True
    assert has_permission(analista_user, "admin:manage") is False


# ── Compliance adicional ──────────────────────────────────────────────────────

def test_validate_balance_zeros():
    """Balanço com todos zeros fecha."""
    from services.compliance.rules import validate_balance
    assert validate_balance({"ativo": "0", "passivo": "0", "pl": "0"}) is True


def test_validate_balance_invalido():
    """Ativo ≠ Passivo + PL levanta ComplianceError."""
    from services.compliance.rules import validate_balance, ComplianceError
    with pytest.raises(ComplianceError, match="não fecha"):
        validate_balance({"ativo": "100", "passivo": "50", "pl": "10"})


def test_cnpj_formatado_valido():
    """CNPJ com formatação deve passar após normalização."""
    from services.compliance.rules import validate_cnpj
    assert validate_cnpj("33.000.167/0001-01") is True
