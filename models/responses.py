"""
Modelos de respuesta de la API.

Define los modelos Pydantic para respuestas de error estandarizadas.
"""

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    """
    Modelo de respuesta de error.

    Utilizado para respuestas de error consistentes
    en toda la API (ej: errores de autenticación 401).
    """

    detail: str
