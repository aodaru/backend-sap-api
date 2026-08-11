"""
Router de Logs y Auditoría.

Endpoints para consultar los logs de auditoría del sistema.
Requiere autenticación via API Key.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from dependencies import verify_api_key
from models.log_models import (
    AuditLogEntry,
    LogQueryParams,
    LogResponse,
    LogStatus,
)
from services.logging_service import audit_logger

router = APIRouter(tags=["Logs"])


@router.get("", response_model=LogResponse)
async def get_logs(
    transaction: Optional[str] = Query(
        default=None, description="Filtrar por transacción (ME12, VK12)"
    ),
    user_id: Optional[str] = Query(
        default=None, description="Filtrar por usuario"
    ),
    date_from: Optional[str] = Query(
        default=None, description="Fecha inicio (YYYY-MM-DD)"
    ),
    date_to: Optional[str] = Query(
        default=None, description="Fecha fin (YYYY-MM-DD)"
    ),
    status: Optional[LogStatus] = Query(
        default=None, description="Filtrar por estado"
    ),
    limit: int = Query(
        default=50, ge=1, le=500, description="Máximo de resultados"
    ),
    offset: int = Query(
        default=0, ge=0, description="Offset para paginación"
    ),
    _api_key: str = Depends(verify_api_key),
):
    """
    Lista logs de auditoría con filtros y paginación.

    Retorna una lista de logs que coinciden con los filtros proporcionados.
    Los resultados se ordenan por timestamp descendente (más recientes primero).

    Requiere autenticación via header X-API-Key.
    """
    filters = LogQueryParams(
        transaction=transaction,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        status=status,
        limit=limit,
        offset=offset,
    )

    return audit_logger.get_logs(filters)


@router.get("/{job_id}", response_model=List[AuditLogEntry])
async def get_logs_by_job_id(
    job_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """
    Retorna logs asociados a un job_id específico.

    Útil para consultar el historial completo de una ejecución SAP.

    Requiere autenticación via header X-API-Key.
    """
    logs = audit_logger.get_logs_by_job_id(job_id)

    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontraron logs para el job {job_id}",
        )

    return logs
