"""
Tests unitarios para services/queue_service.py.

Verifica la lógica de la cola de peticiones:
- RequestQueue (enqueue, dequeue, cancel, get_status, get_stats, process_with_retries)
- Thread-safety y manejo de errores
- Reintentos automáticos

Nota: Tests de integración HTTP están en tests/test_queue.py.
"""

import asyncio
from unittest.mock import AsyncMock

import pytest

from services.queue_service import TRANSIENT_ERRORS, RequestQueue


# ============================================================
# Tests para constantes
# ============================================================


class TestTransientErrors:
    """Tests para la tupla TRANSIENT_ERRORS."""

    def test_contains_timeout_error(self):
        """Test: TimeoutError está en errores transitorios."""
        assert TimeoutError in TRANSIENT_ERRORS

    def test_contains_connection_error(self):
        """Test: ConnectionError está en errores transitorios."""
        assert ConnectionError in TRANSIENT_ERRORS

    def test_contains_os_error(self):
        """Test: OSError está en errores transitorios."""
        assert OSError in TRANSIENT_ERRORS

    def test_is_tuple(self):
        """Test: TRANSIENT_ERRORS es una tupla."""
        assert isinstance(TRANSIENT_ERRORS, tuple)


# ============================================================
# Tests para RequestQueue - process_with_retries
# ============================================================


class TestProcessWithRetries:
    """Tests para el método process_with_retries."""

    @pytest.fixture
    def queue(self):
        """Fixture que retorna una cola limpia."""
        q = RequestQueue(max_size=5)
        return q

    @pytest.mark.asyncio
    async def test_returns_result_on_success(self, queue):
        """Test: Retorna resultado cuando la función tiene éxito."""
        await queue.clear()
        await queue.enqueue("job-1", "ME12", "user1")

        async def success_func():
            return {"status": "ok"}

        result = await queue.process_with_retries("job-1", success_func)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_retries_on_transient_error(self, queue):
        """Test: Reintenta en errores transitorios."""
        await queue.clear()
        await queue.enqueue("job-retry", "ME12", "user1")

        call_count = 0

        async def transient_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Connection refused")
            return {"status": "recovered"}

        result = await queue.process_with_retries("job-retry", transient_func)
        assert result == {"status": "recovered"}
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_does_not_retry_business_error(self, queue):
        """Test: No reintenta en errores de negocio."""
        await queue.clear()
        await queue.enqueue("job-biz", "ME12", "user1")

        async def business_error():
            raise ValueError("Error de validación")

        with pytest.raises(ValueError, match="Error de validación"):
            await queue.process_with_retries("job-biz", business_error)

    @pytest.mark.asyncio
    async def test_fails_after_max_retries(self, queue):
        """Test: Falla después de agotar reintentos."""
        await queue.clear()
        await queue.enqueue("job-max", "ME12", "user1")

        async def always_fails():
            raise ConnectionError("Siempre falla")

        with pytest.raises(Exception, match="Agotados los reintentos"):
            await queue.process_with_retries("job-max", always_fails)

    @pytest.mark.asyncio
    async def test_timeout_retries(self, queue):
        """Test: Reintenta en TimeoutError."""
        await queue.clear()
        await queue.enqueue("job-timeout", "ME12", "user1")

        call_count = 0

        async def timeout_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise asyncio.TimeoutError("Timeout")
            return {"status": "ok"}

        result = await queue.process_with_retries("job-timeout", timeout_func)
        assert result == {"status": "ok"}
        assert call_count == 2
