"""
Backend API - Automatización SAP GUI.

FastAPI principal que sirve como punto de entrada de la aplicación.
Expone endpoints REST para automatizar transacciones SAP (ME12, VK12).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from dependencies import verify_api_key
from routers.condiciones import router as condiciones_router
from routers.costos import router as costos_router
from routers.health import router as health_router
from routers.logs import router as logs_router
from routers.queue import router as queue_router
from services.logging_service import audit_logger


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona el ciclo de vida de la aplicación.

    Se ejecuta al iniciar y al cerrar el servidor. Útil para
    inicializar conexiones, limpiar recursos y gestionar logs.
    """
    # Startup
    settings = get_settings()
    print(f"🚀 Backend API iniciado - SAP System: {settings.sap_system}")

    # Limpiar logs antiguos al iniciar
    removed = audit_logger.cleanup_old_logs()
    if removed > 0:
        print(f"🗑️  Logs antiguos eliminados: {removed} archivos")

    audit_logger.log_error(
        context="startup",
        message=f"Backend API iniciado - SAP System: {settings.sap_system}",
    )

    yield

    # Shutdown
    audit_logger.log_error(
        context="shutdown",
        message="Backend API cerrado",
    )
    print("🛑 Backend API cerrado")


# Crear la app FastAPI
app = FastAPI(
    title="Backend API - Automatización SAP",
    description=(
        "API REST para ejecutar transacciones SAP (ME12, VK12) "
        "mediante scripts automatizados. Requiere autenticación por API Key."
    ),
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configurar CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(health_router, prefix="/api")
app.include_router(costos_router, prefix="/api/costos")
app.include_router(condiciones_router, prefix="/api/condiciones")
app.include_router(queue_router, prefix="/api/queue")
app.include_router(logs_router, prefix="/api/logs")


@app.get("/", tags=["General"])
async def root(
    _api_key: str = Depends(verify_api_key),
):
    """
    Endpoint raíz.

    Retorna información básica de la API.

    Requiere autenticación via header X-API-Key.
    """
    return {
        "message": "Backend API - Automatización SAP",
        "docs": "/docs",
        "health": "/api/health",
    }


def run_server() -> None:
    """Inicia Uvicorn usando la configuración del servidor."""
    import uvicorn

    uvicorn.run(
        "main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    run_server()
