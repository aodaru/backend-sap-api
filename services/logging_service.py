"""
Servicio de Logging y Auditoría.

Implementa el sistema de logs estructurado (JSON) para auditoría
de todas las ejecuciones SAP y operaciones sensibles del backend.
Los logs se almacenan en archivos JSONL con rotación diaria y por tamaño.
"""

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.log_models import (
    AuditLogEntry,
    ErrorDetail,
    LogQueryParams,
    LogResponse,
    LogLevel,
    LogStatus,
)

# Nivel de log custom para auditoría (entre INFO=20 y WARNING=30)
AUDIT_LEVEL = 25
logging.addLevelName(AUDIT_LEVEL, "AUDIT")


class AuditLogger:
    """
    Logger de auditoría que escribe logs estructurados en archivos JSON.

    Maneja rotación diaria de archivos, segmentación por tamaño,
    thread-safe writes, y limpieza automática de logs antiguos.
    """

    def __init__(
        self,
        log_dir: str = "logs",
        retention_days: int = 90,
        max_file_size_mb: float = 10,
    ) -> None:
        """
        Inicializa el AuditLogger.

        Args:
            log_dir: Directorio donde se almacenan los archivos de log.
            retention_days: Número de días de retención de logs.
            max_file_size_mb: Tamaño máximo por archivo de log en MB.
        """
        self._log_dir = Path(log_dir)
        self._retention_days = retention_days
        self._max_size_bytes = max_file_size_mb * 1024 * 1024
        self._lock = threading.Lock()

        # Crear directorio si no existe
        self._log_dir.mkdir(parents=True, exist_ok=True)

        # Estado del archivo actual
        self._current_date: Optional[str] = None
        self._current_file_path: Optional[Path] = None
        self._current_file = None
        self._current_segment: int = 0

    def _get_date_str(self) -> str:
        """Retorna la fecha actual como string YYYY-MM-DD en UTC."""
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _build_file_path(self, date_str: str, segment: int) -> Path:
        """
        Construye la ruta del archivo de log para una fecha y segmento dados.

        Args:
            date_str: Fecha en formato YYYY-MM-DD.
            segment: Número de segmento (0 = archivo principal).

        Returns:
            Ruta completa al archivo de log.
        """
        if segment == 0:
            return self._log_dir / f"audit-{date_str}.json"
        return self._log_dir / f"audit-{date_str}.{segment}.json"

    def _find_latest_segment(self, date_str: str) -> int:
        """
        Busca el último segmento existente para una fecha dada.

        Args:
            date_str: Fecha en formato YYYY-MM-DD.

        Returns:
            Número del último segmento existente (0 si no hay archivos).
        """
        latest = 0
        for seg in range(1000):  # Límite arbitrario para evitar loops infinitos
            path = self._build_file_path(date_str, seg)
            if path.exists():
                latest = seg
            else:
                break
        return latest

    def _open_new_file(self, date_str: str, segment: int) -> None:
        """
        Abre un nuevo archivo de log para escritura.

        Cierra el archivo anterior si estaba abierto.

        Args:
            date_str: Fecha en formato YYYY-MM-DD.
            segment: Número de segmento.
        """
        self._close_current_file()
        path = self._build_file_path(date_str, segment)
        self._current_file = open(path, "a", encoding="utf-8")
        self._current_date = date_str
        self._current_file_path = path
        self._current_segment = segment

    def _close_current_file(self) -> None:
        """Cierra el archivo de log actual si está abierto."""
        if self._current_file is not None:
            try:
                self._current_file.flush()
                self._current_file.close()
            except OSError:
                pass
            self._current_file = None

    def _rotate_if_needed(self) -> None:
        """
        Verifica si se necesita rotar el archivo de log.

        Rota si:
        1. No hay archivo abierto (primera escritura).
        2. La fecha cambió (nuevo día → nuevo archivo).
        3. El archivo actual excede max_size_bytes (nuevo segmento).
        """
        today = self._get_date_str()

        # Caso 1: No hay archivo abierto
        if self._current_file is None:
            segment = self._find_latest_segment(today)
            # Si el último archivo existe y es mayor al máximo, empezar nuevo segmento
            if segment > 0:
                last_path = self._build_file_path(today, segment)
                if last_path.stat().st_size >= self._max_size_bytes:
                    segment += 1
            elif segment == 0:
                main_path = self._build_file_path(today, 0)
                if main_path.exists() and main_path.stat().st_size >= self._max_size_bytes:
                    segment = 1
            self._open_new_file(today, segment)
            return

        # Caso 2: La fecha cambió → nuevo archivo del día
        if today != self._current_date:
            self._open_new_file(today, 0)
            return

        # Caso 3: Archivo actual excede el tamaño máximo → nuevo segmento
        if self._current_file_path is not None:
            try:
                current_size = self._current_file_path.stat().st_size
                if current_size >= self._max_size_bytes:
                    self._open_new_file(today, self._current_segment + 1)
            except OSError:
                pass

    def _write_log(self, log_data: Dict[str, Any]) -> None:
        """
        Escribe una entrada de log de forma thread-safe.

        Args:
            log_data: Diccionario con los datos del log.
        """
        with self._lock:
            self._rotate_if_needed()
            assert self._current_file is not None  # _rotate_if_needed garantiza archivo abierto
            line = json.dumps(log_data, ensure_ascii=False, default=str) + "\n"
            self._current_file.write(line)
            self._current_file.flush()

    def log_execution(
        self,
        job_id: str,
        user_id: str,
        transaction: str,
        status: str,
        duration: float,
        sap_login_success: bool,
        rows_total: int,
        rows_success: int,
        rows_failed: int,
        errors: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Registra un log de ejecución SAP.

        Args:
            job_id: ID del job ejecutado.
            user_id: Identificador del usuario SAP.
            transaction: Tipo de transacción (ME12, VK12).
            status: Resultado (success, error, cancelled).
            duration: Duración total en segundos.
            sap_login_success: Si el login a SAP fue exitoso.
            rows_total: Total de filas procesadas.
            rows_success: Filas procesadas exitosamente.
            rows_failed: Filas con error.
            errors: Lista de errores detallados.
            metadata: Información adicional (filename, org_compras, etc.).
        """
        error_details = []
        if errors:
            for err in errors:
                error_details.append(
                    ErrorDetail(
                        row=err.get("row", 0),
                        material=err.get("material", ""),
                        proveedor=err.get("proveedor", "N/A"),
                        message=err.get("message", ""),
                    ).model_dump()
                )

        log_data = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=LogLevel.AUDIT,
            event_type="execution",
            user_id=user_id,
            transaction=transaction,
            job_id=job_id,
            status=LogStatus(status),
            duration_seconds=round(duration, 3),
            sap_login_success=sap_login_success,
            rows_total=rows_total,
            rows_success=rows_success,
            rows_failed=rows_failed,
            errors=error_details,
            metadata=metadata or {},
        ).model_dump()

        self._write_log(log_data)

    def log_auth(
        self,
        user_id: str,
        success: bool,
        ip_address: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        """
        Registra un intento de autenticación.

        Args:
            user_id: Identificador del usuario que intentó autenticarse.
            success: Si la autenticación fue exitosa.
            ip_address: Dirección IP del cliente.
            message: Mensaje descriptivo del resultado.
        """
        log_data = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=LogLevel.AUDIT if success else LogLevel.ERROR,
            event_type="auth",
            user_id=user_id,
            status=LogStatus.SUCCESS if success else LogStatus.ERROR,
            ip_address=ip_address,
            message=message or ("Autenticación exitosa" if success else "Autenticación fallida"),
        ).model_dump()

        self._write_log(log_data)

    def log_upload(
        self,
        user_id: str,
        filename: str,
        row_count: int,
        valid: bool,
        validations: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """
        Registra la subida de un archivo Excel.

        Args:
            user_id: Identificador del usuario.
            filename: Nombre del archivo subido.
            row_count: Número de filas procesadas.
            valid: Si el archivo es válido.
            validations: Detalles de errores de validación.
        """
        log_data = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=LogLevel.AUDIT if valid else LogLevel.ERROR,
            event_type="upload",
            user_id=user_id,
            status=LogStatus.SUCCESS if valid else LogStatus.ERROR,
            rows_total=row_count,
            metadata={
                "filename": filename,
                "valid": valid,
                "validations": validations or [],
            },
        ).model_dump()

        self._write_log(log_data)

    def log_error(
        self,
        context: str,
        message: str,
        exception: Optional[Exception] = None,
    ) -> None:
        """
        Registra un error del sistema.

        Args:
            context: Contexto donde ocurrió el error.
            message: Mensaje descriptivo del error.
            exception: Excepción original (opcional).
        """
        error_info = {}
        if exception:
            error_info = {
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
            }

        log_data = AuditLogEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            level=LogLevel.ERROR,
            event_type="error",
            user_id="system",
            message=message,
            metadata={
                "context": context,
                **error_info,
            },
        ).model_dump()

        self._write_log(log_data)

    def cleanup_old_logs(self) -> int:
        """
        Elimina archivos de log más antiguos que retention_days.

        Returns:
            Número de archivos eliminados.
        """
        cutoff = datetime.now(timezone.utc).timestamp() - (
            self._retention_days * 86400
        )
        removed = 0

        with self._lock:
            # Cerrar el archivo actual si pertenece a la fecha a limpiar
            if self._current_file_path is not None:
                try:
                    file_mtime = self._current_file_path.stat().st_mtime
                    if file_mtime < cutoff:
                        self._close_current_file()
                except OSError:
                    pass

            for log_file in self._log_dir.glob("audit-*.json"):
                if log_file.name == ".gitkeep":
                    continue
                try:
                    file_mtime = log_file.stat().st_mtime
                    if file_mtime < cutoff:
                        log_file.unlink()
                        removed += 1
                except OSError:
                    pass  # Ignorar errores al eliminar archivos

        return removed

    def get_logs(self, filters: LogQueryParams) -> LogResponse:
        """
        Consulta logs con filtros y paginación.

        Lee todos los archivos de log y filtra en memoria.
        Para producción con muchos logs, se debería usar una BD.

        Args:
            filters: Parámetros de filtro y paginación.

        Returns:
            Respuesta paginada con los logs que coinciden.
        """
        all_entries: List[AuditLogEntry] = []

        # Determinar archivos a leer según rango de fechas
        files_to_read = self._get_files_for_range(
            filters.date_from, filters.date_to
        )

        for log_file in files_to_read:
            entries = self._read_log_file(log_file)
            all_entries.extend(entries)

        # Aplicar filtros
        filtered = self._apply_filters(all_entries, filters)

        # Ordenar por timestamp descendente
        filtered.sort(key=lambda e: e.timestamp, reverse=True)

        total = len(filtered)

        # Aplicar paginación
        paginated = filtered[filters.offset : filters.offset + filters.limit]

        return LogResponse(
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            logs=paginated,
        )

    def get_logs_by_job_id(self, job_id: str) -> List[AuditLogEntry]:
        """
        Retorna logs asociados a un job_id específico.

        Args:
            job_id: ID del job a buscar.

        Returns:
            Lista de entradas de log para ese job.
        """
        all_entries: List[AuditLogEntry] = []

        for log_file in self._log_dir.glob("audit-*.json"):
            if log_file.name == ".gitkeep":
                continue
            entries = self._read_log_file(log_file)
            for entry in entries:
                if entry.job_id == job_id:
                    all_entries.append(entry)

        all_entries.sort(key=lambda e: e.timestamp, reverse=True)
        return all_entries

    def _get_files_for_range(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
    ) -> List[Path]:
        """
        Retorna archivos de log dentro del rango de fechas.

        Soporta archivos con formato:
        - audit-YYYY-MM-DD.json (segmento 0)
        - audit-YYYY-MM-DD.N.json (segmento N)

        Args:
            date_from: Fecha inicio (YYYY-MM-DD) o None.
            date_to: Fecha fin (YYYY-MM-DD) o None.

        Returns:
            Lista de archivos .json que podrían tener datos en el rango.
        """
        files = []
        for log_file in sorted(self._log_dir.glob("audit-*.json")):
            if log_file.name == ".gitkeep":
                continue
            # Extraer fecha del nombre del archivo
            # Formato: audit-YYYY-MM-DD.json o audit-YYYY-MM-DD.N.json
            try:
                # Remover prefijo "audit-" y extensión ".json"
                name_without_prefix = log_file.name[len("audit-"):]  # "YYYY-MM-DD.json" o "YYYY-MM-DD.N.json"
                name_without_ext = name_without_prefix[:-5]  # "YYYY-MM-DD" o "YYYY-MM-DD.N"

                # Separar fecha del segmento (si existe)
                date_part = name_without_ext.split(".")[0]
                file_date = datetime.strptime(date_part, "%Y-%m-%d").date()

                if date_from:
                    from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
                    if file_date < from_date:
                        continue
                if date_to:
                    to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
                    if file_date > to_date:
                        continue

                files.append(log_file)
            except (ValueError, IndexError):
                continue

        return files

    def _read_log_file(self, file_path: Path) -> List[AuditLogEntry]:
        """
        Lee un archivo de log JSON y retorna las entradas válidas.

        Args:
            file_path: Ruta al archivo de log.

        Returns:
            Lista de entradas de log parseadas.
        """
        entries = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        entry = AuditLogEntry(**data)
                        entries.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue  # Líneas inválidas se ignoran
        except OSError:
            pass
        return entries

    def _apply_filters(
        self,
        entries: List[AuditLogEntry],
        filters: LogQueryParams,
    ) -> List[AuditLogEntry]:
        """
        Aplica los filtros de consulta a una lista de entradas.

        Args:
            entries: Lista de entradas a filtrar.
            filters: Parámetros de filtro.

        Returns:
            Lista filtrada de entradas.
        """
        result = entries

        if filters.transaction:
            result = [
                e for e in result if e.transaction == filters.transaction
            ]

        if filters.user_id:
            result = [
                e for e in result if e.user_id == filters.user_id
            ]

        if filters.status:
            result = [
                e for e in result if e.status == filters.status
            ]

        if filters.date_from:
            from_date = datetime.strptime(filters.date_from, "%Y-%m-%d").date()
            result = [
                e
                for e in result
                if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")).date()
                >= from_date
            ]

        if filters.date_to:
            to_date = datetime.strptime(filters.date_to, "%Y-%m-%d").date()
            result = [
                e
                for e in result
                if datetime.fromisoformat(e.timestamp.replace("Z", "+00:00")).date()
                <= to_date
            ]

        return result


# Instancia global del AuditLogger
from config import get_settings

_settings = get_settings()
audit_logger = AuditLogger(
    log_dir=_settings.log_dir,
    retention_days=_settings.log_retention_days,
    max_file_size_mb=_settings.log_max_file_size_mb,
)
