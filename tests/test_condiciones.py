"""
Tests - Condiciones VK12 (Fase 5).

Verifica que los endpoints de condiciones funcionen correctamente,
incluyendo descarga de template, upload, execute y status.
"""

import io
import json

from fastapi.testclient import TestClient

# Credenciales SAP de prueba (mock)
SAP_CREDENTIALS = {
    "system": "ERQ",
    "mandt": "200",
    "username": "test_user",
    "password": "test_pass",
    "language": "ES",
}


def test_template_download(client: TestClient, valid_api_key: str):
    """Test: Template VK12 se descarga correctamente."""
    response = client.get(
        "/api/condiciones/template",
        headers={"X-API-Key": valid_api_key},
    )
    assert response.status_code == 200
    assert (
        response.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


def test_template_requires_api_key(client: TestClient):
    """Test: Template VK12 requiere API Key."""
    response = client.get("/api/condiciones/template")
    assert response.status_code == 401


def test_upload_valid_excel(
    client: TestClient, valid_api_key: str, valid_condiciones_excel: io.BytesIO
):
    """Test: Upload de Excel válido retorna 200 con valid=true."""
    response = client.post(
        "/api/condiciones/upload",
        headers={"X-API-Key": valid_api_key},
        files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["row_count"] == 1
    assert data["filename"] == "test.xlsx"


def test_upload_invalid_missing_columns(
    client: TestClient,
    valid_api_key: str,
    invalid_condiciones_excel_missing_columns: io.BytesIO,
):
    """Test: Upload de Excel inválido (columnas faltantes) retorna errores."""
    response = client.post(
        "/api/condiciones/upload",
        headers={"X-API-Key": valid_api_key},
        files={"file": ("test.xlsx", invalid_condiciones_excel_missing_columns, "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["validations"]) > 0


def test_upload_invalid_bad_flow(
    client: TestClient,
    valid_api_key: str,
    invalid_condiciones_excel_bad_flow: io.BytesIO,
):
    """Test: Upload de Excel con flujo inválido retorna errores."""
    response = client.post(
        "/api/condiciones/upload",
        headers={"X-API-Key": valid_api_key},
        files={"file": ("test.xlsx", invalid_condiciones_excel_bad_flow, "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["validations"]) > 0


def test_upload_invalid_bad_types(
    client: TestClient,
    valid_api_key: str,
    invalid_condiciones_excel_bad_types: io.BytesIO,
):
    """Test: Upload de Excel con tipos incorrectos retorna errores."""
    response = client.post(
        "/api/condiciones/upload",
        headers={"X-API-Key": valid_api_key},
        files={"file": ("test.xlsx", invalid_condiciones_excel_bad_types, "application/octet-stream")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert len(data["validations"]) > 0


def test_upload_requires_api_key(
    client: TestClient, valid_condiciones_excel: io.BytesIO
):
    """Test: Upload VK12 requiere API Key."""
    response = client.post(
        "/api/condiciones/upload",
        files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
    )
    assert response.status_code == 401


def test_upload_invalid_extension(client: TestClient, valid_api_key: str):
    """Test: Upload de archivo no Excel retorna error 422."""
    response = client.post(
        "/api/condiciones/upload",
        headers={"X-API-Key": valid_api_key},
        files={"file": ("test.txt", io.BytesIO(b"not an excel"), "text/plain")},
    )
    assert response.status_code == 422


def test_execute_valid_excel(
    client: TestClient, valid_api_key: str, valid_condiciones_excel: io.BytesIO
):
    """Test: Execute con Excel válido crea job y retorna 202."""
    response = client.post(
        "/api/condiciones/execute",
        headers={"X-API-Key": valid_api_key},
        data={
            "credentials": json.dumps(SAP_CREDENTIALS),
        },
        files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
    )
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "completed"
    assert data["message"] == "VK12 ejecutado exitosamente"


def test_execute_invalid_excel(
    client: TestClient,
    valid_api_key: str,
    invalid_condiciones_excel_missing_columns: io.BytesIO,
):
    """Test: Execute con Excel inválido retorna 400."""
    response = client.post(
        "/api/condiciones/execute",
        headers={"X-API-Key": valid_api_key},
        data={
            "credentials": json.dumps(SAP_CREDENTIALS),
        },
        files={"file": ("test.xlsx", invalid_condiciones_excel_missing_columns, "application/octet-stream")},
    )
    assert response.status_code == 400


def test_execute_requires_api_key(
    client: TestClient, valid_condiciones_excel: io.BytesIO
):
    """Test: Execute VK12 requiere API Key."""
    response = client.post(
        "/api/condiciones/execute",
        data={
            "credentials": json.dumps(SAP_CREDENTIALS),
        },
        files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
    )
    assert response.status_code == 401


def test_status_returns_job(
    client: TestClient, valid_api_key: str, valid_condiciones_excel: io.BytesIO
):
    """Test: Status retorna estado del job VK12."""
    # Primero crear un job ejecutando
    execute_response = client.post(
        "/api/condiciones/execute",
        headers={"X-API-Key": valid_api_key},
        data={
            "credentials": json.dumps(SAP_CREDENTIALS),
        },
        files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
    )
    job_id = execute_response.json()["job_id"]

    # Consultar estado
    response = client.get(
        f"/api/condiciones/status/{job_id}",
        headers={"X-API-Key": valid_api_key},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["progress"] == 100


def test_status_job_not_found(client: TestClient, valid_api_key: str):
    """Test: Status de job inexistente retorna 404."""
    response = client.get(
        "/api/condiciones/status/nonexistent-job-id",
        headers={"X-API-Key": valid_api_key},
    )
    assert response.status_code == 404


def test_status_requires_api_key(client: TestClient):
    """Test: Status VK12 requiere API Key."""
    response = client.get("/api/condiciones/status/some-job-id")
    assert response.status_code == 401
