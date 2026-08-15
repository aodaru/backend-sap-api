"""
Tests - Sistema de Cola de Peticiones (Fase 6).

Verifica el correcto funcionamiento de:
- Modelos de datos de la cola
- Servicio de cola (enqueue, dequeue, cancel, stats)
- Endpoints de la cola
- Integración con servicios existentes (ME12, VK12)
"""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from models.queue_models import (
    QueueJobStatus,
    QueueRequest,
    QueueStats,
    QueueStatus,
)
from services.queue_service import RequestQueue, request_queue


def _clear_queue_sync() -> None:
    """Limpia la cola global de forma síncrona (para tests síncronos)."""
    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(request_queue.clear())
    finally:
        loop.close()


# ============================================================
# Tests de Modelos de Datos
# ============================================================


class TestQueueJobStatus:
    """Tests para el enum QueueJobStatus."""

    def test_queue_status_values(self):
        """Verifica que los valores del enum son correctos."""
        assert QueueJobStatus.QUEUED.value == "queued"
        assert QueueJobStatus.PROCESSING.value == "processing"
        assert QueueJobStatus.COMPLETED.value == "completed"
        assert QueueJobStatus.FAILED.value == "failed"
        assert QueueJobStatus.CANCELLED.value == "cancelled"

    def test_queue_status_is_string(self):
        """Verifica que QueueJobStatus es un str enum."""
        assert isinstance(QueueJobStatus.QUEUED, str)
        assert QueueJobStatus.QUEUED == "queued"


class TestQueueModels:
    """Tests para los modelos Pydantic de la cola."""

    def test_queue_request_creation(self):
        """Verifica que QueueRequest se crea correctamente."""
        request = QueueRequest(
            job_id="test-123",
            transaction="ME12",
            status=QueueJobStatus.QUEUED,
            position=1,
            user_id="test_user",
        )
        assert request.job_id == "test-123"
        assert request.transaction == "ME12"
        assert request.status == QueueJobStatus.QUEUED
        assert request.position == 1
        assert request.user_id == "test_user"
        assert request.error_message is None

    def test_queue_request_defaults(self):
        """Verifica valores por defecto de QueueRequest."""
        request = QueueRequest(
            job_id="test-456",
            transaction="VK12",
            status=QueueJobStatus.QUEUED,
        )
        assert request.position == 0
        assert request.user_id == "system"
        assert request.error_message is None
        assert request.started_at is None
        assert request.completed_at is None

    def test_queue_status_creation(self):
        """Verifica que QueueStatus se crea correctamente."""
        status = QueueStatus(
            job_id="test-789",
            position=2,
            estimated_wait=240,
            status=QueueJobStatus.QUEUED,
        )
        assert status.job_id == "test-789"
        assert status.position == 2
        assert status.estimated_wait == 240
        assert status.status == QueueJobStatus.QUEUED

    def test_queue_stats_creation(self):
        """Verifica que QueueStats se crea correctamente."""
        stats = QueueStats(
            total_queued=3,
            total_processing=1,
            total_completed=10,
            total_failed=2,
            total_cancelled=1,
            max_queue_size=5,
        )
        assert stats.total_queued == 3
        assert stats.total_processing == 1
        assert stats.total_completed == 10
        assert stats.total_failed == 2
        assert stats.total_cancelled == 1
        assert stats.max_queue_size == 5

    def test_queue_stats_defaults(self):
        """Verifica valores por defecto de QueueStats."""
        stats = QueueStats()
        assert stats.total_queued == 0
        assert stats.total_processing == 0
        assert stats.total_completed == 0
        assert stats.total_failed == 0
        assert stats.total_cancelled == 0
        assert stats.max_queue_size == 5


# ============================================================
# Tests del Servicio de Cola
# ============================================================


