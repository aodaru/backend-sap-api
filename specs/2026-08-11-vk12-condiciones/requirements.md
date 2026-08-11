# Requirements - VK12 Condiciones (Fase 5)

## Objetivo
Implementar endpoints para la transacción SAP VK12 (modificación masiva de condiciones de precio), siguiendo el patrón establecido en la Fase 4 (ME12 Costos).

---

## Scope

### Incluido
- **Router** `routers/condiciones.py` con 4 endpoints:
  - `GET /api/condiciones/template` — Descarga template Excel VK12
  - `POST /api/condiciones/upload` — Upload + validación de Excel
  - `POST /api/condiciones/execute` — Ejecución de VK12 con credenciales del usuario
  - `GET /api/condiciones/status/{job_id}` — Consulta estado de job
- **Servicio** `services/condiciones_service.py` con lógica de negocio VK12
- **Modelos** en `models/responses.py` para respuestas de condiciones
- **Template Excel** `templates/condiciones_template.xlsx` con columnas VK12
- **Tests** `tests/test_condiciones.py` siguiendo patrón de `test_costos.py`
- **Configuración** de validaciones en `config.py` o variables de entorno

### No incluido
- Desarrollo de scripts SAP (ya existen en app de escritorio)
- Frontend (se desarrollará por separado)
- Sistema de cola de peticiones (Fase 6)
- Logging avanzado (Fase 7)

---

## Template Excel VK12 - Columnas

| # | Columna | Tipo | Requerida | Descripción | Validación |
|---|---------|------|-----------|-------------|------------|
| 1 | MATERIAL | numérico | Según flujo | Código del material | Solo números |
| 2 | UNIDAD_DE_MEDIDA | texto | Según flujo | Unidad de medida | Lista válida (UN, KG, etc.) |
| 3 | IMPORTE | numérico | Sí | Valor del cambio | Número (entero o decimal) |
| 4 | GRUPO_ARTICULO | numérico | Según flujo | Grupo de artículo | 9 dígitos numéricos |
| 5 | ORG_VENTA | numérico | Sí | Organización de ventas | Valor: 1000 |
| 6 | CAN_DISTR | numérico | Sí | Canal de distribución | Valores: 10, 20, 30, 40, 50 |
| 7 | SECTOR | numérico | Según flujo | Sector | Valores: 10, 20, 30, 40, 50 |
| 8 | RAMO | texto | Según flujo | Ramo | Valores: ZDET, ZCON, ZPRO, ZCOL, ZMIN |
| 9 | TIPO_MODIFICACION | texto | Sí | Flujo a ejecutar | Ver flujos válidos |

> **Nota**: "Según flujo" indica que la columna es requerida solo si el flujo la necesita.

---

## Flujos de Modificación VK12

### Flujo 1: `mat_orgvent_candistr`
- **Descripción**: Modificación por Material + Organización de Ventas + Canal de Distribución
- **Campos requeridos**: MATERIAL, UNIDAD_DE_MEDIDA, IMPORTE, ORG_VENTA, CAN_DISTR
- **Tipo de condición SAP**: Z004

### Flujo 2: `orgvent_candistr_gpoart`
- **Descripción**: Modificación por Org. Ventas + Canal Distrib. + Grupo Artículo
- **Campos requeridos**: ORG_VENTA, CAN_DISTR, GRUPO_ARTICULO, IMPORTE
- **Tipo de condición SAP**: Z004

### Flujo 3: `orgvent_candistr_sec_ramo_mat`
- **Descripción**: Modificación por Org. Ventas + Canal Distrib. + Sector + Ramo + Material
- **Campos requeridos**: ORG_VENTA, CAN_DISTR, SECTOR, RAMO, MATERIAL
- **Tipo de condición SAP**: Z004

### Flujo 4: `orgven_candist_sec_gpoart`
- **Descripción**: Modificación por Org. Ventas + Canal Distrib. + Sector + Grupo Artículo
- **Campos requeridos**: ORG_VENTA, CAN_DISTR, SECTOR, RAMO, GRUPO_ARTICULO
- **Tipo de condición SAP**: Z004

---

## Decisions

### Diferencia clave con ME12: Credenciales SAP
- **App de escritorio**: Credenciales en `.env` (USER, PASSWD, SYSTEM, MANDT, LANGUAGE)
- **Web API**: Credenciales se reciben en el body del request `POST /api/condiciones/execute`
- **Modelo de request**: Nuevo modelo `CondicionesExecuteRequest` con campos:
  - `system`: str — Sistema SAP (ej: "ERQ")
  - `mandt`: str — Cliente SAP (ej: "200")
  - `username`: str — Usuario SAP
  - `password`: str — Contraseña SAP
  - `language`: str — Idioma (ej: "ES")

### Validaciones heredadas de app de escritorio
- `ORG_VENTA`: Debe ser "1000"
- `CAN_DISTR`: Debe ser 10, 20, 30, 40 o 50
- `SECTOR`: Debe ser 10, 20, 30, 40 o 50
- `RAMO`: Debe ser ZDET, ZCON, ZPRO, ZCOL o ZMIN
- `GRUPO_ARTICULO`: 9 dígitos numéricos
- `MATERIAL`: Solo números
- `UNIDAD_DE_MEDIDA`: Lista de unidades válidas (ver .env.example de app escritorio)
- `IMPORTE`: Numérico
- `TIPO_MODIFICACION`: Debe ser uno de los 4 flujos válidos

### Patrón de implementación
- Seguir exactamente la estructura de `routers/costos.py` y `services/costos_service.py`
- Reutilizar `JobManager` existente (instancia global en `costos_service.py`)
- Reutilizar `ValidationDetail` y `JobStatus` de `models/responses.py`
- Agregar modelos específicos: `CondicionesUploadResponse`, `CondicionesExecuteResponse`, `CondicionesStatusResponse`
- Template se genera dinámicamente si no existe (patrón de ME12)

---

## Context

### Referencia: App de escritorio
- **Ruta**: `/home/agarcia/dev/Jurado/pythonSap/deskapp/sapCondMassMod/`
- **Lógica SAP**: `sap_vk12_massmod.py` — 4 métodos para cada flujo
- **Validaciones**: `validators.py` — Validación por campos y flujos
- **Template**: `template_vk12.xlsx` — 9 columnas
- **Configuración**: `.env.example` con valores válidos

### Convenciones del proyecto
- Docstrings en español
- Python snake_case, endpoints kebab-case
- Tests con mock de SAP (no tocar SAP real)
- Autenticación API Key en todos los endpoints
- Respuestas Pydantic estandarizadas
- Logging con `logging.getLogger(__name__)`

### Stack
- FastAPI, Pydantic, openpyxl, pytest
- Sin nuevas dependencias (usar las existentes)
