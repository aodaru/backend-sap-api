"""
Servicio de Cola de Peticiones SAP.

Implementa una cola en memoria thread-safe para gestionar
peticiones concurrentes a transacciones SAP (ME12, VK12, etc.).

Características:
- Thread-safety via asyncio.Lock
- Límite máximo de peticiones en cola (configurable)
- Cancelación de peticiones en estado queued
- Reintentos automáticos en errores transitorios (max 2)
- Timeout configurable por ejecución
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine, Dict, List, Optional

from config import get_settings
from models.queue_models import (
    QueueJobStatus,
    QueueRequest,
    QueueStats,
    QueueStatus,
)

logger = logging.getLogger(__name__)

# Errores transitorios que justifican reintento
TRANSIENT_ERRORS = (TimeoutError, ConnectionError, ConnectionRefusedError, OSError)


class RequestQueue:
    """
    Cola de peticiones SAP en memoria con thread-safety.

    Gestiona una cola FIFO de peticiones a transacciones SAP,
    con soporte para cancelación, reintentos y timeout configurable.
    """

    def __init__(self, max_size: Optional[int] = None) -> None:
        """
        Inicializa la cola de peticiones.

        Args:
            max_size: Tamaño máximo de la cola. Si es None, usa configuración.
        """
        settings = get_settings()
        self._max_size = max_size or settings.max_queue_size
        self._max_retries = settings.max_retries
        self._execution_timeout = settings.sap_execution_timeout

        # Cola FIFO de peticiones
        self._queue: List[QueueRequest] = []
        # Historial de todas las peticiones (incluye completadas, fallidas, canceladas)
        self._history: Dict[str, QueueRequest] = {}
        # Lock para operaciones thread-safe
        self._lock = asyncio.Lock()

    @property
    def max_size(self) -> int:
        """Retorna el tamaño máximo de la cola."""
        return self._max_size

    async def enqueue(
        self,
        job_id: str,
        transaction: str,
        user_id: str = "system",
    ) -> int:
        """
        Añade una petición a la cola.

        Args:
            job_id: ID único de la petición.
            transaction: Tipo de transacción (ME12, VK12, etc.).
            user_id: Identificador del usuario.

        Returns:
            Posición en la cola (1-N).

        Raises:
            ValueError: Si la cola está llena (HTTP 429).
        """
        async with self._lock:
            if len(self._queue) >= self._max_size:
                raise ValueError(
                    f"Cola llena. Máximo {self._max_size} peticiones en cola."
                )

            position = len(self._queue) + 1

            request = QueueRequest(
                job_id=job_id,
                transaction=transaction,
                status=QueueJobStatus.QUEUED,
                position=position,
                queued_at=datetime.now(timezone.utc),
                user_id=user_id,
            )

            self._queue.append(request)
            self._history[job_id] = request

            logger.info(
                "Petición encolada: %s (transacción: %s, posición: %d/%d)",
                job_id,
                transaction,
                position,
                self._max_size,
            )

            return position

    async def dequeue(self) -> Optional[QueueRequest]:
        """
        Extrae la siguiente petición de la cola para procesarla.

        Returns:
            La petición más antigua en estado QUEUED, o None si la cola está vacía.
        """
        async with self._lock:
            for i, request in enumerate(self._queue):
                if request.status == QueueJobStatus.QUEUED:
                    request.status = QueueJobStatus.PROCESSING
                    request.started_at = datetime.now(timezone.utc)
                    request.position = 0

                    # Actualizar posiciones de las demás peticiones
                    self._update_positions()

                    logger.info(
                        "Petición dequeueada: %s (transacción: %s)",
                        request.job_id,
                        request.transaction,
                    )
                    return request

            return None

    async def cancel(self, job_id: str) -> bool:
        """
        Cancela una petición en la cola.

        Solo se pueden cancelar peticiones en estado QUEUED.

        Args:
            job_id: ID de la petición a cancelar.

        Returns:
            True si se canceló exitosamente, False si no se pudo cancelar.

        Raises:
            KeyError: Si la petición no existe.
        """
        async with self._lock:
            # Buscar en la cola activa
            for request in self._queue:
                if request.job_id == job_id:
                    if request.status != QueueJobStatus.QUEUED:
                        logger.warning(
                            "No se puede cancelar petición %s: estado %s",
                            job_id,
                            request.status.value,
                        )
                        return False

                    request.status = QueueJobStatus.CANCELLED
                    request.completed_at = datetime.now(timezone.utc)
                    request.position = 0

                    # Remover de la cola activa
                    self._queue.remove(request)
                    self._update_positions()

                    logger.info("Petición cancelada: %s", job_id)
                    return True

            # Verificar en historial (ya no está en cola activa)
            if job_id in self._history:
                request = self._history[job_id]
                if request.status != QueueJobStatus.QUEUED:
                    logger.warning(
                        "No se puede cancelar petición %s: estado %s (ya no está en cola)",
                        job_id,
                        request.status.value,
                    )
                    return False

            raise KeyError(f"Petición {job_id} no encontrada")

    async def get_status(self, job_id: str) -> Optional[QueueStatus]:
        """
        Retorna el estado de una petición en la cola.

        Args:
            job_id: ID de la petición.

        Returns:
            QueueStatus con posición y estado, o None si no existe.
        """
        async with self._lock:
            # Buscar en la cola activa
            for request in self._queue:
                if request.job_id == job_id:
                    if request.status == QueueJobStatus.QUEUED:
                        # Calcular posición solo entre peticiones QUEUED
                        position = sum(
                            1
                            for r in self._queue
                            if r.status == QueueJobStatus.QUEUED
                            and self._queue.index(r) < self._queue.index(request)
                        ) + 1
                        estimated_wait = position * self._execution_timeout
                    else:
                        position = 0
                        estimated_wait = 0

                    return QueueStatus(
                        job_id=job_id,
                        position=position,
                        estimated_wait=estimated_wait,
                        status=request.status,
                    )

            # Buscar en historial
            if job_id in self._history:
                request = self._history[job_id]
                return QueueStatus(
                    job_id=job_id,
                    position=0,
                    estimated_wait=0,
                    status=request.status,
                )

            return None

    async def get_stats(self) -> QueueStats:
        """
        Retorna estadísticas actuales de la cola.

        Returns:
            QueueStats con conteos por estado.
        """
        async with self._lock:
            queued = sum(
                1
                for r in self._queue
                if r.status == QueueJobStatus.QUEUED
            )
            processing = sum(
                1
                for r in self._queue
                if r.status == QueueJobStatus.PROCESSING
            )

            # Contar del historial (excluyendo los que están en la cola activa)
            active_ids = {r.job_id for r in self._queue}
            completed = sum(
                1
                for jid, r in self._history.items()
                if r.status == QueueJobStatus.COMPLETED
                and jid not in active_ids
            )
            failed = sum(
                1
                for jid, r in self._history.items()
                if r.status == QueueJobStatus.FAILED
                and jid not in active_ids
            )
            cancelled = sum(
                1
                for jid, r in self._history.items()
                if r.status == QueueJobStatus.CANCELLED
                and jid not in active_ids
            )

            return QueueStats(
                total_queued=queued,
                total_processing=processing,
                total_completed=completed,
                total_failed=failed,
                total_cancelled=cancelled,
                max_queue_size=self._max_size,
            )

    async def mark_completed(
        self, job_id: str, results: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Marca una petición como completada.

        Args:
            job_id: ID de la petición.
            results: Resultados de la ejecución (opcional).
        """
        async with self._lock:
            # Remover de la cola activa si está ahí
            self._queue = [r for r in self._queue if r.job_id != job_id]

            if job_id in self._history:
                self._history[job_id].status = QueueJobStatus.COMPLETED
                self._history[job_id].completed_at = datetime.now(timezone.utc)
                self._history[job_id].position = 0

            self._update_positions()

            logger.info("Petición completada: %s", job_id)

    async def mark_failed(
        self, job_id: str, error_message: str
    ) -> None:
        """
        Marca una petición como fallida.

        Args:
            job_id: ID de la petición.
            error_message: Mensaje de error.
        """
        async with self._lock:
            # Remover de la cola activa si está ahí
            self._queue = [r for r in self._queue if r.job_id != job_id]

            if job_id in self._history:
                self._history[job_id].status = QueueJobStatus.FAILED
                self._history[job_id].completed_at = datetime.now(timezone.utc)
                self._history[job_id].error_message = error_message
                self._history[job_id].position = 0

            self._update_positions()

            logger.error("Petición fallida: %s - %s", job_id, error_message)

    async def process_with_retries(
        self,
        job_id: str,
        func: Callable[..., Coroutine[Any, Any, Any]],
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Ejecuta una función con reintentos automáticos.

        Reintenta solo en errores transitorios (timeout, conexión).
        Errores de negocio NO se reintentan.

        Args:
            job_id: ID de la petición (para actualizar estado).
            func: Función async a ejecutar.
            *args, **kwargs: Argumentos para la función.

        Returns:
            Resultado de la función.

        Raises:
            Exception: Si todos los reintentos fallan.
        """
        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                logger.info(
                    "Ejecutando petición %s (intento %d/%d)",
                    job_id,
                    attempt + 1,
                    self._max_retries + 1,
                )

                # Aplicar timeout
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self._execution_timeout,
                )
                return result

            except asyncio.TimeoutError as e:
                last_error = e
                logger.warning(
                    "Timeout en petición %s (intento %d/%d): %s",
                    job_id,
                    attempt + 1,
                    self._max_retries + 1,
                    str(e),
                )

            except TRANSIENT_ERRORS as e:
                last_error = e
                logger.warning(
                    "Error transitorio en petición %s (intento %d/%d): %s",
                    job_id,
                    attempt + 1,
                    self._max_retries + 1,
                    str(e),
                )

            except Exception as e:
                # Error de negocio - no reintentar
                logger.error(
                    "Error de negocio en petición %s: %s",
                    job_id,
                    str(e),
                )
                raise

        # Agotados los reintentos
        error_msg = f"Agotados los reintentos ({self._max_retries}): {last_error}"
        logger.error("Petición %s fallida definitivamente: %s", job_id, error_msg)
        raise Exception(error_msg)

    def _update_positions(self) -> None:
        """Actualiza las posiciones de las peticiones en la cola."""
        for i, request in enumerate(self._queue):
            if request.status == QueueJobStatus.QUEUED:
                request.position = i + 1
            else:
                request.position = 0

    async def clear(self) -> None:
        """Limpia la cola y el historial (útil para tests)."""
        async with self._lock:
            self._queue.clear()
            self._history.clear()
            logger.info("Cola de peticiones limpiada")


# Instancia global de la cola de peticiones
request_queue = RequestQueue()
