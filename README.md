# Backend API - Automatización SAP

Backend centralizado para ejecutar flujos/scripts en SAP GUI mediante API REST, con autenticación por API Key.

## Estado Actual

**Fase 1 completada**: Estructura base del proyecto con FastAPI.

## Transacciones SAP Soportadas (Planeadas)

| Transacción SAP | Descripción |
|----------------|-------------|
| ME12 | Modificación masiva de precios - Info Records de compra |
| VK12 | Modificación masiva de condiciones de precio |

## Stack

- **FastAPI** - Framework async con docs automáticos (Swagger/ReDoc)
- **Pydantic** - Validación de models
- **python-multipart** - Uploads de archivos
- **pytest** - Testing
- **CORS** - Habilitado para frontends (Astro/Laravel)

## Estructura Actual (Fase 1)

```
backendPy/
├── main.py                  # FastAPI app principal
├── config.py                # Settings, API keys, env
├── requirements.txt         # Dependencias
├── .env.example             # Variables de entorno ejemplo
├── routers/                 # Endpoints (vacío - Fase 4/5)
├── services/                # Lógica de negocio (vacío - Fase 4/5)
├── models/                  # Pydantic models (vacío - Fase 4)
├── templates/               # Excel templates (vacío - Fase 4)
└── tests/
    ├── conftest.py          # Fixtures compartidos
    └── test_health.py       # Tests de health check
```

## Endpoints Actuales

### General

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Root endpoint |
| GET | `/api/health` | Health check |

### Endpoints Planeados (Fase 4-5)

#### Costos (ME12)
- `GET /api/costos/template` - Descargar template Excel
- `POST /api/costos/upload` - Upload + validación Excel
- `POST /api/costos/execute` - Ejecutar ME12 en SAP
- `GET /api/costos/status/{job_id}` - Estado de ejecución

#### Condiciones (VK12)
- `GET /api/condiciones/template` - Descargar template Excel
- `POST /api/condiciones/upload` - Upload + validación Excel
- `POST /api/condiciones/execute` - Ejecutar VK12 en SAP
- `GET /api/condiciones/status/{job_id}` - Estado de ejecución

## Variables de entorno (.env)

```env
# API Keys (separadas por coma)
API_KEYS=mi-key-secreta

# CORS (origins permitidos, separados por coma)
CORS_ORIGINS=http://localhost:4321,http://localhost:8000

# SAP
SAP_SYSTEM=PRD
SAP_MANDANT=100
SAP_LANG=ES

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=true
```

## Instalación

```bash
cd backendPy
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # editar con values reales
```

## Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Docs disponibles en: `http://localhost:8000/docs`

## Tests

```bash
# Todos los tests
pytest tests/ -v

# Con cobertura
pytest tests/ -v --cov=.

# Tests específicos
pytest tests/test_health.py -v
```

## Roadmap

Ver `specs/roadmap.md` para detalles completos de las fases:

1. **Fase 1** ✅ - Estructura base del proyecto
2. **Fase 2** - Sistema de autenticación
3. **Fase 3** - Health check y endpoints básicos
4. **Fase 4** - Endpoints para ME12 (Costos)
5. **Fase 5** - Endpoints para VK12 (Condiciones)
6. **Fase 6** - Sistema de cola de peticiones
7. **Fase 7** - Logging y auditoría
8. **Fase 8** - Testing y documentación
9. **Fase 9** - Integración con frontends

## Notas técnicas

- **Plataforma**: Windows obligatorio (SAP GUI requiere win32com)
- **Concurrencia**: Un solo proceso SAP a la vez (Fase 6 implementará cola)
- **Autenticación**: API Key via header `X-API-Key` (Fase 2)
- **Frontend**: Se desarrollará por separado en Astro/Laravel
