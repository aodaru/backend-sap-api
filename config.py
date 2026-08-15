"""
Configuración centralizada del Backend API.

Gestiona variables de entorno y configuraciones del proyecto usando pydantic-settings.
"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración del backend SAP.

    Lee las variables de entorno desde el archivo .env y las convierte
    en atributos tipados con valores por defecto.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # API Keys para autenticación (separadas por coma)
    api_keys: str = ""

    # CORS
    cors_origins: str = "http://localhost:4321,http://localhost:8080"

    # SAP Configuration
    sap_system: str = "PRD"
    sap_mandant: str = "300"
    sap_lang: str = "ES"
    sap_connection_name: str = ""
    sap_session_index: int = 0
    sap_integration_enabled: bool = False

    # Servidor
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False

    # Cola de peticiones SAP
    sap_execution_timeout: int = 120  # Timeout en segundos por ejecución
    sap_queue_wait_timeout: int = 120  # Tiempo máximo esperando turno
    max_queue_size: int = 5  # Máximo de peticiones en cola
    max_retries: int = 2  # Reintentos en errores transitorios
    sap_retry_backoff: int = 1

    # Logging y Auditoría
    log_dir: str = "logs"  # Directorio donde se almacenan los logs de auditoría
    log_retention_days: int = 90  # Días de retención de archivos de log
    log_max_file_size_mb: int = 10  # Tamaño máximo por archivo de log (MB)
    log_level: str = "audit"  # Nivel de log por defecto (audit, info, error)

    @property
    def api_keys_list(self) -> List[str]:
        """Retorna la lista de API keys configuradas."""
        if not self.api_keys:
            return []
        return [key.strip() for key in self.api_keys.split(",") if key.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
        """Retorna la lista de orígenes CORS permitidos."""
        if not self.cors_origins:
            return []
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """
    Retorna la configuración singleton cacheada.

    Returns:
        Settings: Instancia de configuración con valores del .env
    """
    return Settings()
