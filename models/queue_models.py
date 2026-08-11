"""
Modelos de datos para el sistema de cola de peticiones.

Define los modelos Pydantic para la cola de peticiones SAP,
incluyendo estados, peticiones en cola y estadísticas.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QueueJobStatus(str, Enum):
    """Estados posibles de un job en la cola de peticiones."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueRequest(BaseModel):
    """
    Modelo de una petición en la cola.

    Representa el estado completo de una transacción SAP
    que está en cola o ya fue procesada.
    """

    job_id: str = Field(..., description="ID único de la petición")
    transaction: str = Field(
        ..., description="Tipo de transacción (ME12, VK12, etc.)"
    )
    status: QueueJobStatus = Field(
        ..., description="Estado actual de la petición"
    )
    position: int = Field(
        default=0, description="Posición en la cola (0 si no está en cola)"
    )
    queued_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de cuando se encoló",
    )
    started_at: Optional[datetime] = Field(
        default=None, description="Timestamp de inicio de ejecución"
    )
    completed_at: Optional[datetime] = Field(
        default=None, description="Timestamp de finalización"
    )
    error_message: Optional[str] = Field(
        default=None, description="Mensaje de error si falló"
    )
    user_id: str = Field(
        default="system", description="Identificador del usuario"
    )


class QueueStatus(BaseModel):
    """
    Estado de una petición en la cola.

    Retorna información de posición y tiempo estimado de espera.
    """

    job_id: str = Field(..., description="ID de la petición")
    position: int = Field(
        default=0, description="Posición en la cola (0 si no está en cola)"
    )
    estimated_wait: int = Field(
        default=0,
        description="Tiempo estimado de espera en segundos",
    )
    status: QueueJobStatus = Field(..., description="Estado actual")


class QueueStats(BaseModel):
    """
    Estadísticas actuales de la cola de peticiones.
    """

    total_queued: int = Field(
        default=0, description="Peticiones encoladas esperando procesamiento"
    )
    total_processing: int = Field(
        default=0, description="Peticiones en proceso de ejecución"
    )
    total_completed: int = Field(
        default=0, description="Peticiones completadas exitosamente"
    )
    total_failed: int = Field(
        default=0, description="Peticiones que fallaron"
    )
    total_cancelled: int = Field(
        default=0, description="Peticiones canceladas por el usuario"
    )
    max_queue_size: int = Field(
        default=5, description="Tamaño máximo de la cola"
    )
