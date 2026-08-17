"""Proveedor opcional y seguro de sesiones SAP GUI.

``win32com`` y ``pythoncom`` se importan dentro de ``acquire()`` para
mantener compatibilidad con CI en Linux donde no hay SAP GUI instalado.

El proveedor implementa el ciclo completo de SAP GUI (equivalente al
desktop ``SapClient``): abrir SAP Logon, conectar, loguear, retornar
sesión, y cerrar completamente al liberar.
"""

from __future__ import annotations

import gc
import subprocess
import time
from collections.abc import Mapping
from typing import Any, Optional, Protocol

from services.sap_errors import (
    SapAuthenticationError,
    SapConnectionError,
    SapConnectionUnavailableError,
    SapGuiNotFoundError,
    SapIntegrationDisabledError,
    SapScriptingUnavailableError,
    SapSessionBusyError,
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
    """Proveedor completo para SAP GUI Scripting en Windows.

    Implementa el ciclo completo: abrir SAP Logon, conectar, loguear,
    y cerrar completamente.  Equivalente al ``SapClient`` del desktop.

    ``win32com`` y ``pythoncom`` se importan dentro de ``acquire()``
    para mantener compatibilidad con CI en Linux.
    """

    _DEFAULT_SAP_LOGON_PATH = (
        r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
    )

    def __init__(
        self,
        sap_logon_path: Optional[str] = None,
        system: Optional[str] = None,
        mandt: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        language: Optional[str] = None,
    ) -> None:
        self.sap_logon_path = sap_logon_path or self._DEFAULT_SAP_LOGON_PATH
        self.system = system or "PRD"
        self.mandt = mandt or "300"
        self.username = username or ""
        self.password = password or ""
        self.language = language or "ES"

        # Referencias COM para limpieza en release()
        self._application: Any = None
        self._connection: Any = None

    # ------------------------------------------------------------------ #
    #  acquire — ciclo completo                                            #
    # ------------------------------------------------------------------ #

    def acquire(self, credentials: Optional[Mapping[str, str]] = None) -> Any:
        """Abre SAP GUI, conecta, loguea y retorna la sesión.

        Flujo ( replica desktop ``connect()`` + ``login()`` ):
        1. Importar win32com/pythoncom (dentro del método para CI Linux)
        2. Inicializar COM para thread safety
        3. Obtener SAP GUI (iniciar SAP Logon si no está corriendo)
        4. Buscar conexión existente (compatibilidad) o crear nueva
        5. Login con mandt/usuario/contraseña/idioma
        6. Retornar sesión

        Las credenciales del multipart (VK12) sobreescriben los valores
        del ``.env`` (ME12 usa fijos del ``.env``).
        """
        mandt = (credentials or {}).get("mandt", self.mandt)
        username = (credentials or {}).get("username", self.username)
        password = (credentials or {}).get("password", self.password)
        language = (credentials or {}).get("language", self.language)
        system = (credentials or {}).get("system", self.system)

        # Importar win32com dentro del método para compatibilidad CI/Linux
        try:
            import win32com.client  # type: ignore[import-not-found]
        except ImportError as exc:
            raise SapScriptingUnavailableError() from exc

        # pythoncom puede no estar disponible en CI/Linux; solo se
        # necesita en Windows para inicializar COM en hilos secundarios.
        try:
            import pythoncom  # type: ignore[import-not-found]
            pythoncom.CoInitialize()
        except ImportError:
            pass

        # --- Fase 1: Obtener SAP GUI Application ---
        SapGuiAuto = self._get_sap_gui(win32com.client)

        application = SapGuiAuto.GetScriptingEngine

        # --- Fase 2: Obtener o crear conexión ---
        # Ruta compatible: si SAP ya está corriendo con conexiones, usarlas
        existing_connection = self._find_existing_connection(application)
        if existing_connection is not None:
            return self._use_existing_session(existing_connection)

        # Nueva conexión: ciclo completo (abrir SAP Logon, conectar, login)
        connection = self._create_connection(application, system)
        session = self._setup_session(connection)
        self._login(session, mandt, username, password, language)

        self._application = application
        self._connection = connection
        return session

    # ------------------------------------------------------------------ #
    #  Fase 1: SAP GUI Application                                        #
    # ------------------------------------------------------------------ #

    def _get_sap_gui(self, client_module: Any) -> Any:
        """Obtiene o inicia SAP GUI con lógica de reintentos.

        Replica la espera activa del desktop ``connect()``: si SAP Logon
        tarda en registrar su objeto COM, se reintenta con delays.
        """
        # Ruta rápida: SAP GUI ya corriendo
        try:
            return client_module.GetObject("SAPGUI")
        except Exception:
            pass

        # SAP GUI no está corriendo — iniciar SAP Logon
        sap_logon_started = self._open_sap_logon()

        if not sap_logon_started:
            # No se pudo iniciar SAP Logon — intentar una vez más
            try:
                return client_module.GetObject("SAPGUI")
            except Exception:
                raise SapGuiNotFoundError()

        # Espera activa con reintentos (como desktop connect())
        max_retries = 10
        for attempt in range(max_retries):
            try:
                time.sleep(2)
                return client_module.GetObject("SAPGUI")
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    raise SapGuiNotFoundError()

    def _open_sap_logon(self) -> bool:
        """Abre saplogon.exe via subprocess. Retorna True si se inició."""
        try:
            subprocess.Popen(self.sap_logon_path)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------ #
    #  Fase 2: Conexión                                                   #
    # ------------------------------------------------------------------ #

    def _find_existing_connection(self, application: Any) -> Any:
        """Busca una conexión SAP existente (ruta compatible)."""
        if application.Children.Count > 0:
            return application.Children(0)
        return None

    def _use_existing_session(self, connection: Any) -> Any:
        """Usa una sesión existente en una conexión activa."""
        if connection.Children.Count == 0:
            raise SapSessionUnavailableError()
        session = connection.Children(0)
        if getattr(session, "Busy", False):
            raise SapSessionBusyError()
        return session

    def _create_connection(self, application: Any, system: str) -> Any:
        """Crea una nueva conexión SAP via OpenConnection."""
        try:
            return application.OpenConnection(system, True)
        except Exception as exc:
            raise SapConnectionUnavailableError() from exc

    def _setup_session(self, connection: Any) -> Any:
        """Espera la sesión y maximiza la ventana."""
        time.sleep(3)
        session = connection.Children(0)
        session.findById("wnd[0]").maximize()
        return session

    # ------------------------------------------------------------------ #
    #  Login                                                              #
    # ------------------------------------------------------------------ #

    def _login(
        self,
        session: Any,
        mandt: str,
        username: str,
        password: str,
        language: str,
    ) -> None:
        """Login a SAP con credenciales. Maneja popup 'Session already open'."""
        try:
            session.findById("wnd[0]/usr/txtRSYST-MANDT").text = mandt
            session.findById("wnd[0]/usr/txtRSYST-BNAME").text = username
            session.findById("wnd[0]/usr/pwdRSYST-BCODE").text = password
            session.findById("wnd[0]/usr/txtRSYST-LANGU").text = language
            session.findById("wnd[0]").sendVKey(0)
            time.sleep(2)

            # Manejar popup "Session already open" si aparece
            try:
                popup = session.findById("wnd[1]")
                if popup and "already open" in str(popup.Text):
                    popup.findById("tbar[0]/btn[0]").press()
            except Exception:
                pass  # No apareció el popup, todo OK

        except Exception as exc:
            raise SapAuthenticationError() from exc

    # ------------------------------------------------------------------ #
    #  release — cierre completo                                          #
    # ------------------------------------------------------------------ #

    def release(self, session: Any) -> None:
        """Cierra SAP completamente: sesión, aplicación, fallback taskkill.

        Equivalente al desktop ``close()``: ``CloseSession``, ``Exit``,
        limpieza de referencias COM y ``taskkill`` como fallback.
        Esto evita la entrada corrupta en el ROT que causaba errores
        en la segunda ejecución.
        """
        try:
            if self._connection:
                try:
                    self._connection.CloseSession("ses[0]")
                except Exception:
                    pass
            if self._application:
                try:
                    self._application.Exit()
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            self._application = None
            self._connection = None
            gc.collect()

            # Fallback: matar procesos SAP si aún están corriendo
            for proc in ("saplogon.exe", "sapgui.exe"):
                try:
                    subprocess.run(
                        ["taskkill", "/f", "/im", proc],
                        capture_output=True,
                        timeout=5,
                    )
                except Exception:
                    pass


class NullSapSessionProvider:
    """Proveedor no operativo: nunca simula una ejecución SAP exitosa."""

    def acquire(self, credentials: Optional[Mapping[str, str]] = None) -> Any:
        del credentials
        raise SapIntegrationDisabledError()

    def release(self, session: Any) -> None:
        del session
