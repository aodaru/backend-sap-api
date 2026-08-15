"""
Dependencias compartidas de FastAPI.

Define dependencias reutilizables como verificación de API Key.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader

from config import get_settings
from services.logging_service import audit_logger

# Header para API Key, auto_error=False para controlar el error manualmente
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    request: Request = None,
) -> str:
    """
    Verifica que la petición incluya una API Key válida.

    Extrae el header X-API-Key y lo valida contra las keys
    configuradas en variables de entorno. Registra cada intento
    de autenticación en el log de auditoría.

    Args:
        api_key: Valor del header X-API-Key (inyectado por FastAPI).
        request: Objeto Request de FastAPI para obtener la IP del cliente.

    Returns:
        str: La API Key válida si la verificación es exitosa.

    Raises:
        HTTPException: 401 si la key está ausente o es inválida.
    """
    settings = get_settings()

    # Obtener IP del cliente
    ip_address = None
    if request:
        ip_address = request.client.host if request.client else None

    if api_key is None:
        audit_logger.log_auth(
            user_id="unknown",
            success=False,
            ip_address=ip_address,
            message="API Key ausente",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required",
        )

    if api_key not in settings.api_keys_list:
        audit_logger.log_auth(
            user_id="unknown",
            success=False,
            ip_address=ip_address,
            message="API Key inválida",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    # Log de autenticación exitosa
    audit_logger.log_auth(
        user_id="authenticated",
        success=True,
        ip_address=ip_address,
        message="Autenticación exitosa",
    )

    return api_key
