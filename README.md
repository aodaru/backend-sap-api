# Backend API - Automatización SAP

Backend centralizado para ejecutar las apps de escritorio SAP
ubicadas en `deskapp/` vía API REST, con autenticación por API Key.

## Apps soportadas

| App | Transacción SAP | Descripción |
|-----|----------------|-------------|
| costosProveedorSap | ME12 | Modificación masiva de precios - Info Records de compra |
| sapCondMassMod | VK12 | Modificación masiva de condiciones de precio |

## Stack

- **FastAPI** - Framework async con docs automáticos (Swagger/ReDoc)
- **Pydantic** - Validación de models
- **python-multipart** - Uploads de archivos
- **pytest** - Testing
- **CORS** - Habilitado para frontends (Astro/Laravel)

## Estructura

```
backendPy/
├── main.py                  # FastAPI app principal
├── config.py                # Settings, API keys, env
├── dependencies.py          # Auth middleware (API key)
├── routers/
│   ├── costos.py            # Endpoints para ME12
│   └── condiciones.py       # Endpoints para VK12
├── services/
│   ├── costos_service.py    # Lógica SAP para ME12
│   └── condiciones_service.py # Lógica SAP para VK12
├── models/
│   ├── requests.py          # Pydantic models de entrada
│   └── responses.py         # Pydantic models de salida
├── templates/               # Excel templates (para download)
├── tests/
│   ├── conftest.py          # Fixtures compartidos
│   ├── test_auth.py         # Validación API key
│   ├── test_costos.py       # Endpoints ME12
│   ├── test_condiciones.py  # Endpoints VK12
│   ├── test_upload.py       # Upload + validación Excel
│   └── test_health.py       # Health check
├── .env.example
└── requirements.txt
```

## Endpoints

### General

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/health` | Health check |

### Costos (ME12)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/costos/template` | Descargar template Excel |
| POST | `/api/costos/upload` | Upload + validación Excel |
| POST | `/api/costos/execute` | Ejecutar ME12 en SAP |
| GET | `/api/costos/status/{job_id}` | Estado de ejecución |

### Condiciones (VK12)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/condiciones/template` | Descargar template Excel |
| POST | `/api/condiciones/upload` | Upload + validación Excel |
| POST | `/api/condiciones/execute` | Ejecutar VK12 en SAP |
| GET | `/api/condiciones/status/{job_id}` | Estado de ejecución |

## Autenticación

Todas las rutas `/api/*` requieren header `X-API-Key`:

```
X-API-Key: tu-api-key-aqui
```

Keys configuradas en `.env`:

```
API_KEYS=key1,key2,key3
```

Respuesta sin key o key inválida:

```json
{"detail": "API key inválida"}
```

## Flujo de uso

```
Frontend (Astro/Laravel)
    │
    ├─ GET  /api/costos/template     → descarga Excel template
    ├─ POST /api/costos/upload       → envía Excel → {ok, rows, job_id}
    ├─ POST /api/costos/execute      → {username, password} → ejecuta SAP
    └─ GET  /api/costos/status       → polls estado
```

## Variables de entorno (.env)

```env
# API Keys (separadas por coma)
API_KEYS=mi-key-secreta

# SAP
SAP_SYSTEM=PRD
SAP_MANDANT=100
SAP_LANG=ES

# Flask (para compatibilidad con web existente)
FLASK_SECRET_KEY=change-me
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
pytest tests/test_auth.py -v
pytest tests/test_costos.py -v
pytest tests/test_condiciones.py -v
```

### Estrategia de tests

| Capa | Qué se testea | Enfoque |
|------|---------------|---------|
| Auth | Rechazo sin key, key inválida, acepta key válida | TestClient + mock |
| Upload | Archivo válido, formato incorrecto, vacío | Mock validators |
| Execute | Login falla, SAP ocupado (409), ejecución OK | Mock SapClient |
| Status | Retorna estado correcto | Mock estado |
| Health | Responde 200 | Request simple |

Los tests NO tocan SAP real (todo mockeado).

## Notas técnicas

- **Ejecución en Windows**: La lógica SAP usa `win32com` (solo Windows). El backend se ejecuta en la VM Windows con SAP GUI instalado.
- **Un solo proceso SAP a la vez**: El endpoint execute retorna 409 si ya hay una ejecución en curso.
- **Archivos temporales**: Se limpian automáticamente tras ejecución.
- **Logs en tiempo real**: Se pueden agregar vía WebSocket (SocketIO) si el front lo necesita.
