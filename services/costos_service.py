"""
Servicio de Costos - ME12.

Implementa la lógica de negocio para la transacción SAP ME12
(modificación de precios de material).
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import UploadFile

from models.responses import JobStatus, ValidationDetail

# Columnas requeridas en el template Excel
REQUIRED_COLUMNS = [
    "Material",
    "Proveedor",
    "Org_Compras",
    "Tipo_Info",
    "Tipo_Condicion",
    "Nuevo_Precio",
    "Moneda",
    "Unidad_Precio",
    "Unidad_Medida",
    "Valido_Desde",
    "Valido_Hasta",
]


class JobManager:
    """Gestiona jobs en memoria para ejecución de transacciones SAP."""

    def __init__(self) -> None:
        self._jobs: Dict[str, Dict[str, Any]] = {}

    def create_job(self) -> str:
        """Crea un nuevo job y retorna su ID."""
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "progress": 0,
            "results": None,
            "created_at": datetime.utcnow().isoformat(),
        }
        return job_id

    def update_job(
        self,
        job_id: str,
        status: JobStatus,
        progress: int = 0,
        results: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Actualiza el estado de un job."""
        if job_id not in self._jobs:
            raise KeyError(f"Job {job_id} not found")
        self._jobs[job_id]["status"] = status
        self._jobs[job_id]["progress"] = progress
        if results is not None:
            self._jobs[job_id]["results"] = results

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retorna el estado de un job o None si no existe."""
        return self._jobs.get(job_id)


# Instancia global del JobManager
job_manager = JobManager()


def get_template_path() -> Path:
    """Retorna la ruta al template Excel de costos."""
    return Path(__file__).parent.parent / "templates" / "costos_template.xlsx"


async def validate_excel(
    file: UploadFile,
) -> Tuple[bool, List[ValidationDetail], List[Dict[str, Any]]]:
    """
    Valida un archivo Excel de costos.

    Args:
        file: Archivo Excel subido por el usuario.

    Returns:
        Tupla con (es_válido, lista_de_errores, datos_parseados).
    """
    try:
        import openpyxl
    except ImportError:
        raise RuntimeError("openpyxl no está instalado")

    errors: List[ValidationDetail] = []
    rows_data: List[Dict[str, Any]] = []

    try:
        content = await file.read()
        import io

        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True)
        ws = wb.active

        if ws is None:
            errors.append(
                ValidationDetail(row=0, field="sheet", error="El archivo no tiene hojas")
            )
            return False, errors, []

        # Leer headers
        headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]
        headers = [h for h in headers if h is not None]

        # Validar columnas requeridas
        missing_columns = [col for col in REQUIRED_COLUMNS if col not in headers]
        if missing_columns:
            errors.append(
                ValidationDetail(
                    row=1,
                    field="columns",
                    error=f"Columnas faltantes: {', '.join(missing_columns)}",
                )
            )
            return False, errors, []

        # Validar filas de datos
        for row_idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            if all(cell is None for cell in row):
                continue  # Saltar filas vacías

            row_dict = dict(zip(headers, row))
            rows_data.append(row_dict)

            # Validar que no haya campos vacíos
            for col in REQUIRED_COLUMNS:
                if col in row_dict and row_dict[col] is None:
                    errors.append(
                        ValidationDetail(
                            row=row_idx, field=col, error="Campo requerido vacío"
                        )
                    )

            # Validar tipos numéricos
            if "Nuevo_Precio" in row_dict and row_dict["Nuevo_Precio"] is not None:
                try:
                    float(row_dict["Nuevo_Precio"])
                except (ValueError, TypeError):
                    errors.append(
                        ValidationDetail(
                            row=row_idx,
                            field="Nuevo_Precio",
                            error="Debe ser un número",
                        )
                    )

        wb.close()

        is_valid = len(errors) == 0
        return is_valid, errors, rows_data

    except Exception as e:
        errors.append(
            ValidationDetail(row=0, field="file", error=f"Error al leer archivo: {e!s}")
        )
        return False, errors, []


async def execute_me12(
    file_data: List[Dict[str, Any]], job_id: str
) -> Dict[str, Any]:
    """
    Ejecuta la transacción SAP ME12 con los datos proporcionados.

    En producción, esta función interactuaría con SAP GUI via win32com.
    En tests, se puede mockear esta función.

    Args:
        file_data: Lista de diccionarios con los datos del Excel.
        job_id: ID del job en ejecución.

    Returns:
        Diccionario con los resultados de la ejecución.
    """
    job_manager.update_job(job_id, JobStatus.PROCESSING, progress=10)

    # TODO: Implementar integración real con SAP GUI
    # Por ahora retorna mock de éxito
    job_manager.update_job(
        job_id,
        JobStatus.COMPLETED,
        progress=100,
        results={
            "processed": len(file_data),
            "successful": len(file_data),
            "failed": 0,
            "message": "ME12 ejecutado exitosamente",
        },
    )

    return {
        "processed": len(file_data),
        "successful": len(file_data),
        "failed": 0,
    }
