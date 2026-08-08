"""
Dependencias compartidas de FastAPI.

Define dependencias reutilizables como verificación de API Key.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from config import get_settings

# Header para API Key, auto_error=False para controlar el error manualmente
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def verify_api_key(api_key: str | None = Depends(api_key_header)) -> str:
    """
    Verifica que la petición incluya una API Key válida.

    Extrae el header X-API-Key y lo valida contra las keys
    configuradas en variables de entorno.

    Args:
        api_key: Valor del header X-API-Key (inyectado por FastAPI).

    Returns:
        str: La API Key válida si la verificación es exitosa.

    Raises:
        HTTPException: 401 si la key está ausente o es inválida.
    """
    settings = get_settings()

    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required",
        )

    if api_key not in settings.api_keys_list:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key",
        )

    return api_key
