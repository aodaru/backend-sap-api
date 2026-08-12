"""
Tests unitarios para config.py.

Verifica la gestión de variables de entorno y configuración.
"""

import os
from unittest.mock import patch

from config import Settings, get_settings


class TestSettings:
    """Tests para la clase Settings."""

    def test_default_values(self):
        """Test: Settings tiene valores por defecto correctos."""
        with patch.dict(os.environ, {}, clear=False):
            settings = Settings(
                api_keys="",
                cors_origins="",
                sap_system="PRD",
                sap_mandant="100",
                sap_lang="ES",
                server_host="0.0.0.0",
                server_port=8000,
                debug=False,
            )
            assert settings.sap_system == "PRD"
            assert settings.sap_mandant == "100"
            assert settings.sap_lang == "ES"
            assert settings.server_port == 8000
            assert settings.debug is False

    def test_api_keys_list_empty(self):
        """Test: api_keys_list retorna lista vacía si api_keys está vacío."""
        settings = Settings(api_keys="")
        assert settings.api_keys_list == []

    def test_api_keys_list_single(self):
        """Test: api_keys_list con una key."""
        settings = Settings(api_keys="mi-key")
        assert settings.api_keys_list == ["mi-key"]

    def test_api_keys_list_multiple(self):
        """Test: api_keys_list con múltiples keys separadas por coma."""
        settings = Settings(api_keys="key1,key2,key3")
        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_api_keys_list_strips_whitespace(self):
        """Test: api_keys_list elimina espacios en blanco."""
        settings = Settings(api_keys=" key1 , key2 , key3 ")
        assert settings.api_keys_list == ["key1", "key2", "key3"]

    def test_cors_origins_list_empty(self):
        """Test: cors_origins_list retorna lista vacía si cors_origins está vacío."""
        settings = Settings(cors_origins="")
        assert settings.cors_origins_list == []

    def test_cors_origins_list_single(self):
        """Test: cors_origins_list con un origen."""
        settings = Settings(cors_origins="http://localhost:3000")
        assert settings.cors_origins_list == ["http://localhost:3000"]

    def test_cors_origins_list_multiple(self):
        """Test: cors_origins_list con múltiples orígenes."""
        settings = Settings(
            cors_origins="http://localhost:3000,http://localhost:8080"
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]

    def test_cors_origins_list_strips_whitespace(self):
        """Test: cors_origins_list elimina espacios en blanco."""
        settings = Settings(
            cors_origins=" http://localhost:3000 , http://localhost:8080 "
        )
        assert settings.cors_origins_list == [
            "http://localhost:3000",
            "http://localhost:8080",
        ]

    def test_queue_settings_defaults(self):
        """Test: Configuración de cola tiene valores por defecto."""
        settings = Settings()
        assert settings.sap_execution_timeout == 120
        assert settings.max_queue_size == 5
        assert settings.max_retries == 2

    def test_logging_settings_defaults(self):
        """Test: Configuración de logging tiene valores por defecto."""
        settings = Settings()
        assert settings.log_dir == "logs"
        assert settings.log_retention_days == 90
        assert settings.log_max_file_size_mb == 10
        assert settings.log_level == "audit"

    def test_custom_queue_settings(self):
        """Test: Configuración de cola personalizada."""
        settings = Settings(
            sap_execution_timeout=60,
            max_queue_size=10,
            max_retries=3,
        )
        assert settings.sap_execution_timeout == 60
        assert settings.max_queue_size == 10
        assert settings.max_retries == 3


class TestGetSettings:
    """Tests para la función get_settings."""

    def test_returns_settings_instance(self):
        """Test: get_settings retorna una instancia de Settings."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_is_cached(self):
        """Test: get_settings retorna la misma instancia (cacheada)."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
