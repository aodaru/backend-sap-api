"""
Router de Condiciones - VK12.

Endpoints para gestionar la transacción SAP VK12
(modificación masiva de condiciones de precio).
"""

import io
import json
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse

from dependencies import verify_api_key
from models.responses import (
    CondicionesExecuteRequest,
    CondicionesExecuteResponse,
    CondicionesStatusResponse,
    CondicionesUploadResponse,
    JobStatus,
    ValidationDetail,
)
from services.condiciones_service import (
    execute_vk12,
    get_template_path,
    validate_excel,
)
from services.costos_service import job_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Condiciones"])


@router.get("/template")
async def get_template(
    _api_key: str = Depends(verify_api_key),
):
    """
    Descarga el template Excel para condiciones VK12.

    Retorna un archivo Excel con las 9 columnas requeridas para
    la transacción VK12 (modificación masiva de condiciones).

    Requiere autenticación via header X-API-Key.
    """
    template_path = get_template_path()

    if not template_path.exists():
        # Crear template básico si no existe
        try:
            import openpyxl

            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "VK12 Condiciones"

            headers = [
                "MATERIAL",
                "UNIDAD_DE_MEDIDA",
                "IMPORTE",
                "GRUPO_ARTICULO",
                "ORG_VENTA",
                "CAN_DISTR",
                "SECTOR",
                "RAMO",
                "TIPO_MODIFICACION",
            ]
            ws.append(headers)

            buffer = io.BytesIO()
            wb.save(buffer)
            buffer.seek(0)

            return StreamingResponse(
                buffer,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": "attachment; filename=condiciones_template.xlsx"
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
                "Content-Disposition": "attachment; filename=condiciones_template.xlsx"
            },
        )
    except Exception as e:
        logger.error("Error al leer template: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al descargar template",
        )


@router.post("/upload", response_model=CondicionesUploadResponse)
async def upload_condiciones(
    file: UploadFile,
    _api_key: str = Depends(verify_api_key),
):
    """
    Sube y valida un archivo Excel de condiciones VK12.

    El archivo debe contener las 9 columnas del template y los datos
    a procesar en la transacción VK12.

    Requiere autenticación via header X-API-Key.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe ser un Excel (.xlsx o .xls)",
        )

    is_valid, validations, rows_data = await validate_excel(file)

    return CondicionesUploadResponse(
        filename=file.filename,
        row_count=len(rows_data),
        valid=is_valid,
        validations=validations,
    )


@router.post(
    "/execute",
    response_model=CondicionesExecuteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def execute_condiciones(
    file: UploadFile,
    credentials: str = Form(...),
    _api_key: str = Depends(verify_api_key),
):
    """
    Ejecuta la transacción VK12 con los datos del archivo y credenciales SAP.

    Crea un job y retorna su ID para consultas posteriores.
    El archivo debe ser válido (usar /upload para validar primero).

    Las credenciales SAP se envían como un campo de formulario JSON con
    la estructura: {"system": "ERQ", "mandt": "200", "username": "...",
    "password": "...", "language": "ES"}.

    Requiere autenticación via header X-API-Key.
    """
    if not file.filename or not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El archivo debe ser un Excel (.xlsx o .xls)",
        )

    # Parsear y validar credenciales con Pydantic
    try:
        creds_data = json.loads(credentials) if isinstance(credentials, str) else credentials
        parsed_credentials = CondicionesExecuteRequest(**creds_data)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Credenciales inválidas: {e}",
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
    await execute_vk12(
        rows_data,
        job_id,
        credentials=parsed_credentials.model_dump(),
    )

    return CondicionesExecuteResponse(
        job_id=job_id,
        status=JobStatus.COMPLETED,
        message="VK12 ejecutado exitosamente",
    )


@router.get("/status/{job_id}", response_model=CondicionesStatusResponse)
async def get_status(
    job_id: str,
    _api_key: str = Depends(verify_api_key),
):
    """
    Consulta el estado de un job de condiciones VK12.

    Retorna el progreso y resultados del job cuando está completado.

    Requiere autenticación via header X-API-Key.
    """
    job = job_manager.get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} no encontrado",
        )

    return CondicionesStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=job["progress"],
        results=job["results"],
    )
