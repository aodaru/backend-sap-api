"""
Tests de autenticación - API Key.

Verifica que los endpoints protegidos rechacen peticiones
sin API Key o con API Key inválida, y acepten peticiones válidas.
"""


def test_root_without_api_key_returns_401(client):
    """Test: Endpoint raíz sin API Key retorna 401."""
    response = client.get("/")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "API Key required"


def test_health_without_api_key_returns_401(client):
    """Test: Health check sin API Key retorna 401."""
    response = client.get("/api/health")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "API Key required"


def test_root_with_invalid_api_key_returns_401(client):
    """Test: Endpoint raíz con API Key inválida retorna 401."""
    response = client.get("/", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid API Key"


def test_health_with_invalid_api_key_returns_401(client):
    """Test: Health check con API Key inválida retorna 401."""
    response = client.get("/api/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Invalid API Key"


def test_root_with_valid_api_key_returns_200(client, valid_api_key):
    """Test: Endpoint raíz con API Key válida retorna 200."""
    response = client.get("/", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
    assert "health" in data


def test_health_with_valid_api_key_returns_200(client, valid_api_key):
    """Test: Health check con API Key válida retorna 200."""
    response = client.get("/api/health", headers={"X-API-Key": valid_api_key})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Backend API - Automatización SAP"
    assert "version" in data
    assert "sap_system" in data


def test_docs_accessible_without_api_key(client):
    """Test: Documentación Swagger es accesible sin autenticación."""
    response = client.get("/docs")
    assert response.status_code == 200
