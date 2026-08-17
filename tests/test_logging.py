"""
Tests de Logging y Auditoría.

Verifica que el sistema de logs estructurado funcione correctamente:
- Escritura de logs de ejecución, autenticación y upload
- Limpieza de logs antiguos
- Consulta con filtros y paginación
- Endpoints de consulta con autenticación

Nota: Todos los tests mockean SAP (nunca tocan SAP real).
"""

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from main import app
from models.log_models import (
    AuditLogEntry,
    ErrorDetail,
    LogQueryParams,
    LogResponse,
    LogLevel,
    LogStatus,
)
from services.logging_service import AuditLogger


# --- Fixtures ---


@pytest.fixture
def temp_log_dir() -> Generator[Path, None, None]:
    """
    Fixture que crea un directorio temporal para logs de test.

    Se limpia automáticamente al finalizar cada test.
    """
    temp_dir = Path(tempfile.mkdtemp(prefix="test_logs_"))
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def audit_logger_instance(temp_log_dir: Path) -> AuditLogger:
    """
    Fixture que retorna una instancia de AuditLogger con directorio temporal.

    Returns:
        AuditLogger: Instancia configurada para tests.
    """
    return AuditLogger(log_dir=str(temp_log_dir), retention_days=90)


@pytest.fixture
def client() -> TestClient:
    """
    Fixture que retorna un cliente de prueba FastAPI.

    Returns:
        TestClient: Cliente HTTP para hacer requests contra la app.
    """
    return TestClient(app)


@pytest.fixture
def valid_api_key() -> str:
    """
    Fixture que retorna una API key válida para tests.

    Returns:
        str: API key de prueba.
    """
    return "mi-api-key-secreta"


# --- Tests Unitarios: AuditLogger ---


