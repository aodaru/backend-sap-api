"""
Tests básicos - Health Check y Endpoints generales.

Verifica que los endpoints raíz y de health check respondan correctamente.
Requiere API Key para acceder (autenticación habilitada en Fase 2).
"""


def test_root_returns_200(client, valid_api_key):
    """Test: Endpoint raíz retorna 200 con información básica."""
    response = client.get("/", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


def test_health_check_returns_200(client, valid_api_key):
    """Test: Health check retorna 200 con estado del sistema."""
    response = client.get("/api/health", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Backend API - Automatización SAP"
    assert "version" in data
    assert "sap_system" in data


def test_health_check_content_type(client, valid_api_key):
    """Test: Health check retorna JSON."""
    response = client.get("/api/health", headers={"X-API-Key": valid_api_key})
    assert response.headers["content-type"] == "application/json"
