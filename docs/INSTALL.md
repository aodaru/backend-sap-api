# Guía de Instalación

Instrucciones paso a paso para instalar y configurar el Backend API de Automatización SAP.

## Requisitos Previos

- **Python 3.11+** (recomendado: 3.12 o 3.13)
- **pip** (gestor de paquetes de Python)
- **git** (control de versiones)
- **Windows** (requerido para producción con SAP GUI/win32com)

> **Nota**: Los tests y el desarrollo pueden ejecutarse en Linux/macOS. La integración con SAP GUI solo funciona en Windows.

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/backend-sap-automation.git
cd backend-sap-automation/backendPy
```

### 2. Crear entorno virtual

```bash
python -m venv .venv
```

**Windows:**
```cmd
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
source .venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

Para incluir dependencias de desarrollo (testing, cobertura):
```bash
pip install -r requirements.txt
# O directamente:
pip install pytest pytest-asyncio pytest-cov httpx
```

### 4. Configurar variables de entorno

```bash
cp .env.example .env
```

Editar el archivo `.env` con tus valores:

```env
# API Keys (separadas por coma)
API_KEYS=tu-key-secreta,otra-key

# CORS (orígenes permitidos)
CORS_ORIGINS=http://localhost:4321,http://localhost:8000

# SAP Configuration
SAP_SYSTEM=PRD
SAP_MANDANT=300
SAP_LANG=ES

# Cola de peticiones
SAP_EXECUTION_TIMEOUT=120
MAX_QUEUE_SIZE=5
MAX_RETRIES=2

# Servidor
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
DEBUG=false

# Logging
LOG_DIR=logs
LOG_RETENTION_DAYS=90
LOG_MAX_FILE_SIZE_MB=10
```

### 5. Verificar instalación

```bash
# Ejecutar tests
pytest tests/ -v

# Verificar cobertura
pytest tests/ --cov=. --cov-report=term-missing
```

## Variables de Entorno

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `API_KEYS` | API Keys válidas (separadas por coma) | (vacío) |
| `CORS_ORIGINS` | Orígenes CORS permitidos | `http://localhost:4321,http://localhost:8080` |
| `SAP_SYSTEM` | Sistema SAP | `PRD` |
| `SAP_MANDANT` | Mandante SAP | `100` |
| `SAP_LANG` | Idioma SAP | `ES` |
| `SERVER_HOST` | Host del servidor | `0.0.0.0` |
| `SERVER_PORT` | Puerto del servidor | `8000` |
| `DEBUG` | Modo debug | `false` |
| `SAP_EXECUTION_TIMEOUT` | Timeout por ejecución (seg) | `120` |
| `MAX_QUEUE_SIZE` | Max peticiones en cola | `5` |
| `MAX_RETRIES` | Reintentos en errores transitorios | `2` |
| `LOG_DIR` | Directorio de logs | `logs` |
| `LOG_RETENTION_DAYS` | Días de retención de logs | `90` |
| `LOG_MAX_FILE_SIZE_MB` | Tamaño max por archivo de log | `10` |

## Ejecución

### Servidor de desarrollo

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Servidor production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1
```

> **Nota**: Se recomienda 1 worker por ahora ya que SAP GUI solo permite una conexión a la vez.

## Estructura del Proyecto

```
backendPy/
├── main.py                  # FastAPI app principal
├── config.py                # Settings (pydantic-settings)
├── dependencies.py          # Verificación API Key
├── requirements.txt         # Dependencias
├── pyproject.toml           # Configuración de pytest/cobertura
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
├── tests/                   # Suite de tests
│   ├── conftest.py          # Fixtures compartidos
│   ├── test_health.py       # Tests health check
│   ├── test_auth.py         # Tests autenticación
│   ├── test_costos.py       # Tests ME12
│   ├── test_condiciones.py  # Tests VK12
│   ├── test_queue.py        # Tests cola
│   ├── test_logging.py      # Tests logging
│   ├── unit/                # Tests unitarios
│   │   ├── test_models.py
│   │   ├── test_config.py
│   │   ├── test_costos_service.py
│   │   ├── test_condiciones_service.py
│   │   └── test_queue_service.py
│   └── integration/         # Tests de integración
│       └── test_endpoints.py
├── docs/                    # Documentación
│   ├── INSTALL.md           # Esta guía
│   ├── USAGE.md             # Guía de uso de la API
│   └── CONTRIBUTING.md      # Guía de contribución
└── logs/                    # Logs de auditoría (generados)
```

## Solución de Problemas

### Error: `ModuleNotFoundError: No module named 'openpyxl'`

```bash
pip install openpyxl
```

### Error: `ImportError: win32com`

En Linux/macOS, `win32com` no está disponible. Los tests mockean esta dependencia automáticamente.

### Diagnóstico Windows de HTTP 503

Consultar el `operational_code` de auditoría asociado al `job_id`. El checklist
completo (integración habilitada, pywin32, SAPGUI, conexión, sesión y sesión
ocupada) está en `specs/2026-08-15-integracion-real-sap-gui/diagnostic-503-report.md`.
Los mensajes HTTP no incluyen secretos ni rutas internas.

### Tests fallan con `asyncio` errors

Asegúrate de tener `pytest-asyncio` instalado:
```bash
pip install pytest-asyncio
```

### Puerto ya en uso

Cambia el puerto en `.env`:
```env
SERVER_PORT=8001
```

O usa un puerto diferente al ejecutar:
```bash
uvicorn main:app --port 8001
```
