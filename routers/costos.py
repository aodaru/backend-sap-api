"""
Router de Costos - ME12.

Endpoints para gestionar la transacción SAP ME12
(modificación de precios de material).
"""

import io
import logging
import time
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from dependencies import verify_api_key
from models.responses import (
    CostosExecuteResponse,
    CostosStatusResponse,
    CostosUploadResponse,
    JobStatus,
    ValidationDetail,
)
from services.costos_service import (
    execute_me12,
    get_template_path,
    job_manager,
    validate_excel,
)
from services.logging_service import audit_logger
from services.sap_errors import operational_context, public_error

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Costos"])


@router.get("/template")
async def get_template(
    _api_key: str = Depends(verify_api_key),
):
    """
    Descarga el template Excel para costos.

    Retorna un archivo Excel con las columnas requeridas para
    la transacción ME12.

    Requiere autenticación via header X-API-Key.
    """
    template_path = get_template_path()

    if not template_path.exists():
        # Crear template básico si no existe
        try:
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Costos ME12"

            headers = [
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
            ws.append(headers)

            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=costos_template.xlsx"
                },
            )
        except ImportError:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="openpyxl no está instalado",
            )

    try:
        with open(template_path, "rb") as f:
            content = f.read()

        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": "attachment; filename=costos_template.xlsx"
            },
        )
    except Exception as e:
        logger.error("Error al leer template: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descargar template",
        )


@router.post("/upload", response_model=CostosUploadResponse)
async def upload_costos(
    file: UploadFile,
    _api_key: str = Depends(verify_api_key),
):
    """
    Sube y valida un archivo Excel de costos.

    El archivo debe contener las columnas del template y los datos
    a procesar en la transacción ME12.

    Requiere autenticación via header X-API-Key.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe ser un Excel (.xlsx o .xls)",
        )

    is_valid, validations, rows_data = await validate_excel(file)

    return CostosUploadResponse(
        filename=file.filename,
        row_count=len(rows_data),
        valid=is_valid,
        validations=validations,
    )


@router.post(
    "/execute",
    response_model=CostosExecuteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_costos(
    file: UploadFile,
    _api_key: str = Depends(verify_api_key),
):
    """
    Ejecuta la transacción ME12 con los datos del archivo.

    Crea un job y retorna su ID para consultas posteriores.
    El archivo debe ser válido (usar /upload para validar primero).

    Requiere autenticación via header X-API-Key.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe ser un Excel (.xlsx o .xls)",
        )

    is_valid, validations, rows_data = await validate_excel(file)

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": "Archivo inválido",
                "validations": [v.model_dump() for v in validations],
            },
        )

    job_id = job_manager.create_job()

    # Ejecutar en background (por ahora síncrono para MVP)
    start_time = time.time()
    safe_filename = file.filename.replace("\\", "/").rsplit("/", 1)[-1]
    try:
        await execute_me12(rows_data, job_id)
        duration = time.time() - start_time

        # Registrar log de auditoría exitoso
        audit_logger.log_execution(
            job_id=job_id,
            user_id="system",
            transaction="ME12",
            status="success",
            duration=duration,
            sap_login_success=True,
            rows_total=len(rows_data),
            rows_success=len(rows_data),
            rows_failed=0,
            errors=[],
            metadata={
                "filename": safe_filename,
            },
        )
    except ValueError as e:
        duration = time.time() - start_time

        # Registrar log de auditoría con error
        audit_logger.log_execution(
            job_id=job_id,
            user_id="system",
            transaction="ME12",
            status="error",
            duration=duration,
            sap_login_success=False,
            rows_total=len(rows_data),
            rows_success=0,
            rows_failed=len(rows_data),
            errors=[
                {
                    "row": 0,
                    "material": "",
                    "proveedor": "",
                    "message": "Cola llena: no hay capacidad disponible",
                }
            ],
            metadata={
                "filename": safe_filename,
            },
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Cola llena: no hay capacidad disponible",
        )
    except Exception as e:
        duration = time.time() - start_time
        message, http_status = public_error(e)
        context = operational_context(e)
        audit_logger.log_execution(
            job_id=job_id, user_id="system", transaction="ME12", status="error",
            duration=duration, sap_login_success=False, rows_total=len(rows_data), rows_success=0,
            rows_failed=len(rows_data), errors=[{"row": 0, "message": message}],
            metadata={"filename": file.filename.rsplit("\\", 1)[-1].rsplit("/", 1)[-1], **context},
            operational_code=str(context["operational_code"]),
        )
        raise HTTPException(status_code=http_status, detail=message)

    return CostosExecuteResponse(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        message="ME12 ejecutado exitosamente",
    )


@router.get("/status/{job_id}", response_model=CostosStatusResponse)
async def get_status(
    job_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """
    Consulta el estado de un job de costos.

    Retorna el progreso y resultados del job cuando está completado.

    Requiere autenticación via header X-API-Key.
    """
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} no encontrado",
        )

    return CostosStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        results=job["results"],
    )
