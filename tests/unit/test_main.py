"""Tests unitarios para el punto de entrada de la aplicación."""

from unittest.mock import patch

import main


def test_run_server_uses_configured_uvicorn_settings():
    """Uvicorn recibe el host, puerto y modo debug configurados."""
    with patch("uvicorn.run") as run:
        main.run_server()

    run.assert_called_once_with(
        "main:app",
        host=main.settings.server_host,
        port=main.settings.server_port,
        reload=main.settings.debug,
    )
