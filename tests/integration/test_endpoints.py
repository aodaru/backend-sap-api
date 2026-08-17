"""
Tests de integración adicionales para endpoints.

Verifica casos edge, manejo de errores y autenticación
en todos los endpoints de la API.
"""

import io
import json
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests adicionales para el endpoint raíz."""

    def test_root_returns_api_info(self, client: TestClient, valid_api_key: str):
        """Test: Root retorna información completa de la API."""
        response = client.get("/", headers={"X-API-Key": valid_api_key})
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Backend API - Automatización SAP"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/health"

    def test_root_content_type(self, client: TestClient, valid_api_key: str):
        """Test: Root retorna JSON."""
        response = client.get("/", headers={"X-API-Key": valid_api_key})
        assert response.headers["content-type"] == "application/json"


class TestCostosEdgeCases:
    """Tests de edge cases para endpoints de costos."""

    def test_upload_empty_excel(self, client: TestClient, valid_api_key: str):
        """Test: Upload de Excel sin filas de datos retorna válido con 0 rows."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Costos ME12"
        headers = [
            "Material", "Proveedor", "Org_Compras", "Tipo_Info",
            "Tipo_Condicion", "Nuevo_Precio", "Moneda", "Unidad_Precio",
            "Unidad_Medida", "Valido_Desde", "Valido_Hasta",
        ]
        ws.append(headers)
        # No data rows

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        buffer.name = "empty.xlsx"

        response = client.post(
            "/api/costos/upload",
            headers={"X-API-Key": valid_api_key},
            files={"file": ("empty.xlsx", buffer, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["row_count"] == 0

    def test_execute_requires_file(self, client: TestClient, valid_api_key: str):
        """Test: Execute sin archivo retorna error."""
        response = client.post(
            "/api/costos/execute",
            headers={"X-API-Key": valid_api_key},
            data={
                "credentials": json.dumps(
                    {"system": "PRD", "mandt": "300", "username": "test_user", "password": "test_pass", "language": "ES"}
                )
            },
        )
        assert response.status_code == 422

    def test_template_returns_xlsx_content_type(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Template retorna content-type de Excel."""
        response = client.get(
            "/api/costos/template",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]


class TestCondicionesEdgeCases:
    """Tests de edge cases para endpoints de condiciones."""

    def test_upload_empty_excel(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Upload de Excel sin filas de datos retorna válido."""
        import openpyxl

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "VK12 Condiciones"
        headers = [
            "MATERIAL", "UNIDAD_DE_MEDIDA", "IMPORTE", "GRUPO_ARTICULO",
            "ORG_VENTA", "CAN_DISTR", "SECTOR", "RAMO", "TIPO_MODIFICACION",
        ]
        ws.append(headers)
        # No data rows

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        buffer.name = "empty.xlsx"

        response = client.post(
            "/api/condiciones/upload",
            headers={"X-API-Key": valid_api_key},
            files={"file": ("empty.xlsx", buffer, "application/octet-stream")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["row_count"] == 0

    def test_execute_requires_credentials(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Execute sin credenciales retorna error 422."""
        response = client.post(
            "/api/condiciones/execute",
            headers={"X-API-Key": valid_api_key},
            files={"file": ("test.xlsx", io.BytesIO(b"dummy"), "application/octet-stream")},
        )
        assert response.status_code == 422

    def test_execute_invalid_credentials_format(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Execute con credenciales JSON inválido retorna error."""
        response = client.post(
            "/api/condiciones/execute",
            headers={"X-API-Key": valid_api_key},
            data={"credentials": "not-json"},
            files={"file": ("test.xlsx", io.BytesIO(b"dummy"), "application/octet-stream")},
        )
        assert response.status_code == 422

    def test_execute_missing_required_credential_fields(
        self, client: TestClient, valid_api_key: str, valid_condiciones_excel
    ):
        """Test: Execute con credenciales incompletas retorna error."""
        incomplete_creds = json.dumps({"system": "ERQ"})
        response = client.post(
            "/api/condiciones/execute",
            headers={"X-API-Key": valid_api_key},
            data={"credentials": incomplete_creds},
            files={"file": ("test.xlsx", valid_condiciones_excel, "application/octet-stream")},
        )
        assert response.status_code == 422

    def test_execute_vk12_multipart_contract_without_sap(
        self, client: TestClient, valid_api_key: str, valid_condiciones_excel,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """Test: VK12 acepta file y credentials sin conectar con SAP real."""
        mocked_execute = AsyncMock(return_value={"processed": 1})
        monkeypatch.setattr("routers.condiciones.execute_vk12", mocked_execute)
        credentials = {
            "system": "ERQ",
            "mandt": "300",
            "username": "sap-user",
            "password": "not-a-real-password",
            "language": "ES",
        }

        response = client.post(
            "/api/condiciones/execute",
            headers={"X-API-Key": valid_api_key},
            data={"credentials": json.dumps(credentials)},
            files={
                "file": (
                    "condiciones.xlsx",
                    valid_condiciones_excel,
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert data["job_id"]
        assert data["status"] == "completed"
        mocked_execute.assert_awaited_once()
        assert mocked_execute.await_args.kwargs["credentials"] == credentials

    def test_template_returns_xlsx_content_type(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Template retorna content-type de Excel."""
        response = client.get(
            "/api/condiciones/template",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 200
        assert "spreadsheetml" in response.headers["content-type"]


class TestAuthenticationCoverage:
    """Tests adicionales de autenticación para mejorar cobertura."""

    def test_all_protected_endpoints_require_auth(self, client: TestClient):
        """Test: Todos los endpoints protegidos rechazan sin API Key."""
        protected_endpoints = [
            ("GET", "/"),
            ("GET", "/api/costos/template"),
            ("GET", "/api/condiciones/template"),
            ("GET", "/api/queue/stats"),
            ("GET", "/api/logs"),
        ]
        for method, path in protected_endpoints:
            response = client.request(method, path)
            assert response.status_code == 401, (
                f"{method} {path} debería retornar 401 sin API Key"
            )

    def test_multiple_invalid_keys(self, client: TestClient):
        """Test: Múltiples API keys inválidas siempre retornan 401."""
        invalid_keys = ["wrong-key-1", "wrong-key-2", "12345678"]
        for key in invalid_keys:
            response = client.get("/", headers={"X-API-Key": key})
            assert response.status_code == 401


class TestSwaggerAndRedoc:
    """Tests para verificar que la documentación API funciona."""

    def test_swagger_ui_accessible(self, client: TestClient):
        """Test: Swagger UI es accesible en /docs."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_accessible(self, client: TestClient):
        """Test: ReDoc es accesible en /redoc."""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_json_accessible(self, client: TestClient):
        """Test: OpenAPI JSON es accesible en /openapi.json."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data

    def test_openapi_has_all_endpoints(self, client: TestClient):
        """Test: OpenAPI lista todos los endpoints principales."""
        response = client.get("/openapi.json")
        data = response.json()
        paths = data["paths"]

        expected_paths = [
            "/",
            "/api/health",
            "/api/costos/template",
            "/api/costos/upload",
            "/api/costos/execute",
            "/api/costos/status/{job_id}",
            "/api/condiciones/template",
            "/api/condiciones/upload",
            "/api/condiciones/execute",
            "/api/condiciones/status/{job_id}",
            "/api/queue/stats",
            "/api/queue/status/{job_id}",
            "/api/queue/{job_id}",
            "/api/logs",
            "/api/logs/{job_id}",
        ]
        for path in expected_paths:
            assert path in paths, f"Endpoint {path} no encontrado en OpenAPI"

    def test_openapi_has_tags(self, client: TestClient):
        """Test: OpenAPI tiene tags documentados."""
        response = client.get("/openapi.json")
        data = response.json()
        tags = [t["name"] for t in data.get("info", {}).get("tags", [])]
        # Verificar que hay al menos algunos tags definidos en los endpoints
        all_tags = set()
        for path_data in data["paths"].values():
            for operation in path_data.values():
                if isinstance(operation, dict) and "tags" in operation:
                    all_tags.update(operation["tags"])
        assert len(all_tags) > 0
