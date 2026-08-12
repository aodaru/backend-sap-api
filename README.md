# Backend API - Automatización SAP

Backend centralizado para ejecutar flujos/scripts en SAP GUI mediante API REST, con autenticación por API Key.

## Estado Actual

**Fase 8 completada**: Testing y documentación.

| Fase | Estado | Descripción |
|------|--------|-------------|
| 1 | ✅ | Estructura base del proyecto |
| 2 | ✅ | Sistema de autenticación (API Key) |
| 3 | ✅ | Health check y endpoints básicos |
| 4 | ✅ | Endpoints para ME12 (Costos) |
| 5 | ✅ | Endpoints para VK12 (Condiciones) |
| 6 | ✅ | Sistema de cola de peticiones |
| 7 | ✅ | Logging y auditoría |
| 8 | ✅ | Testing y documentación |
| 9 | 🔲 | Integración con frontends |

## Transacciones SAP Soportadas

| Transacción SAP | Descripción |
|----------------|-------------|
| ME12 | Modificación masiva de precios - Info Records de compra |
| VK12 | Modificación masiva de condiciones de precio |

## Stack

- **FastAPI** - Framework async con docs automáticos (Swagger/ReDoc)
- **Pydantic v2** - Validación de modelos con tipado estricto
- **python-multipart** - Uploads de archivos
- **openpyxl** - Procesamiento de Excel
- **pytest** - Testing con soporte async
- **pytest-cov** - Cobertura de código
- **CORS** - Habilitado para frontends (Astro/Laravel)

## Estructura del Proyecto

```
backendPy/
├── main.py                  # FastAPI app principal
├── config.py                # Settings (pydantic-settings)
├── dependencies.py          # Verificación API Key
├── requirements.txt         # Dependencias
├── pyproject.toml           # Config pytest/cobertura
├── .env.example             # Variables de entorno ejemplo
├── routers/                 # Endpoints REST
│   ├── health.py            # Health check (público)
│   ├── costos.py            # Endpoints ME12
│   ├── condiciones.py       # Endpoints VK12
│   ├── queue.py             # Cola de peticiones
│   └── logs.py              # Logs de auditoría
├── services/                # Lógica de negocio
│   ├── costos_service.py    # Lógica ME12
│   ├── condiciones_service.py # Lógica VK12
│   ├── queue_service.py     # Cola de peticiones
│   └── logging_service.py   # Sistema de logs
├── models/                  # Modelos Pydantic
│   ├── requests.py          # Modelos de petición
│   ├── responses.py         # Modelos de respuesta
│   ├── log_models.py        # Modelos de logging
│   └── queue_models.py      # Modelos de cola
├── templates/               # Templates Excel
├── tests/                   # Suite de tests (236+ tests)
│   ├── conftest.py          # Fixtures compartidos
│   ├── test_*.py            # Tests de integración
│   ├── unit/                # Tests unitarios
│   └── integration/         # Tests de integración avanzada
├── docs/                    # Documentación
│   ├── INSTALL.md           # Guía de instalación
│   ├── USAGE.md             # Guía de uso de la API
│   └── CONTRIBUTING.md      # Guía de contribución
└── .github/workflows/       # CI/CD
    └── ci.yml               # GitHub Actions
```

## Endpoints Disponibles

### General

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/` | Root endpoint | ✅ |
| GET | `/api/health` | Health check | ❌ |

### Costos (ME12)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/costos/template` | Descargar template Excel | ✅ |
| POST | `/api/costos/upload` | Upload + validación Excel | ✅ |
| POST | `/api/costos/execute` | Ejecutar ME12 en SAP | ✅ |
| GET | `/api/costos/status/{job_id}` | Estado de ejecución | ✅ |

### Condiciones (VK12)

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/condiciones/template` | Descargar template Excel | ✅ |
| POST | `/api/condiciones/upload` | Upload + validación Excel | ✅ |
| POST | `/api/condiciones/execute` | Ejecutar VK12 en SAP | ✅ |
| GET | `/api/condiciones/status/{job_id}` | Estado de ejecución | ✅ |

### Cola de Peticiones

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/queue/stats` | Estadísticas de la cola | ✅ |
| GET | `/api/queue/status/{job_id}` | Estado de petición | ✅ |
| DELETE | `/api/queue/{job_id}` | Cancelar petición | ✅ |

### Logs de Auditoría

| Método | Ruta | Descripción | Auth |
|--------|------|-------------|------|
| GET | `/api/logs` | Consultar logs con filtros | ✅ |
| GET | `/api/logs/{job_id}` | Logs por job_id | ✅ |

## Variables de Entorno (.env)

```env
# API Keys (separadas por coma)
API_KEYS=mi-key-secreta

# CORS (origens permitidos, separados por coma)
CORS_ORIGINS=http://localhost:4321,http://localhost:8000

# SAP
SAP_SYSTEM=PRD
SAP_MANDANT=100
SAP_LANG=ES

# Cola de peticiones
SAP_EXECUTION_TIMEOUT=120
MAX_QUEUE_SIZE=5
MAX_RETRIES=2

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# Logging
LOG_DIR=logs
LOG_RETENTION_DAYS=90
```

## Instalación

Ver `docs/INSTALL.md` para instrucciones detalladas.

```bash
cd backendPy
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp .env.example .env  # editar con values reales
```

## Ejecución

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## Tests

```bash
# Todos los tests (236+)
pytest tests/ -v

# Con cobertura (objetivo: 70%)
pytest tests/ --cov=. --cov-report=term-missing

# Tests unitarios solamente
pytest tests/unit/ -v

# Tests de integración solamente
pytest tests/integration/ -v

# Verificar umbral de cobertura
pytest tests/ --cov=. --cov-fail-under=70
```

### Cobertura Actual: 89%+

| Módulo | Cobertura |
|--------|-----------|
| config.py | 100% |
| dependencies.py | 100% |
| models/ | 100% |
| routers/health.py | 100% |
| services/condiciones_service.py | 90% |
| services/costos_service.py | 85% |
| services/queue_service.py | 95% |
| services/logging_service.py | 82% |

## Documentación

- `docs/INSTALL.md` - Guía de instalación paso a paso
- `docs/USAGE.md` - Ejemplos de uso de la API con curl
- `docs/CONTRIBUTING.md` - Guía para contribuir al proyecto

## Roadmap

Ver `specs/roadmap.md` para detalles completos de las fases:

1. **Fase 1** ✅ - Estructura base del proyecto
2. **Fase 2** ✅ - Sistema de autenticación
3. **Fase 3** ✅ - Health check y endpoints básicos
4. **Fase 4** ✅ - Endpoints para ME12 (Costos)
5. **Fase 5** ✅ - Endpoints para VK12 (Condiciones)
6. **Fase 6** ✅ - Sistema de cola de peticiones
7. **Fase 7** ✅ - Logging y auditoría
8. **Fase 8** ✅ - Testing y documentación
9. **Fase 9** 🔲 - Integración con frontends

## Notas Técnicas

- **Plataforma**: Windows obligatorio para SAP GUI (win32com). Tests corren en Linux/macOS.
- **Concurrencia**: Un solo proceso SAP a la vez (gestionado por cola de peticiones)
- **Autenticación**: API Key via header `X-API-Key`
- **Frontend**: Se desarrollará por separado en Astro/Laravel
- **Cobertura**: Mínimo 70% en módulos principales
- **CI/CD**: GitHub Actions ejecuta tests automáticamente en PRs
