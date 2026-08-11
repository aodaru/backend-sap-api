# Requirements: Phase 4 - Endpoints ME12 (Costos)

## Scope

### What's Included
- **Template Excel**: Descarga del template con campos predefinidos
- **Upload**: Recepción y validación de archivos Excel
- **Execute**: Ejecución de transacción SAP ME12 (modificación de precios)
- **Status**: Consulta de estado de jobs en cola

### Excel Template Fields
| Columna | Tipo | Requerido | Descripción |
|---------|------|-----------|-------------|
| Material | string | Sí | Código de material SAP |
| Proveedor | string | Sí | Código de proveedor |
| Org_Compras | string | Sí | Organización de compras (4 dígitos) |
| Tipo_Info | string | Sí | Tipo de info record (0=estándar) |
| Tipo_Condicion | string | Sí | Tipo de condición (PB00=precio base) |
| Nuevo_Precio | decimal | Sí | Nuevo precio a establecer |
| Moneda | string | Sí | Código moneda (MXN, USD, EUR) |
| Unidad_Precio | string | Sí | Unidad del precio |
| Unidad_Medida | string | Sí | Unidad de medida (ST, KG, etc.) |
| Valido_Desde | string | Sí | Fecha inicio vigencia (YYYYMMDD) |
| Valido_Hasta | string | Sí | Fecha fin vigencia (YYYYMMDD) |

### What's NOT Included
- VK12 (condiciones) - va en Fase 5
- Sistema de cola avanzado - va en Fase 6
- Logging extensivo - va en Fase 7
- Integración con frontends - va en Fase 9

## Decisions

| Decisión | Elección | Razón |
|----------|----------|-------|
| Jobs en memoria | `dict` + `uuid` | MVP simple, sin persistencia aún |
| Cola FIFO | `asyncio.Queue` | Simpleza, un proceso SAP a la vez |
| Validación Excel | openpyxl + Pydantic | Ya usamos Pydantic, openpyxl es estándar |
| Mock SAP en tests | `unittest.mock` | No tocar SAP real en tests |

## Context

### Stack Existente
- FastAPI + Pydantic (configurado en Fase 1-3)
- API Key auth via `dependencies.py`
- Estructura: `routers/`, `services/`, `models/`

### Patrones a Seguir
- Endpoints kebab-case: `/api/costos/template`
- Models en `models/responses.py` y `models/requests.py`
- Services con lógica SAP en `services/costos_service.py`
- Tests en `tests/` con fixtures en `conftest.py`

### Restricciones
- Solo Windows para SAP GUI (win32com)
- Un solo proceso SAP activo a la vez
- Template Excel ya definido en script existente
