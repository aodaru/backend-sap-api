"""
Tests - CORS (Fase 9: Integración con Frontends).

Verifica que la configuración CORS permita el consumo desde
frontends Astro y Laravel correctamente.
"""


def test_cors_allows_astro_origin(client):
    """Test: CORS permite origen de Astro (localhost:4321)."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:4321"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_allows_laravel_origin(client):
    """Test: CORS permite origen de Laravel (localhost:8080)."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:8080"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers


def test_cors_preflight_returns_200(client):
    """Test: Preflight OPTIONS retorna 200."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:4321",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200


def test_cors_preflight_allows_get(client):
    """Test: Preflight permite método GET."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:4321",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert "access-control-allow-methods" in response.headers


def test_cors_preflight_allows_post(client):
    """Test: Preflight permite método POST."""
    response = client.options(
        "/api/costos/upload",
        headers={
            "Origin": "http://localhost:4321",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200


def test_cors_preflight_allows_api_key_header(client):
    """Test: Preflight permite header X-API-Key."""
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:4321",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "X-API-Key",
        },
    )
    assert response.status_code == 200


def test_cors_preflight_allows_content_type(client):
    """Test: Preflight permite header Content-Type."""
    response = client.options(
        "/api/costos/upload",
        headers={
            "Origin": "http://localhost:4321",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200


def test_cors_rejects_unknown_origin(client):
    """Test: CORS rechaza origen no configurado."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://malicious-site.com"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_credentials_allowed(client):
    """Test: CORS permite credenciales."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:4321"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_health_endpoint_with_origin(client):
    """Test: Health check funciona con header Origin."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:4321"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_cors_costos_endpoint_with_origin(client, valid_api_key):
    """Test: Endpoint costos funciona con header Origin."""
    response = client.get(
        "/api/costos/template",
        headers={
            "Origin": "http://localhost:4321",
            "X-API-Key": valid_api_key,
        },
    )
    assert response.status_code == 200


def test_cors_condiciones_endpoint_with_origin(client, valid_api_key):
    """Test: Endpoint condiciones funciona con header Origin."""
    response = client.get(
        "/api/condiciones/template",
        headers={
            "Origin": "http://localhost:8080",
            "X-API-Key": valid_api_key,
        },
    )
    assert response.status_code == 200
