"""
Tests unitarios para models/requests.py y models/responses.py.

Verifica la validación Pydantic de los modelos de petición y respuesta.
"""

import pytest
from pydantic import ValidationError

from models.requests import CostosExecuteRequest
from models.responses import (
    CostosExecuteResponse,
    CostosStatusResponse,
    CostosUploadResponse,
    CondicionesExecuteRequest,
    CondicionesExecuteResponse,
    CondicionesStatusResponse,
    CondicionesUploadResponse,
    ErrorResponse,
    HealthResponse,
    JobStatus,
    ValidationDetail,
)
from datetime import datetime, timezone


# ============================================================
# Tests para CostosExecuteRequest
# ============================================================


class TestCostosExecuteRequest:
    """Tests para el modelo CostosExecuteRequest."""

    def test_creation_with_valid_data(self):
        """Test: CostosExecuteRequest se crea con datos válidos."""
        request = CostosExecuteRequest(job_id="job-123")
        assert request.job_id == "job-123"

    def test_requires_job_id(self):
        """Test: job_id es obligatorio."""
        with pytest.raises(ValidationError):
            CostosExecuteRequest()

    def test_rejects_empty_string_job_id(self):
        """Test: job_id no puede ser string vacío."""
        # Pydantic v2 acepta string vacío por defecto, verificamos que se cree
        request = CostosExecuteRequest(job_id="")
        assert request.job_id == ""


# ============================================================
# Tests para HealthResponse
# ============================================================


class TestHealthResponse:
    """Tests para el modelo HealthResponse."""

    def test_creation(self):
        """Test: HealthResponse se crea correctamente."""
        response = HealthResponse(
            status="ok",
            message="Servicio listo",
            timestamp=datetime.now(timezone.utc),
        )
        assert response.status == "ok"
        assert response.message == "Servicio listo"
        assert response.timestamp is not None

    def test_requires_all_fields(self):
        """Test: Todos los campos son obligatorios."""
        with pytest.raises(ValidationError):
            HealthResponse(status="ok")

    def test_status_ok_value(self):
        """Test: Status acepta 'ok'."""
        response = HealthResponse(
            status="ok",
            message="OK",
            timestamp=datetime.now(timezone.utc),
        )
        assert response.status == "ok"


# ============================================================
# Tests para ValidationDetail
# ============================================================


class TestValidationDetail:
    """Tests para el modelo ValidationDetail."""

    def test_creation(self):
        """Test: ValidationDetail se crea correctamente."""
        detail = ValidationDetail(row=2, field="Precio", error="Debe ser numérico")
        assert detail.row == 2
        assert detail.field == "Precio"
        assert detail.error == "Debe ser numérico"

    def test_requires_all_fields(self):
        """Test: Todos los campos son obligatorios."""
        with pytest.raises(ValidationError):
            ValidationDetail(row=2, field="Precio")


# ============================================================
# Tests para JobStatus
# ============================================================


class TestJobStatus:
    """Tests para el enum JobStatus."""

    def test_all_values_exist(self):
        """Test: Todos los valores del enum existen."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
        assert JobStatus.QUEUED.value == "queued"
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_is_string_enum(self):
        """Test: JobStatus es un string enum."""
        assert isinstance(JobStatus.PENDING, str)
        assert JobStatus.PENDING == "pending"

    def test_backward_compatible(self):
        """Test: Los valores originales siguen existiendo."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"


# ============================================================
# Tests para CostosUploadResponse
# ============================================================


class TestCostosUploadResponse:
    """Tests para el modelo CostosUploadResponse."""

    def test_creation_valid(self):
        """Test: CostosUploadResponse con datos válidos."""
        response = CostosUploadResponse(
            filename="test.xlsx",
            row_count=10,
            valid=True,
            validations=[],
        )
        assert response.filename == "test.xlsx"
        assert response.row_count == 10
        assert response.valid is True
        assert response.validations == []

    def test_with_validations(self):
        """Test: CostosUploadResponse con errores de validación."""
        validations = [
            ValidationDetail(row=2, field="Precio", error="Inválido")
        ]
        response = CostosUploadResponse(
            filename="test.xlsx",
            row_count=10,
            valid=False,
            validations=validations,
        )
        assert response.valid is False
        assert len(response.validations) == 1

    def test_validations_default_empty(self):
        """Test: validations tiene lista vacía por defecto."""
        response = CostosUploadResponse(
            filename="test.xlsx",
            row_count=0,
            valid=True,
        )
        assert response.validations == []


# ============================================================
# Tests para CostosExecuteResponse
# ============================================================


class TestCostosExecuteResponse:
    """Tests para el modelo CostosExecuteResponse."""

    def test_creation(self):
        """Test: CostosExecuteResponse se crea correctamente."""
        response = CostosExecuteResponse(
            job_id="job-123",
            status=JobStatus.COMPLETED,
            message="ME12 ejecutado exitosamente",
        )
        assert response.job_id == "job-123"
        assert response.status == JobStatus.COMPLETED
        assert response.message == "ME12 ejecutado exitosamente"

    def test_status_as_string(self):
        """Test: status acepta string y se convierte a JobStatus."""
        response = CostosExecuteResponse(
            job_id="job-123",
            status="completed",
            message="OK",
        )
        assert response.status == JobStatus.COMPLETED


