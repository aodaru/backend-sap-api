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
    sap_mandant: str = "100"
    sap_lang: str = "ES"

    # Servidor
    server_host: str = "0.0.0.0"
    server_port: int = 8000
    debug: bool = False

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