class TestRequestQueue:
    """Tests para la clase RequestQueue."""

    @pytest.fixture
    def queue(self):
        """Fixture que retorna una cola vacía para tests."""
        q = RequestQueue(max_size=3)
        return q

    @pytest.mark.asyncio
    async def test_enqueue_adds_to_queue(self, queue):
        """Verifica que enqueue añade una petición a la cola."""
        await queue.clear()
        position = await queue.enqueue("job-1", "ME12", "user1")
        assert position == 1

        stats = await queue.get_stats()
        assert stats.total_queued == 1

    @pytest.mark.asyncio
    async def test_enqueue_multiple(self, queue):
        """Verifica que enqueue funciona con múltiples peticiones."""
        await queue.clear()
        pos1 = await queue.enqueue("job-1", "ME12", "user1")
        pos2 = await queue.enqueue("job-2", "VK12", "user2")
        pos3 = await queue.enqueue("job-3", "ME12", "user3")

        assert pos1 == 1
        assert pos2 == 2
        assert pos3 == 3

        stats = await queue.get_stats()
        assert stats.total_queued == 3

    @pytest.mark.asyncio
    async def test_enqueue_full_queue_raises(self, queue):
        """Verifica que enqueue lanza error cuando la cola está llena."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")
        await queue.enqueue("job-3", "ME12", "user3")

        with pytest.raises(ValueError, match="Cola llena"):
            await queue.enqueue("job-4", "VK12", "user4")

    @pytest.mark.asyncio
    async def test_dequeue_returns_first(self, queue):
        """Verifica que dequeue retorna la primera petición de la cola."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")

        request = await queue.dequeue()
        assert request is not None
        assert request.job_id == "job-1"
        assert request.status == QueueJobStatus.PROCESSING
        assert request.position == 0

    @pytest.mark.asyncio
    async def test_dequeue_empty_returns_none(self, queue):
        """Verifica que dequeue retorna None en cola vacía."""
        await queue.clear()
        request = await queue.dequeue()
        assert request is None

    @pytest.mark.asyncio
    async def test_dequeue_updates_positions(self, queue):
        """Verifica que dequeue actualiza las posiciones restantes."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")
        await queue.enqueue("job-3", "ME12", "user3")

        await queue.dequeue()

        status = await queue.get_status("job-2")
        assert status is not None
        assert status.position == 1

        status = await queue.get_status("job-3")
        assert status is not None
        assert status.position == 2

    @pytest.mark.asyncio
    async def test_cancel_queued_request(self, queue):
        """Verifica que cancel funciona para peticiones en estado QUEUED."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")

        result = await queue.cancel("job-1")
        assert result is True

        stats = await queue.get_stats()
        assert stats.total_queued == 1
        assert stats.total_cancelled == 1

    @pytest.mark.asyncio
    async def test_cancel_processing_fails(self, queue):
        """Verifica que cancel falla para peticiones en estado PROCESSING."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.dequeue()  # Cambia a PROCESSING

        result = await queue.cancel("job-1")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_raises(self, queue):
        """Verifica que cancel lanza KeyError para petición inexistente."""
        await queue.clear()
        with pytest.raises(KeyError):
            await queue.cancel("nonexistent-job")

    @pytest.mark.asyncio
    async def test_get_status_queued(self, queue):
        """Verifica get_status para petición en cola."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")

        status = await queue.get_status("job-1")
        assert status is not None
        assert status.job_id == "job-1"
        assert status.position == 1
        assert status.status == QueueJobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_status_nonexistent(self, queue):
        """Verifica get_status retorna None para petición inexistente."""
        await queue.clear()
        status = await queue.get_status("nonexistent-job")
        assert status is None

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, queue):
        """Verifica get_stats con cola vacía."""
        await queue.clear()
        stats = await queue.get_stats()
        assert stats.total_queued == 0
        assert stats.total_processing == 0
        assert stats.total_completed == 0
        assert stats.total_failed == 0
        assert stats.total_cancelled == 0

    @pytest.mark.asyncio
    async def test_get_stats_mixed(self, queue):
        """Verifica get_stats con diferentes estados."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")
        await queue.enqueue("job-3", "ME12", "user3")

        await queue.dequeue()  # job-1 -> PROCESSING
        await queue.cancel("job-3")  # job-3 -> CANCELLED

        await queue.mark_completed("job-2")  # job-2 -> COMPLETED

        stats = await queue.get_stats()
        assert stats.total_queued == 0  # job-2 ya no está en cola
        assert stats.total_processing == 1  # job-1
        assert stats.total_cancelled == 1  # job-3
        assert stats.total_completed == 1  # job-2

    @pytest.mark.asyncio
    async def test_mark_completed(self, queue):
        """Verifica que mark_completed actualiza el estado."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.mark_completed("job-1")

        stats = await queue.get_stats()
        assert stats.total_completed == 1
        assert stats.total_queued == 0

    @pytest.mark.asyncio
    async def test_mark_failed(self, queue):
        """Verifica que mark_failed actualiza el estado."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.mark_failed("job-1", "Error de conexión")

        stats = await queue.get_stats()
        assert stats.total_failed == 1
        assert stats.total_queued == 0

    @pytest.mark.asyncio
    async def test_clear(self, queue):
        """Verifica que clear limpia la cola."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")
        await queue.enqueue("job-2", "VK12", "user2")

        await queue.clear()

        stats = await queue.get_stats()
        assert stats.total_queued == 0