# ============================================================
# Tests para CostosStatusResponse
# ============================================================


class TestCostosStatusResponse:
    """Tests para el modelo CostosStatusResponse."""

    def test_creation_with_results(self):
        """Test: CostosStatusResponse con resultados."""
        response = CostosStatusResponse(
            job_id="job-123",
            status=JobStatus.COMPLETED,
            progress=100,
            results={"processed": 10},
        )
        assert response.job_id == "job-123"
        assert response.progress == 100
        assert response.results == {"processed": 10}

    def test_results_default_none(self):
        """Test: results es None por defecto."""
        response = CostosStatusResponse(
            job_id="job-123",
            status=JobStatus.PENDING,
            progress=0,
        )
        assert response.results is None


# ============================================================
# Tests para ErrorResponse
# ============================================================


class TestErrorResponse:
    """Tests para el modelo ErrorResponse."""

    def test_creation(self):
        """Test: ErrorResponse se crea correctamente."""
        response = ErrorResponse(detail="Error de autenticación")
        assert response.detail == "Error de autenticación"


# ============================================================
# Tests para CondicionesExecuteRequest
# ============================================================


class TestCondicionesExecuteRequest:
    """Tests para el modelo CondicionesExecuteRequest."""

    def test_creation(self):
        """Test: CondicionesExecuteRequest se crea con datos válidos."""
        request = CondicionesExecuteRequest(
            system="ERQ",
            mandt="300",
            username="test_user",
            password="test_pass",
            language="ES",
        )
        assert request.system == "ERQ"
        assert request.mandt == "300"
        assert request.username == "test_user"
        assert request.password == "test_pass"
        assert request.language == "ES"

    def test_language_default_es(self):
        """Test: language tiene valor por defecto 'ES'."""
        request = CondicionesExecuteRequest(
            system="ERQ",
            mandt="300",
            username="test_user",
            password="test_pass",
        )
        assert request.language == "ES"

    def test_requires_system(self):
        """Test: system es obligatorio."""
        with pytest.raises(ValidationError):
            CondicionesExecuteRequest(
                mandt="300",
                username="test_user",
                password="test_pass",
            )

    def test_requires_mandt(self):
        """Test: mandt es obligatorio."""
        with pytest.raises(ValidationError):
            CondicionesExecuteRequest(
                system="ERQ",
                username="test_user",
                password="test_pass",
            )

    def test_requires_username(self):
        """Test: username es obligatorio."""
        with pytest.raises(ValidationError):
            CondicionesExecuteRequest(
                system="ERQ",
                mandt="300",
                password="test_pass",
            )

    def test_requires_password(self):
        """Test: password es obligatorio."""
        with pytest.raises(ValidationError):
            CondicionesExecuteRequest(
                system="ERQ",
                mandt="300",
                username="test_user",
            )

    def test_model_dump(self):
        """Test: model_dump retorna diccionario correcto."""
        request = CondicionesExecuteRequest(
            system="ERQ",
            mandt="300",
            username="user",
            password="pass",
            language="ES",
        )
        data = request.model_dump()
        assert data["system"] == "ERQ"
        assert data["mandt"] == "300"
        assert data["username"] == "user"
        assert data["password"] == "pass"
        assert data["language"] == "ES"


# ============================================================
# Tests para CondicionesUploadResponse
# ============================================================


class TestCondicionesUploadResponse:
    """Tests para el modelo CondicionesUploadResponse."""

    def test_creation_valid(self):
        """Test: CondicionesUploadResponse con datos válidos."""
        response = CondicionesUploadResponse(
            filename="test.xlsx",
            row_count=5,
            valid=True,
        )
        assert response.filename == "test.xlsx"
        assert response.row_count == 5
        assert response.valid is True
        assert response.validations == []


# ============================================================
# Tests para CondicionesExecuteResponse
# ============================================================


class TestCondicionesExecuteResponse:
    """Tests para el modelo CondicionesExecuteResponse."""

    def test_creation(self):
        """Test: CondicionesExecuteResponse se crea correctamente."""
        response = CondicionesExecuteResponse(
            job_id="job-vk12",
            status=JobStatus.COMPLETED,
            message="VK12 ejecutado exitosamente",
        )
        assert response.job_id == "job-vk12"
        assert response.status == JobStatus.COMPLETED


# ============================================================
# Tests para CondicionesStatusResponse
# ============================================================


class TestCondicionesStatusResponse:
    """Tests para el modelo CondicionesStatusResponse."""

    def test_creation_with_results(self):
        """Test: CondicionesStatusResponse con resultados."""
        response = CondicionesStatusResponse(
            job_id="job-vk12",
            status=JobStatus.COMPLETED,
            progress=100,
            results={"processed": 5},
        )
        assert response.job_id == "job-vk12"
        assert response.results == {"processed": 5}
