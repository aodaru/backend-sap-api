"""
Backend API - Automatización SAP GUI.

FastAPI principal que sirve como punto de entrada de la aplicación.
Expone endpoints REST para automatizar transacciones SAP (ME12, VK12).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Gestiona el ciclo de vida de la aplicación.

    Se ejecuta al iniciar y al cerrar el servidor. Útil para
    inicializar conexiones o limpiar recursos.
    """
    # Startup
    settings = get_settings()
    print(f"🚀 Backend API iniciado - SAP System: {settings.sap_system}")
    yield
    # Shutdown
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


@app.get("/api/health", tags=["General"])
async def health_check():
    """
    Health check endpoint.

    Verifica que el servidor esté operativo.
    Retorna el estado del sistema y metadatos básicos.
    """
    return {
        "status": "ok",
        "service": "Backend API - Automatización SAP",
        "version": "0.1.0",
        "sap_system": settings.sap_system,
    }


@app.get("/", tags=["General"])
async def root():
    """
    Endpoint raíz.

    Retorna información básica de la API.
    """
    return {
        "message": "Backend API - Automatización SAP",
        "docs": "/docs",
        "health": "/api/health",
    }
