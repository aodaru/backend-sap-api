"""Errores públicos y clasificación de fallos de la frontera SAP."""

from __future__ import annotations


class SapIntegrationError(Exception):
    """Error seguro para devolver y auditar una operación SAP."""

    code = "sap_error"
    retryable = False
    public_message = "No se pudo completar la operación SAP"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.public_message)
        self.message = message or self.public_message


class SapIntegrationDisabledError(SapIntegrationError):
    """La ejecución real fue solicitada sin habilitar la integración SAP."""

    code = "integration_disabled"
    public_message = "La integración real con SAP GUI no está habilitada"


class SapConnectionError(SapIntegrationError):
    code = "connection_error"
    retryable = True
    public_message = "No se pudo conectar con SAP GUI"


class SapGuiNotFoundError(SapIntegrationError):
    """SAPGUI no está registrado/abierto en el host Windows."""

    code = "sapgui_not_found"
    public_message = "SAP GUI no está disponible en este host"


class SapConnectionUnavailableError(SapIntegrationError):
    """No existe una conexión SAP GUI que coincida con la configuración."""

    code = "connection_unavailable"
    public_message = "No hay una conexión SAP GUI disponible"


class SapSessionUnavailableError(SapIntegrationError):
    code = "session_unavailable"
    public_message = "No hay una sesión SAP GUI activa y disponible"


class SapSessionBusyError(SapIntegrationError):
    """La sesión encontrada está ocupada o bloqueada."""

    code = "session_busy"
    public_message = "La sesión SAP GUI está ocupada; inténtelo más tarde"


class SapScriptingUnavailableError(SapIntegrationError):
    code = "scripting_unavailable"
    public_message = "SAP GUI Scripting no está disponible en este host"


class SapNavigationError(SapIntegrationError):
    code = "navigation_error"
    # La navegación pudo haber enviado una modificación; no es seguro repetirla.
    retryable = False
    public_message = "SAP no pudo abrir la transacción solicitada"


class SapBusinessError(SapIntegrationError):
    code = "business_error"
    public_message = "SAP rechazó los datos de la operación"


class SapAuthenticationError(SapIntegrationError):
    code = "authentication_error"
    public_message = "SAP rechazó las credenciales proporcionadas"


class SapExecutionTimeoutError(SapIntegrationError):
    code = "execution_timeout"
    retryable = True
    public_message = "La ejecución SAP excedió el tiempo límite"


class QueueFullError(SapIntegrationError):
    code = "queue_full"
    public_message = "La cola SAP está llena"


class QueueWaitTimeoutError(SapIntegrationError):
    code = "queue_wait_timeout"
    public_message = "El job excedió el tiempo máximo de espera en la cola SAP"


OPERATIONAL_CODES = frozenset(
    {
        "sap_error", "integration_disabled", "scripting_unavailable",
        "sapgui_not_found", "connection_unavailable", "connection_error",
        "session_unavailable", "session_busy", "navigation_error",
        "business_error", "authentication_error", "execution_timeout",
        "queue_full", "queue_wait_timeout",
    }
)

PUBLIC_ERRORS: dict[str, tuple[str, int]] = {
    "sap_error": ("No se pudo completar la operación SAP", 503),
    "integration_disabled": (SapIntegrationDisabledError.public_message, 503),
    "scripting_unavailable": (SapScriptingUnavailableError.public_message, 503),
    "sapgui_not_found": (SapGuiNotFoundError.public_message, 503),
    "connection_unavailable": (SapConnectionUnavailableError.public_message, 503),
    "connection_error": (SapConnectionError.public_message, 503),
    "session_unavailable": (SapSessionUnavailableError.public_message, 503),
    "session_busy": (SapSessionBusyError.public_message, 503),
    "navigation_error": (SapNavigationError.public_message, 503),
    "business_error": (SapBusinessError.public_message, 422),
    "authentication_error": (SapAuthenticationError.public_message, 422),
    "execution_timeout": (SapExecutionTimeoutError.public_message, 504),
    "queue_full": (QueueFullError.public_message, 429),
    "queue_wait_timeout": (QueueWaitTimeoutError.public_message, 504),
}


def public_error(error: Exception) -> tuple[str, int]:
    """Convierte cualquier excepción en mensaje/status seguros para HTTP."""
    code = getattr(error, "code", "sap_error")
    if code not in OPERATIONAL_CODES:
        code = "sap_error"
    return PUBLIC_ERRORS[code]


def safe_exception(error: Exception) -> Exception:
    """Conserva clasificación sin conservar el texto potencialmente secreto."""
    error_type = type(error) if isinstance(error, SapIntegrationError) else SapIntegrationError
    try:
        return error_type()
    except TypeError:
        return SapIntegrationError()


def operational_context(error: Exception) -> dict[str, object]:
    """Devuelve únicamente contexto fijo y no sensible para auditoría."""
    code = getattr(error, "code", "sap_error")
    if code not in OPERATIONAL_CODES:
        code = "sap_error"
    return {
        "operational_code": code,
        "retryable": bool(getattr(error, "retryable", False)),
        "diagnostic_stage": {
            "integration_disabled": "configuration",
            "scripting_unavailable": "dependencies",
            "sapgui_not_found": "sapgui_process",
            "connection_unavailable": "sap_connection",
            "connection_error": "sap_connection",
            "session_unavailable": "sap_session",
            "session_busy": "sap_session",
            "execution_timeout": "execution",
            "queue_wait_timeout": "queue",
            "queue_full": "queue",
        }.get(code, "execution"),
    }
