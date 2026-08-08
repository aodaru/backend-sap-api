"""
Configuración de tests - Fixtures compartidos.

Proporciona fixtures reutilizables para toda la suite de tests,
incluyendo el cliente de prueba FastAPI.
"""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    """
    Fixture que retorna un cliente de prueba FastAPI.

    Scope: module - se crea una vez por módulo de test para mejor rendimiento.

    Returns:
        TestClient: Cliente HTTP para hacer requests contra la app.
    """
    return TestClient(app)


@pytest.fixture(scope="module")
def valid_api_key() -> str:
    """
    Fixture que retorna una API key válida para tests.

    Returns:
        str: API key de prueba.
    """
    return "mi-api-key-secreta"
