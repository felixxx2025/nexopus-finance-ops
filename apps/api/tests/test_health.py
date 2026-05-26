"""
Testes de infraestrutura — health check e metadados da API.
"""
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    """GET /health deve retornar status ok."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "nexopus-finance-api"


def test_health_returns_version():
    """GET /health deve incluir campo version."""
    res = client.get("/health")
    assert "version" in res.json()


def test_docs_available():
    """Swagger UI deve estar acessível em /docs."""
    res = client.get("/docs")
    assert res.status_code == 200


def test_openapi_schema():
    """OpenAPI schema deve estar disponível em /openapi.json."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()
    assert schema["info"]["title"] == "Nexopus Finance Ops — API"
