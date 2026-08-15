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


class SapConnectionError(SapIntegrationError):
    code = "connection_error"
    retryable = True
    public_message = "No se pudo conectar con SAP GUI"


class SapSessionUnavailableError(SapIntegrationError):
    code = "session_unavailable"
    public_message = "No hay una sesión SAP GUI activa y disponible"


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


def public_error(error: Exception) -> tuple[str, int]:
    """Convierte cualquier excepción en mensaje/status seguros para HTTP."""
    code = getattr(error, "code", "sap_error")
    message = getattr(error, "public_message", "No se pudo completar la operación SAP")
    status = 504 if "timeout" in code else 503
    if code == "queue_full":
        status = 429
    if code in {"business_error", "authentication_error"}:
        status = 422
    return message, status


def safe_exception(error: Exception) -> Exception:
    """Conserva clasificación sin conservar el texto potencialmente secreto."""
    error_type = type(error) if isinstance(error, SapIntegrationError) else SapIntegrationError
    try:
        return error_type()
    except TypeError:
        return SapIntegrationError()
