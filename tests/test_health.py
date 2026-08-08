"""
Tests - Health Check (Fase 3: Endpoint público).

Verifica que el endpoint de health check funcione correctamente
sin requerir autenticación.
"""


def test_health_check_returns_200(client):
    """Test: Health check retorna 200 sin API Key."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_no_requires_api_key(client):
    """Test: Health check NO requiere API Key."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_check_has_required_fields(client):
    """Test: Respuesta tiene campos status, message, timestamp."""
    response = client.get("/api/health")
    data = response.json()
    assert "status" in data
    assert "message" in data
    assert "timestamp" in data


def test_health_check_status_is_ok(client):
    """Test: Status es 'ok'."""
    response = client.get("/api/health")
    data = response.json()
    assert data["status"] == "ok"


def test_health_check_message_descriptive(client):
    """Test: Message es descriptivo."""
    response = client.get("/api/health")
    data = response.json()
    assert len(data["message"]) > 0


def test_health_check_content_type(client):
    """Test: Respuesta es JSON."""
    response = client.get("/api/health")
    assert response.headers["content-type"] == "application/json"