# ============================================================
# Tests de Endpoints de la Cola
# ============================================================


class TestQueueEndpoints:
    """Tests para los endpoints de la cola de peticiones."""

    @pytest.fixture(autouse=True)
    def _clear_global_queue(self):
        """Fixture autouse que limpia la cola global antes de cada test."""
        _clear_queue_sync()
        yield
        _clear_queue_sync()

    def test_queue_stats_requires_api_key(self, client: TestClient):
        """Test: Stats de cola requiere API Key."""
        response = client.get("/api/queue/stats")
        assert response.status_code == 401

    def test_queue_stats_empty(self, client: TestClient, valid_api_key: str):
        """Test: Stats de cola vacía retorna ceros."""
        response = client.get(
            "/api/queue/stats",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_queued"] == 0
        assert data["total_processing"] == 0
        assert data["total_completed"] == 0
        assert data["max_queue_size"] == 5

    def test_queue_status_nonexistent(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Status de petición inexistente retorna 404."""
        response = client.get(
            "/api/queue/status/nonexistent-job",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 404

    def test_queue_status_requires_api_key(self, client: TestClient):
        """Test: Status de cola requiere API Key."""
        response = client.get("/api/queue/status/some-job-id")
        assert response.status_code == 401

    def test_cancel_nonexistent(
        self, client: TestClient, valid_api_key: str
    ):
        """Test: Cancelar petición inexistente retorna 404."""
        response = client.delete(
            "/api/queue/nonexistent-job",
            headers={"X-API-Key": valid_api_key},
        )
        assert response.status_code == 404

    def test_cancel_requires_api_key(self, client: TestClient):
        """Test: Cancelar requiere API Key."""
        response = client.delete("/api/queue/some-job-id")
        assert response.status_code == 401

    def test_execute_costos_creates_job(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_excel_file,
    ):
        """Test: Execute de costos crea un job y retorna 202."""
        response = client.post(
            "/api/costos/execute",
            headers={"X-API-Key": valid_api_key},
            files={
                "file": (
                    "test.xlsx",
                    valid_excel_file,
                    "application/octet-stream",
                )
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        assert data["message"] == "ME12 ejecutado exitosamente"

    def test_execute_condiciones_creates_job(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_condiciones_excel,
    ):
        """Test: Execute de condiciones crea un job y retorna 202."""
        import json

        credentials = json.dumps({
            "system": "ERQ",
            "mandt": "300",
            "username": "test_user",
            "password": "test_pass",
            "language": "ES",
        })

        response = client.post(
            "/api/condiciones/execute",
            headers={"X-API-Key": valid_api_key},
            data={"credentials": credentials},
            files={
                "file": (
                    "test.xlsx",
                    valid_condiciones_excel,
                    "application/octet-stream",
                )
            },
        )
        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        assert data["message"] == "VK12 ejecutado exitosamente"

    def test_queue_status_after_execute(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_excel_file,
    ):
        """Test: Después de execute, la cola muestra la petición completada."""
        # Ejecutar
        response = client.post(
            "/api/costos/execute",
            headers={"X-API-Key": valid_api_key},
            files={
                "file": (
                    "test.xlsx",
                    valid_excel_file,
                    "application/octet-stream",
                )
            },
        )
        job_id = response.json()["job_id"]

        # Verificar en la cola
        queue_response = client.get(
            f"/api/queue/status/{job_id}",
            headers={"X-API-Key": valid_api_key},
        )
        assert queue_response.status_code == 200
        data = queue_response.json()
        assert data["job_id"] == job_id
        assert data["status"] == "completed"

    def test_queue_stats_after_execute(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_excel_file,
    ):
        """Test: Stats se actualiza después de ejecutar."""
        # Ejecutar
        client.post(
            "/api/costos/execute",
            headers={"X-API-Key": valid_api_key},
            files={
                "file": (
                    "test.xlsx",
                    valid_excel_file,
                    "application/octet-stream",
                )
            },
        )

        # Verificar stats
        stats_response = client.get(
            "/api/queue/stats",
            headers={"X-API-Key": valid_api_key},
        )
        assert stats_response.status_code == 200
        data = stats_response.json()
        assert data["total_completed"] >= 1


# ============================================================
# Tests de Integración HTTP: Cola llena → 429
# ============================================================


class TestQueueFullHTTP:
    """Tests de integración HTTP que verifican HTTP 429 cuando la cola está llena."""

    @pytest.fixture(autouse=True)
    def _clear_global_queue(self):
        """Fixture que limpia la cola global antes y después de cada test."""
        _clear_queue_sync()
        yield
        _clear_queue_sync()

    def test_execute_costos_returns_429_when_queue_full(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_excel_file,
    ):
        """Verifica que POST /api/costos/execute retorna 429 cuando la cola está llena.

        Llena la cola a su capacidad máxima (5) y verifica que la petición
        subsecuente retorna HTTP 429 TOO MANY REQUESTS.
        """
        # Llenar la cola directamente a capacidad máxima (max_queue_size=5)
        loop = asyncio.new_event_loop()
        try:
            for i in range(5):
                loop.run_until_complete(
                    request_queue.enqueue(f"fill-costos-{i}", "ME12", "filler")
                )
        finally:
            loop.close()

        # La 6ta petición vía endpoint debería retornar 429
        valid_excel_file.seek(0)
        with patch(
            "routers.costos.validate_excel", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = (True, [], [{"Material": "MAT001"}])
            response = client.post(
                "/api/costos/execute",
                files={
                    "file": (
                        "test.xlsx",
                        valid_excel_file,
                        "application/octet-stream",
                    )
                },
                headers={"X-API-Key": valid_api_key},
            )
        assert response.status_code == 429
        assert "Cola llena" in response.json()["detail"]

    def test_execute_condiciones_returns_429_when_queue_full(
        self,
        client: TestClient,
        valid_api_key: str,
        valid_condiciones_excel,
    ):
        """Verifica que POST /api/condiciones/execute retorna 429 cuando la cola está llena.

        Llena la cola a su capacidad máxima (5) y verifica que la petición
        subsecuente retorna HTTP 429 TOO MANY REQUESTS.
        """
        import json

        # Llenar la cola directamente a capacidad máxima (max_queue_size=5)
        loop = asyncio.new_event_loop()
        try:
            for i in range(5):
                loop.run_until_complete(
                    request_queue.enqueue(f"fill-cond-{i}", "VK12", "filler")
                )
        finally:
            loop.close()

        # La 6ta petición vía endpoint debería retornar 429
        credentials = json.dumps({
            "system": "ERQ",
            "mandt": "300",
            "username": "test_user",
            "password": "test_pass",
            "language": "ES",
        })

        valid_condiciones_excel.seek(0)
        with patch(
            "routers.condiciones.validate_excel", new_callable=AsyncMock
        ) as mock_validate:
            mock_validate.return_value = (True, [], [{"Material": "MAT001"}])
            response = client.post(
                "/api/condiciones/execute",
                headers={"X-API-Key": valid_api_key},
                data={"credentials": credentials},
                files={
                    "file": (
                        "test.xlsx",
                        valid_condiciones_excel,
                        "application/octet-stream",
                    )
                },
            )
        assert response.status_code == 429
        assert "Cola llena" in response.json()["detail"]


# ============================================================
# Tests de Integración: JobStatus extendido
# ============================================================


class TestJobStatusExtended:
    """Tests para verificar que JobStatus extiende correctamente."""

    def test_job_status_has_queued(self):
        """Verifica que JobStatus tiene QUEUED."""
        from models.responses import JobStatus
        assert hasattr(JobStatus, "QUEUED")
        assert JobStatus.QUEUED.value == "queued"

    def test_job_status_has_cancelled(self):
        """Verifica que JobStatus tiene CANCELLED."""
        from models.responses import JobStatus
        assert hasattr(JobStatus, "CANCELLED")
        assert JobStatus.CANCELLED.value == "cancelled"

    def test_job_status_backward_compatible(self):
        """Verifica que los valores originales siguen existiendo."""
        from models.responses import JobStatus
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.PROCESSING.value == "processing"
        assert JobStatus.COMPLETED.value == "completed"
        assert JobStatus.FAILED.value == "failed"
