"""
Modelos de petición de la API.

Define los modelos Pydantic para peticiones entrantes.
"""

from pydantic import BaseModel, Field


class CostosExecuteRequest(BaseModel):
    """Modelo de petición para ejecutar ME12."""

    job_id: str = Field(..., description="ID del job a ejecutar")
