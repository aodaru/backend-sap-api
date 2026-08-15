"""Proveedor opcional y seguro de sesiones SAP GUI.

``win32com`` se importa únicamente al solicitar una sesión y por tanto este
módulo puede importarse y probarse en Linux/CI sin SAP instalado.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Optional, Protocol

from services.sap_errors import (
    SapConnectionError,
    SapConnectionUnavailableError,
    SapIntegrationDisabledError,
    SapGuiNotFoundError,
    SapSessionBusyError,
    SapScriptingUnavailableError,
    SapSessionUnavailableError,
)


class SapSession(Protocol):
    """Contrato mínimo que usan los adaptadores y los mocks."""

    def release(self) -> None: ...


class SapSessionProvider(Protocol):
    """Obtiene una sesión ya abierta, nunca crea sesiones concurrentes."""

    def acquire(self, credentials: Optional[Mapping[str, str]] = None) -> Any: ...

    def release(self, session: Any) -> None: ...


class Win32ComSapSessionProvider:
    """Proveedor para SAP GUI Scripting en Windows.

    La conexión, el mandante y el idioma se configuran fuera del código. El
    proveedor solo inspecciona conexiones/sesiones ya abiertas.
    """

    def __init__(self, connection_name: Optional[str] = None, session_index: int = 0) -> None:
        self.connection_name = connection_name
        self.session_index = session_index

    def acquire(self, credentials: Optional[Mapping[str, str]] = None) -> Any:
        del credentials  # Nunca se conserva ni se registra.
        try:
            import win32com.client  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SapScriptingUnavailableError() from exc
        try:
            try:
                sap_gui = win32com.client.GetObject("SAPGUI")
            except Exception as exc:
                raise SapGuiNotFoundError() from exc
            application = sap_gui.GetScriptingEngine
            connections = [application.Children(i) for i in range(application.Children.Count)]
            if self.connection_name:
                connections = [c for c in connections if getattr(c, "Description", "") == self.connection_name]
            if not connections:
                raise SapConnectionUnavailableError()
            connection = connections[0]
            if connection.Children.Count <= self.session_index:
                raise SapSessionUnavailableError()
            session = connection.Children(self.session_index)
            if getattr(session, "Busy", False):
                raise SapSessionBusyError()
            return session
        except (SapGuiNotFoundError, SapConnectionUnavailableError, SapSessionUnavailableError, SapSessionBusyError):
            raise
        except Exception as exc:
            raise SapConnectionError() from exc

    def release(self, session: Any) -> None:
        """Deja la sesión abierta, pero libera referencias del job."""
        try:
            if hasattr(session, "release"):
                session.release()
        except Exception:
            # El cierre del job no debe dejar el worker bloqueado.
            return


class NullSapSessionProvider:
    """Proveedor no operativo: nunca simula una ejecución SAP exitosa."""

    def acquire(self, credentials: Optional[Mapping[str, str]] = None) -> Any:
        del credentials
        raise SapIntegrationDisabledError()

    def release(self, session: Any) -> None:
        del session
