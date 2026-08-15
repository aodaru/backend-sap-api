"""
Modelos de respuesta de la API.

Define los modelos Pydantic para respuestas estandarizadas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """
    Modelo de respuesta de error.

    Utilizado para respuestas de error consistentes
    en toda la API (ej: errores de autenticación 401).
    """

    detail: str


class HealthResponse(BaseModel):
    """Modelo de respuesta para health check."""

    status: str = Field(..., description="Estado del servicio: ok o error")
    message: str = Field(..., description="Descripción legible del estado")
    timestamp: datetime = Field(..., description="Timestamp de la respuesta")


class JobStatus(str, Enum):
    """Estados posibles de un job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    QUEUED = "queued"
    CANCELLED = "cancelled"


class ValidationDetail(BaseModel):
    """Detalle de validación de una fila del Excel."""

    row: int = Field(..., description="Número de fila con error")
    field: str = Field(..., description="Campo con error")
    error: str = Field(..., description="Descripción del error")


class CostosUploadResponse(BaseModel):
    """Modelo de respuesta para upload de costos."""

    filename: str = Field(..., description="Nombre del archivo subido")
    row_count: int = Field(..., description="Número de filas procesadas")
    valid: bool = Field(..., description="Si el archivo es válido")
    validations: List[ValidationDetail] = Field(
        default_factory=list, description="Detalles de errores de validación"
    )


class CostosExecuteResponse(BaseModel):
    """Modelo de respuesta para ejecución de ME12."""

    job_id: str = Field(..., description="ID del job creado")
    status: JobStatus = Field(..., description="Estado inicial del job")
    message: str = Field(..., description="Mensaje descriptivo")


class CostosStatusResponse(BaseModel):
    """Modelo de respuesta para estado de job."""

    job_id: str = Field(..., description="ID del job")
    status: JobStatus = Field(..., description="Estado del job")
    progress: int = Field(..., description="Progreso del 0 al 100")
    results: Optional[Dict[str, Any]] = Field(
        default=None, description="Resultados cuando el job completa"
    )


# --- Modelos para VK12 Condiciones ---


class CondicionesUploadResponse(BaseModel):
    """Modelo de respuesta para upload de condiciones."""

    filename: str = Field(..., description="Nombre del archivo subido")
    row_count: int = Field(..., description="Número de filas procesadas")
    valid: bool = Field(..., description="Si el archivo es válido")
    validations: List[ValidationDetail] = Field(
        default_factory=list, description="Detalles de errores de validación"
    )


class CondicionesExecuteRequest(BaseModel):
    """Modelo de request para ejecución de VK12 con credenciales SAP."""

    system: str = Field(..., description="Sistema SAP (ej: ERQ)")
    mandt: str = Field(..., description="Cliente SAP (ej: 200)")
    username: str = Field(..., description="Usuario SAP")
    password: str = Field(..., description="Contraseña SAP")
    language: str = Field(default="ES", description="Idioma SAP (ej: ES)")


class CondicionesExecuteResponse(BaseModel):
    """Modelo de respuesta para ejecución de VK12."""

    job_id: str = Field(..., description="ID del job creado")
    status: JobStatus = Field(..., description="Estado inicial del job")
    message: str = Field(..., description="Mensaje descriptivo")


class CondicionesStatusResponse(BaseModel):
    """Modelo de respuesta para estado de job de condiciones."""

    job_id: str = Field(..., description="ID del job")
    status: JobStatus = Field(..., description="Estado del job")
    progress: int = Field(..., description="Progreso del 0 al 100")
    results: Optional[Dict[str, Any]] = Field(
        default=None, description="Resultados cuando el job completa"
    )
