"""
Modelos de respuesta de la API.

Define los modelos Pydantic para respuestas estandarizadas.
"""

from datetime import datetime

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
