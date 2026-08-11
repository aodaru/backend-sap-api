"""
Router de Cola de Peticiones SAP.

Endpoints para gestionar la cola de peticiones a transacciones SAP,
incluyendo consulta de estado, cancelación y estadísticas.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from dependencies import verify_api_key
from models.queue_models import QueueJobStatus, QueueStats, QueueStatus
from services.queue_service import request_queue

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Cola"])


@router.get("/status/{job_id}", response_model=QueueStatus)
async def get_queue_status(
    job_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """
    Consulta el estado de una petición en la cola.

    Retorna la posición en la cola, tiempo estimado de espera
    y estado actual de la petición.

    Args:
        job_id: ID de la petición a consultar.

    Returns:
        QueueStatus con posición, tiempo estimado y estado.

    Raises:
        404: Si la petición no existe.
        401: Si no se proporciona API Key válida.
    """
    queue_status = await request_queue.get_status(job_id)

    if queue_status is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Petición {job_id} no encontrada",
        )

    return queue_status


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_200_OK,
)
async def cancel_queue_request(
    job_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """
    Cancela una petición en la cola.

    Solo se pueden cancelar peticiones en estado QUEUED.
    Si la petición ya está procesándose o completada, retorna error.

    Args:
        job_id: ID de la petición a cancelar.

    Returns:
        Mensaje de confirmación con el estado actualizado.

    Raises:
        404: Si la petición no existe.
        409: Si la petición no se puede cancelar (ya está procesándose).
        401: Si no se proporciona API Key válida.
    """
    try:
        cancelled = await request_queue.cancel(job_id)

        if not cancelled:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"La petición {job_id} no se puede cancelar. "
                    "Solo las peticiones en cola (queued) pueden ser canceladas."
                ),
            )

        return {
            "message": f"Petición {job_id} cancelada exitosamente",
            "job_id": job_id,
            "status": QueueJobStatus.CANCELLED.value,
        }

    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Petición {job_id} no encontrada",
        )


@router.get("/stats", response_model=QueueStats)
async def get_queue_stats(
    _api_key: str = Depends(verify_api_key),
):
    """
    Retorna estadísticas actuales de la cola de peticiones.

    Incluye conteos de peticiones por estado:
    - En cola (queued)
    - Procesándose (processing)
    - Completadas (completed)
    - Fallidas (failed)
    - Canceladas (cancelled)

    Requiere autenticación via header X-API-Key.
    """
    return await request_queue.get_stats()
