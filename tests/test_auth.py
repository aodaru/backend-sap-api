"""
Tests de autenticación - API Key.

Verifica que los endpoints protegidos rechacen peticiones
sin API Key o con API Key inválida, y acepten peticiones válidas.

Nota: El endpoint /api/health es público (no requiere API Key).
"""

import pytest


def test_root_without_api_key_returns_401(client):
    """Test: Endpoint raíz sin API Key retorna 401."""
    response = client.get("/")
    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "API Key required"


def test_root_with_invalid_api_key_returns_401(client):
    """Test: Endpoint raíz con API Key inválida retorna 401."""
    response = client.get("/", headers={"X-API-Key": "wrong-key"})
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


def test_health_is_public_no_api_key(client):
    """Test: Health check NO requiere API Key (endpoint público)."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_is_public_invalid_key(client):
    """Test: Health check responde 200 aunque la API Key sea inválida."""
    response = client.get("/api/health", headers={"X-API-Key": "wrong-key"})
    assert response.status_code == 200


def test_docs_accessible_without_api_key(client):
    """Test: Documentación Swagger es accesible sin autenticación."""
    response = client.get("/docs")
    assert response.status_code == 200
