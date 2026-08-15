"""Worker SAP único: sesión, timeout, reintentos y liberación segura."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any

from config import get_settings
from services.sap_adapters import TransactionResult, select_adapter
from services.sap_errors import (
    SapBusinessError,
    SapConnectionError,
    SapExecutionTimeoutError,
    SapIntegrationDisabledError,
    SapIntegrationError,
    safe_exception,
)
from services.sap_session import NullSapSessionProvider, SapSessionProvider, Win32ComSapSessionProvider


class SapTransactionExecutor:
    """Serializa todas las transacciones sobre una única sesión SAP."""

    def __init__(self, provider: SapSessionProvider | None = None) -> None:
        settings = get_settings()
        self._lock = asyncio.Lock()
        self._provider = provider or (
            Win32ComSapSessionProvider(settings.sap_connection_name, settings.sap_session_index)
            if settings.sap_integration_enabled else NullSapSessionProvider()
        )

    async def execute(
        self,
        transaction: str,
        rows: Sequence[Mapping[str, Any]],
        credentials: Mapping[str, str] | None = None,
    ) -> TransactionResult:
        """Ejecuta un job con un solo worker y borra referencias a credenciales."""
        adapter = select_adapter(transaction)
        settings = get_settings()
        if not getattr(settings, "sap_integration_enabled", False):
            raise SapIntegrationDisabledError()
        if transaction.upper() == "VK12":
            if not credentials or credentials.get("mandt") != "300":
                raise SapBusinessError("Mandante SAP no permitido")
        async with self._lock:
            for attempt in range(settings.max_retries + 1):
                session = None
                try:
                    session = self._provider.acquire(credentials)
                    result = await asyncio.wait_for(
                        adapter.execute(session, rows), timeout=settings.sap_execution_timeout
                    )
                    return result
                except asyncio.TimeoutError as exc:
                    error: SapIntegrationError = SapExecutionTimeoutError()
                except SapIntegrationError as exc:
                    error = exc
                except (ConnectionError, OSError) as exc:
                    error = SapConnectionError()
                finally:
                    if session is not None:
                        self._provider.release(session)
                if not error.retryable or attempt >= settings.max_retries:
                    raise safe_exception(error)
                await asyncio.sleep(min(2**attempt, settings.sap_retry_backoff))
        raise RuntimeError("worker SAP terminó sin resultado")


sap_executor = SapTransactionExecutor()
