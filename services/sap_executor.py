"""Worker SAP único: sesión, timeout, reintentos y liberación segura."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping, Sequence
from typing import Any, Optional

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

    def __init__(self, provider: Optional[SapSessionProvider] = None) -> None:
        settings = get_settings()
        self._lock = asyncio.Lock()
        self._provider = provider or (
            Win32ComSapSessionProvider(
                sap_logon_path=settings.sap_logon_path,
                system=settings.sap_system,
                mandt=settings.sap_mandant,
                username=settings.sap_username,
                password=settings.sap_password,
                language=settings.sap_lang,
            )
            if settings.sap_integration_enabled else NullSapSessionProvider()
        )

    async def execute(
        self,
        transaction: str,
        rows: Sequence[Mapping[str, Any]],
        credentials: Optional[Mapping[str, str]] = None,
    ) -> TransactionResult:
        """Ejecuta un job con un solo worker y borra referencias a credenciales."""
        adapter = select_adapter(transaction)
        settings = get_settings()
        if not getattr(settings, "sap_integration_enabled", False):
            raise SapIntegrationDisabledError()
        if transaction.upper() == "VK12":
            if not credentials:
                raise SapBusinessError("Credenciales SAP requeridas para VK12")
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