class TestLogExecution:
    """Tests para AuditLogger.log_execution()."""

    def test_log_execution_writes_json(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: log_execution() crea archivo JSON válido con todos los campos.

        Verifica que se escriba un archivo de log con formato JSON
        y que contenga todos los campos requeridos.
        """
        # Arrange
        errors = [
            {
                "row": 2,
                "material": "MAT001",
                "proveedor": "PROV001",
                "message": "Error de precio",
            }
        ]
        metadata = {"filename": "test.xlsx", "org_compras": "1000"}

        # Act
        audit_logger_instance.log_execution(
            job_id="job-123",
            user_id="test_user",
            transaction="ME12",
            status="success",
            duration=1.234,
            sap_login_success=True,
            rows_total=10,
            rows_success=9,
            rows_failed=1,
            errors=errors,
            metadata=metadata,
        )

        # Assert
        log_files = list(temp_log_dir.glob("audit-*.json"))
        assert len(log_files) == 1

        with open(log_files[0], "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
            assert len(lines) == 1

            entry = json.loads(lines[0])
            assert entry["event_type"] == "execution"
            assert entry["user_id"] == "test_user"
            assert entry["transaction"] == "ME12"
            assert entry["job_id"] == "job-123"
            assert entry["status"] == "success"
            assert entry["duration_seconds"] == 1.234
            assert entry["sap_login_success"] is True
            assert entry["rows_total"] == 10
            assert entry["rows_success"] == 9
            assert entry["rows_failed"] == 1
            assert entry["metadata"]["filename"] == "test.xlsx"

    def test_log_execution_error_fields(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Campo errors contiene row, material, proveedor, message.

        Verifica que los errores se serialicen correctamente en el log.
        """
        # Arrange
        errors = [
            {
                "row": 5,
                "material": "MAT999",
                "proveedor": "PROV999",
                "message": "Material no encontrado",
            },
            {
                "row": 8,
                "material": "MAT888",
                "proveedor": "N/A",
                "message": "Precio inválido",
            },
        ]

        # Act
        audit_logger_instance.log_execution(
            job_id="job-456",
            user_id="user2",
            transaction="VK12",
            status="error",
            duration=0.5,
            sap_login_success=True,
            rows_total=2,
            rows_success=0,
            rows_failed=2,
            errors=errors,
        )

        # Assert
        log_files = list(temp_log_dir.glob("audit-*.json"))
        with open(log_files[0], "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert len(entry["errors"]) == 2

            err1 = entry["errors"][0]
            assert err1["row"] == 5
            assert err1["material"] == "MAT999"
            assert err1["proveedor"] == "PROV999"
            assert err1["message"] == "Material no encontrado"

            err2 = entry["errors"][1]
            assert err2["row"] == 8
            assert err2["material"] == "MAT888"
            assert err2["proveedor"] == "N/A"


class TestLogAuth:
    """Tests para AuditLogger.log_auth()."""

    def test_log_auth_success(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: log_auth() registra intento exitoso.

        Verifica que se escriba un log con nivel AUDIT y estado success.
        """
        # Act
        audit_logger_instance.log_auth(
            user_id="admin",
            success=True,
            ip_address="192.168.1.100",
            message="Autenticación exitosa",
        )

        # Assert
        log_files = list(temp_log_dir.glob("audit-*.json"))
        assert len(log_files) == 1

        with open(log_files[0], "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert entry["event_type"] == "auth"
            assert entry["user_id"] == "admin"
            assert entry["status"] == "success"
            assert entry["ip_address"] == "192.168.1.100"
            assert entry["level"] == "audit"

    def test_log_auth_failure(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: log_auth() registra intento fallido.

        Verifica que se escriba un log con nivel ERROR y estado error.
        """
        # Act
        audit_logger_instance.log_auth(
            user_id="unknown",
            success=False,
            ip_address="10.0.0.1",
            message="API Key inválida",
        )

        # Assert
        log_files = list(temp_log_dir.glob("audit-*.json"))
        with open(log_files[0], "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert entry["event_type"] == "auth"
            assert entry["status"] == "error"
            assert entry["level"] == "error"


class TestLogUpload:
    """Tests para AuditLogger.log_upload()."""

    def test_log_upload(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: log_upload() registra upload con resultado.

        Verifica que se escriba un log con los datos del archivo.
        """
        # Arrange
        validations = [
            {"row": 3, "field": "Precio", "error": "Debe ser numérico"}
        ]

        # Act
        audit_logger_instance.log_upload(
            user_id="user1",
            filename="data.xlsx",
            row_count=10,
            valid=False,
            validations=validations,
        )

        # Assert
        log_files = list(temp_log_dir.glob("audit-*.json"))
        with open(log_files[0], "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert entry["event_type"] == "upload"
            assert entry["user_id"] == "user1"
            assert entry["status"] == "error"
            assert entry["rows_total"] == 10
            assert entry["metadata"]["filename"] == "data.xlsx"
            assert entry["metadata"]["valid"] is False
            assert len(entry["metadata"]["validations"]) == 1


class TestSizeBasedSegmentation:
    """Tests para segmentación por tamaño de archivo."""

    def test_creates_new_segment_when_file_exceeds_max_size(
        self, temp_log_dir: Path
    ) -> None:
        """
        Test: Cuando el archivo supera max_file_size_mb, crea un nuevo segmento.

        Crea un logger con tamaño máximo de 1KB para facilitar el test,
        escribe suficientes datos para superar el límite, y verifica
        que se cree un segundo archivo de segmento.
        """
        # Arrange - Logger con tamaño máximo de 1KB para el test
        logger = AuditLogger(
            log_dir=str(temp_log_dir),
            retention_days=90,
            max_file_size_mb=0.001,  # 1 KB
        )

        # Act - Escribir suficientes datos para superar 1KB
        for i in range(100):
            logger.log_execution(
                job_id=f"job-{i}",
                user_id=f"user-{i}",
                transaction="ME12",
                status="success",
                duration=1.0,
                sap_login_success=True,
                rows_total=10,
                rows_success=10,
                rows_failed=0,
                metadata={"iteration": i},
            )

        # Assert - Debe existir al menos 2 archivos (segmento 0 y segmento 1)
        log_files = list(temp_log_dir.glob("audit-*.json"))
        assert len(log_files) >= 2, f"Se esperaban al menos 2 archivos, se encontraron {len(log_files)}: {[f.name for f in log_files]}"

        # Verificar que el primer archivo tiene contenido
        segment_0 = temp_log_dir / f"audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.json"
        assert segment_0.exists()
        assert segment_0.stat().st_size > 0

        # Verificar que existe al menos un segmento adicional
        segment_1 = temp_log_dir / f"audit-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.1.json"
        assert segment_1.exists(), f"Se esperaba segmento 1, archivos: {[f.name for f in log_files]}"
        assert segment_1.stat().st_size > 0

    def test_daily_rotation_creates_new_date_file(
        self, temp_log_dir: Path
    ) -> None:
        """
        Test: Al cambiar la fecha, se crea un nuevo archivo.

        Crea un archivo con fecha de "ayer" manualmente y luego escribe
        con el logger (fecha "hoy"), verificando que se crean archivos
        separados y que ambos son legibles.
        """
        # Arrange - Crear archivo de "ayer" manualmente
        yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        yesterday_file = temp_log_dir / f"audit-{yesterday}.json"
        yesterday_entry = json.dumps({
            "timestamp": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "level": "audit",
            "event_type": "execution",
            "user_id": "user1",
            "transaction": "ME12",
            "job_id": "old-job",
            "status": "success",
            "duration_seconds": 1.0,
            "sap_login_success": True,
            "rows_total": 5,
            "rows_success": 5,
            "rows_failed": 0,
            "errors": [],
            "metadata": {},
        }) + "\n"
        yesterday_file.write_text(yesterday_entry, encoding="utf-8")
        # Ajustar mtime para que parezca de hace 1 día
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        os.utime(yesterday_file, (old_timestamp, old_timestamp))

        # Act - Logger escribe en "hoy"
        logger = AuditLogger(
            log_dir=str(temp_log_dir),
            retention_days=90,
        )
        logger.log_execution(
            job_id="new-job",
            user_id="user2",
            transaction="VK12",
            status="success",
            duration=2.0,
            sap_login_success=True,
            rows_total=3,
            rows_success=3,
            rows_failed=0,
        )

        # Assert - Deben existir 2 archivos (ayer y hoy)
        log_files = list(temp_log_dir.glob("audit-*.json"))
        assert len(log_files) == 2

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        today_file = temp_log_dir / f"audit-{today_str}.json"
        assert yesterday_file.exists()
        assert today_file.exists()

        # Verificar que el archivo de hoy tiene el log correcto
        with open(today_file, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert entry["job_id"] == "new-job"
            assert entry["user_id"] == "user2"

        # Verificar que el archivo de ayer tiene el log correcto
        with open(yesterday_file, "r", encoding="utf-8") as f:
            entry = json.loads(f.readline().strip())
            assert entry["job_id"] == "old-job"
            assert entry["user_id"] == "user1"

        logger._close_current_file()

    def test_reads_from_segmented_files(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: get_logs y get_logs_by_job_id leen de archivos segmentados.

        Crea archivos con formato de segmento manualmente y verifica
        que se puedan leer correctamente.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Crear archivos segmentados manualmente
        segment_0 = temp_log_dir / f"audit-{today}.json"
        segment_1 = temp_log_dir / f"audit-{today}.1.json"

        entry_0 = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "audit",
            "event_type": "execution",
            "user_id": "user1",
            "transaction": "ME12",
            "job_id": "job-seg0",
            "status": "success",
            "duration_seconds": 1.0,
            "sap_login_success": True,
            "rows_total": 5,
            "rows_success": 5,
            "rows_failed": 0,
            "errors": [],
            "metadata": {},
        }) + "\n"

        entry_1 = json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "audit",
            "event_type": "execution",
            "user_id": "user2",
            "transaction": "VK12",
            "job_id": "job-seg1",
            "status": "success",
            "duration_seconds": 2.0,
            "sap_login_success": True,
            "rows_total": 3,
            "rows_success": 3,
            "rows_failed": 0,
            "errors": [],
            "metadata": {},
        }) + "\n"

        segment_0.write_text(entry_0, encoding="utf-8")
        segment_1.write_text(entry_1, encoding="utf-8")

        # Act - get_logs debe encontrar ambos
        filters = LogQueryParams()
        result = audit_logger_instance.get_logs(filters)
        assert result.total == 2

        # Act - get_logs_by_job_id debe encontrar el del segmento 1
        logs = audit_logger_instance.get_logs_by_job_id("job-seg1")
        assert len(logs) == 1
        assert logs[0].job_id == "job-seg1"

    def test_cleanup_removes_segmented_files(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: cleanup_old_logs() elimina archivos segmentados antiguos.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).strftime("%Y-%m-%d")

        # Crear archivos antiguos (segmento 0 y 1)
        old_seg0 = temp_log_dir / f"audit-{old_date}.json"
        old_seg1 = temp_log_dir / f"audit-{old_date}.1.json"
        old_seg0.write_text('{"test": "old0"}\n', encoding="utf-8")
        old_seg1.write_text('{"test": "old1"}\n', encoding="utf-8")

        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=100)).timestamp()
        os.utime(old_seg0, (old_timestamp, old_timestamp))
        os.utime(old_seg1, (old_timestamp, old_timestamp))

        # Crear archivo reciente
        recent_file = temp_log_dir / f"audit-{today}.json"
        recent_file.write_text('{"test": "recent"}\n', encoding="utf-8")

        # Act
        removed = audit_logger_instance.cleanup_old_logs()

        # Assert
        assert removed == 2
        assert not old_seg0.exists()
        assert not old_seg1.exists()
        assert recent_file.exists()


class TestCleanupOldLogs:
    """Tests para AuditLogger.cleanup_old_logs()."""

    def test_cleanup_old_logs(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: cleanup_old_logs() elimina archivos > retention_days.

        Crea archivos fake con fechas antiguas y verifica que se eliminen.
        """
        # Arrange - Crear archivos con fechas antiguas
        old_date = (datetime.now(timezone.utc) - timedelta(days=100)).strftime("%Y-%m-%d")
        old_file = temp_log_dir / f"audit-{old_date}.json"
        old_file.write_text('{"test": "old"}\n', encoding="utf-8")
        # Modificar mtime para que parezca un archivo de hace 100 días
        old_timestamp = (datetime.now(timezone.utc) - timedelta(days=100)).timestamp()
        os.utime(old_file, (old_timestamp, old_timestamp))

        recent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        recent_file = temp_log_dir / f"audit-{recent_date}.json"
        recent_file.write_text('{"test": "recent"}\n', encoding="utf-8")

        # Act
        removed = audit_logger_instance.cleanup_old_logs()

        # Assert
        assert removed == 1
        assert not old_file.exists()
        assert recent_file.exists()

    def test_cleanup_keeps_recent(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: cleanup_old_logs() NO elimina archivos recientes.

        Verifica que los archivos de hoy se mantengan.
        """
        # Arrange - Crear archivo reciente
        recent_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        recent_file = temp_log_dir / f"audit-{recent_date}.json"
        recent_file.write_text('{"test": "recent"}\n', encoding="utf-8")

        # Act
        removed = audit_logger_instance.cleanup_old_logs()

        # Assert
        assert removed == 0
        assert recent_file.exists()


class TestGetLogs:
    """Tests para AuditLogger.get_logs() y get_logs_by_job_id()."""

    def test_get_logs_filters_by_transaction(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Filtrado por tipo de transacción.

        Verifica que solo se retornen logs del tipo solicitado.
        """
        # Arrange - Crear logs de diferentes transacciones
        audit_logger_instance.log_execution(
            job_id="job-1",
            user_id="user1",
            transaction="ME12",
            status="success",
            duration=1.0,
            sap_login_success=True,
            rows_total=5,
            rows_success=5,
            rows_failed=0,
        )
        audit_logger_instance.log_execution(
            job_id="job-2",
            user_id="user2",
            transaction="VK12",
            status="success",
            duration=2.0,
            sap_login_success=True,
            rows_total=3,
            rows_success=3,
            rows_failed=0,
        )

        # Act
        filters = LogQueryParams(transaction="ME12")
        result = audit_logger_instance.get_logs(filters)

        # Assert
        assert result.total == 1
        assert result.logs[0].transaction == "ME12"

    def test_get_logs_filters_by_user(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Filtrado por usuario.

        Verifica que solo se retornen logs del usuario solicitado.
        """
        # Arrange
        audit_logger_instance.log_execution(
            job_id="job-1",
            user_id="alice",
            transaction="ME12",
            status="success",
            duration=1.0,
            sap_login_success=True,
            rows_total=5,
            rows_success=5,
            rows_failed=0,
        )
        audit_logger_instance.log_execution(
            job_id="job-2",
            user_id="bob",
            transaction="ME12",
            status="success",
            duration=2.0,
            sap_login_success=True,
            rows_total=3,
            rows_success=3,
            rows_failed=0,
        )

        # Act
        filters = LogQueryParams(user_id="alice")
        result = audit_logger_instance.get_logs(filters)

        # Assert
        assert result.total == 1
        assert result.logs[0].user_id == "alice"

    def test_get_logs_filters_by_date(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Filtrado por rango de fechas.

        Verifica que se respeten los filtros date_from y date_to.
        """
        # Arrange - Crear log hoy
        audit_logger_instance.log_execution(
            job_id="job-today",
            user_id="user1",
            transaction="ME12",
            status="success",
            duration=1.0,
            sap_login_success=True,
            rows_total=5,
            rows_success=5,
            rows_failed=0,
        )

        # Act - Filtrar por fecha de mañana (no debería encontrar nada)
        tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
        filters = LogQueryParams(date_from=tomorrow)
        result = audit_logger_instance.get_logs(filters)

        # Assert
        assert result.total == 0

    def test_get_logs_by_job_id(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Retorna logs de una ejecución específica.

        Verifica que se retornen solo los logs del job_id solicitado.
        """
        # Arrange
        audit_logger_instance.log_execution(
            job_id="target-job",
            user_id="user1",
            transaction="ME12",
            status="success",
            duration=1.0,
            sap_login_success=True,
            rows_total=5,
            rows_success=5,
            rows_failed=0,
        )
        audit_logger_instance.log_execution(
            job_id="other-job",
            user_id="user2",
            transaction="VK12",
            status="success",
            duration=2.0,
            sap_login_success=True,
            rows_total=3,
            rows_success=3,
            rows_failed=0,
        )

        # Act
        logs = audit_logger_instance.get_logs_by_job_id("target-job")

        # Assert
        assert len(logs) == 1
        assert logs[0].job_id == "target-job"

    def test_get_logs_by_job_id_not_found(
        self, audit_logger_instance: AuditLogger, temp_log_dir: Path
    ) -> None:
        """
        Test: Retorna lista vacía para job inexistente.

        Verifica que no se lance excepción y se retorne lista vacía.
        """
        # Act
        logs = audit_logger_instance.get_logs_by_job_id("nonexistent-job")

        # Assert
        assert logs == []


# --- Tests de Integración: Endpoints ---


class TestLogsEndpoint:
    """Tests de integración para los endpoints de logs."""

    def test_endpoint_get_logs_requires_auth(self, client: TestClient) -> None:
        """
        Test: GET /api/logs retorna 401 sin API key.

        Verifica que el endpoint esté protegido.
        """
        response = client.get("/api/logs")
        assert response.status_code == 401

    def test_endpoint_get_logs_returns_200(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """
        Test: GET /api/logs retorna 200 con estructura paginada.

        Verifica la estructura de la respuesta.
        """
        response = client.get(
            "/api/logs",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 200

        data = response.json()
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_endpoint_get_logs_by_job_id(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """
        Test: GET /api/logs/{job_id} retorna 200 o 404.

        Verifica que el endpoint responda correctamente.
        """
        # Buscar un job inexistente (debería retornar 404)
        response = client.get(
            "/api/logs/nonexistent-job-id",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 404


class TestExecutionGeneratesLog:
    """Tests de integración: ejecución genera log."""

    def test_execute_generates_log(
        self, client: TestClient, valid_api_key: str
    ) -> None:
        """
        Test: Después de POST /api/costos/execute, existe log entry.

        Verifica que la ejecución de una transacción genere un log.
        """
        import io
        import openpyxl

        # Crear Excel válido
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Costos ME12"
        headers = [
            "Material", "Proveedor", "Org_Compras", "Tipo_Info",
            "Tipo_Condicion", "Nuevo_Precio", "Moneda", "Unidad_Precio",
            "Unidad_Medida", "Valido_Desde", "Valido_Hasta",
        ]
        ws.append(headers)
        ws.append([
            "MAT001", "PROV001", "1000", "0", "PB00",
            100.50, "MXN", "ST", "ST", "20260101", "20261231",
        ])

        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        buffer.name = "test_execute.xlsx"

        # Ejecutar
        response = client.post(
            "/api/costos/execute",
            headers={"X-API-Key": valid_api_key},
            data={
                "credentials": json.dumps(
                    {"system": "PRD", "mandt": "300", "username": "test_user", "password": "test_pass", "language": "ES"}
                )
            },
            files={"file": ("test_execute.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )

        # Verificar que se ejecutó (puede ser 202 o error de cola)
        assert response.status_code in (202, 429)

        # Verificar que se creó un archivo de log
        from config import get_settings
        settings = get_settings()
        log_dir = Path(settings.log_dir)
        log_files = list(log_dir.glob("audit-*.json"))
        assert len(log_files) > 0


class TestLogModels:
    """Tests para los modelos Pydantic de log."""

    def test_error_detail_model(self) -> None:
        """Test: ErrorDetail se crea correctamente."""
        error = ErrorDetail(
            row=5,
            material="MAT001",
            proveedor="PROV001",
            message="Error test",
        )
        assert error.row == 5
        assert error.material == "MAT001"
        assert error.proveedor == "PROV001"
        assert error.message == "Error test"

    def test_audit_log_entry_model(self) -> None:
        """Test: AuditLogEntry se crea correctamente."""
        entry = AuditLogEntry(
            timestamp="2026-08-11T10:00:00+00:00",
            level=LogLevel.AUDIT,
            event_type="execution",
            user_id="test_user",
            transaction="ME12",
            job_id="job-123",
            status=LogStatus.SUCCESS,
            duration_seconds=1.5,
            sap_login_success=True,
            rows_total=10,
            rows_success=10,
            rows_failed=0,
        )
        assert entry.event_type == "execution"
        assert entry.transaction == "ME12"
        assert entry.duration_seconds == 1.5

    def test_log_query_params_defaults(self) -> None:
        """Test: LogQueryParams tiene valores por defecto correctos."""
        params = LogQueryParams()
        assert params.limit == 50
        assert params.offset == 0
        assert params.transaction is None
        assert params.user_id is None

    def test_log_response_model(self) -> None:
        """Test: LogResponse se crea correctamente."""
        response = LogResponse(
            total=100,
            limit=50,
            offset=0,
            logs=[],
        )
        assert response.total == 100
        assert response.limit == 50
        assert response.logs == []
