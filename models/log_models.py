"""
Modelos de auditoría y logging.

Define los modelos Pydantic para la estructura de log entries,
filtros de consulta y respuestas paginadas del endpoint de logs.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    """Niveles de log de auditoría."""

    AUDIT = "audit"
    INFO = "info"
    ERROR = "error"


class LogStatus(str, Enum):
    """Estados posibles de una ejecución en los logs."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


class ErrorDetail(BaseModel):
    """
    Detalle de un error individual en una ejecución SAP.

    Cada error incluye contexto de la fila del Excel y el
    material/proveedor afectado para facilitar la depuración.
    """

    row: int = Field(..., description="Número de fila del Excel")
    material: str = Field(..., description="Código del material")
    proveedor: str = Field(..., description="Proveedor (ME12) o N/A (VK12)")
    message: str = Field(..., description="Mensaje descriptivo del error")


class AuditLogEntry(BaseModel):
    """
    Entrada de log de auditoría.

    Representa una ejecución SAP u operación auditable.
    Cada campo está documentado en specs/requirements.md.
    """

    timestamp: str = Field(
        ..., description="Timestamp ISO 8601 UTC del evento"
    )
    level: LogLevel = Field(
        default=LogLevel.AUDIT, description="Nivel del log"
    )
    event_type: str = Field(
        ..., description="Tipo de evento (execution, auth, upload, error)"
    )
    user_id: str = Field(
        ..., description="Identificador del usuario SAP"
    )
    transaction: Optional[str] = Field(
        default=None, description="Tipo de transacción SAP (ME12, VK12)"
    )
    job_id: Optional[str] = Field(
        default=None, description="ID del job asociado"
    )
    status: Optional[LogStatus] = Field(
        default=None, description="Resultado de la operación"
    )
    duration_seconds: Optional[float] = Field(
        default=None, description="Tiempo total de la ejecución en segundos"
    )
    sap_login_success: Optional[bool] = Field(
        default=None, description="Si el login a SAP fue exitoso"
    )
    rows_total: Optional[int] = Field(
        default=None, description="Total de filas procesadas"
    )
    rows_success: Optional[int] = Field(
        default=None, description="Filas exitosas"
    )
    rows_failed: Optional[int] = Field(
        default=None, description="Filas con error"
    )
    errors: List[ErrorDetail] = Field(
        default_factory=list, description="Lista de errores detallados"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Información adicional (filename, org_compras, etc.)"
    )
    ip_address: Optional[str] = Field(
        default=None, description="Dirección IP del cliente (solo auth)"
    )
    message: Optional[str] = Field(
        default=None, description="Mensaje descriptivo del evento"
    )


class LogQueryParams(BaseModel):
    """
    Parámetros de filtro para la consulta de logs.

    Todos los campos son opcionales; si no se proveen,
    se retornan todos los logs sin filtro adicional.
    """

    transaction: Optional[str] = Field(
        default=None, description="Filtrar por tipo de transacción (ME12, VK12)"
    )
    user_id: Optional[str] = Field(
        default=None, description="Filtrar por identificador de usuario"
    )
    date_from: Optional[str] = Field(
        default=None,
        description="Fecha inicio del rango (formato YYYY-MM-DD)",
    )
    date_to: Optional[str] = Field(
        default=None,
        description="Fecha fin del rango (formato YYYY-MM-DD)",
    )
    status: Optional[LogStatus] = Field(
        default=None, description="Filtrar por estado de la ejecución"
    )
    limit: int = Field(
        default=50, ge=1, le=500, description="Número máximo de resultados"
    )
    offset: int = Field(
        default=0, ge=0, description="Offset para paginación"
    )


class LogResponse(BaseModel):
    """
    Respuesta paginada del endpoint de consulta de logs.

    Incluye los logs solicitados y metadatos de paginación.
    """

    total: int = Field(
        ..., description="Total de logs que coinciden con los filtros"
    )
    limit: int = Field(..., description="Límite aplicado en la consulta")
    offset: int = Field(..., description="Offset aplicado en la consulta")
    logs: List[AuditLogEntry] = Field(
        default_factory=list, description="Lista de logs de auditoría"
    )
