"""
Router de Health Check.

Endpoint público para verificar que el servicio esté operativo.
No requiere autenticación (diseñado para load balancers y monitoreo).
"""

from datetime import datetime, timezone

from fastapi import APIRouter

from models.responses import HealthResponse

router = APIRouter(tags=["General"])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Verifica que el servidor esté operativo.
    Endpoint público - no requiere autenticación.
    """
    return HealthResponse(
        status="ok",
        message="Servicio listo para procesar pedidos",
        timestamp=datetime.now(timezone.utc),
    )
