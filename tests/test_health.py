"""
Tests básicos - Health Check y Endpoints generales.

Verifica que los endpoints raíz y de health check respondan correctamente.
"""


def test_root_returns_200(client):
    """Test: Endpoint raíz retorna 200 con información básica."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


def test_health_check_returns_200(client):
    """Test: Health check retorna 200 con estado del sistema."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Backend API - Automatización SAP"
    assert "version" in data
    assert "sap_system" in data


def test_health_check_content_type(client):
    """Test: Health check retorna JSON."""
    response = client.get("/api/health")
    assert response.headers["content-type"] == "application/json"
