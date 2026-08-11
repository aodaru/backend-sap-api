# Plan - VK12 Condiciones (Fase 5)

## Grupo 1: Modelos y Configuración
1.1. Agregar modelos de respuesta en `models/responses.py`:
    - `CondicionesUploadResponse`
    - `CondicionesExecuteRequest` (con credenciales SAP)
    - `CondicionesExecuteResponse`
    - `CondicionesStatusResponse`
1.2. Agregar constantes de validación VK12 en `services/condiciones_service.py`:
    - `REQUIRED_COLUMNS` (columnas del template)
    - `VALID_FLOWS` (4 flujos válidos)
    - `FLOW_FIELDS` (campos requeridos por flujo)
    - Valores válidos por campo (ORG_VENTA, CAN_DISTR, SECTOR, RAMO, etc.)

## Grupo 2: Servicio de Condiciones
2.1. Crear `services/condiciones_service.py`:
    - Función `get_template_path()` — Ruta al template
    - Función `validate_excel()` — Validación de Excel VK12
    - Función `execute_vk12()` — Ejecución mock de VK12
    - Reutilizar `JobManager` de `costos_service.py`
2.2. Implementar validación específica por flujo:
    - Validar `TIPO_MODIFICACION` existe
    - Validar campos requeridos según flujo
    - Validar valores permitidos por campo

## Grupo 3: Router de Condiciones
3.1. Crear `routers/condiciones.py` con 4 endpoints:
    - `GET /template` — Descarga template Excel VK12
    - `POST /upload` — Upload + validación
    - `POST /execute` — Ejecución con credenciales del usuario
    - `GET /status/{job_id}` — Estado del job
3.2. Registrar router en `main.py`:
    - Importar router
    - `app.include_router(condiciones_router, prefix="/api/condiciones")`

## Grupo 4: Template Excel
4.1. Crear `templates/condiciones_template.xlsx` con columnas VK12:
    - Headers: MATERIAL, UNIDAD_DE_MEDIDA, IMPORTE, GRUPO_ARTICULO, ORG_VENTA, CAN_DISTR, SECTOR, RAMO, TIPO_MODIFICACION
    - Fila de ejemplo con datos de prueba

## Grupo 5: Tests
5.1. Crear `tests/test_condiciones.py` siguiendo patrón de `test_costos.py`:
    - Test template download
    - Test template requires API key
    - Test upload valid Excel
    - Test upload invalid Excel (columnas faltantes)
    - Test upload invalid Excel (tipos incorrectos)
    - Test upload requires API key
    - Test upload invalid file extension
    - Test execute valid Excel
    - Test execute invalid Excel
    - Test execute requires API key
    - Test status returns job
    - Test status job not found
    - Test status requires API key
5.2. Actualizar `tests/conftest.py` con fixtures para condiciones:
    - `valid_condiciones_excel` — Excel válido con todos los flujos
    - `invalid_condiciones_excel_missing_columns` — Excel sin columnas
    - `invalid_condiciones_excel_bad_flow` — Excel con flujo inválido

## Grupo 6: Documentación y Limpieza
6.1. Verificar que Swagger/ReDoc muestra endpoints de condiciones
6.2. Ejecutar todos los tests y asegurar que pasan
6.3. Actualizar `README.md` con nuevos endpoints

---

## Orden de implementación recomendado
1. Grupo 1 (Modelos) → 2. Grupo 2 (Servicio) → 3. Grupo 4 (Template) → 4. Grupo 3 (Router) → 5. Grupo 5 (Tests) → 6. Grupo 6 (Documentación)

## Estimación
- **Archivos a crear**: 3 (`routers/condiciones.py`, `services/condiciones_service.py`, `tests/test_condiciones.py`)
- **Archivos a modificar**: 2 (`models/responses.py`, `main.py`, `tests/conftest.py`)
- **Template**: 1 (`templates/condiciones_template.xlsx`)
- **Complejidad**: Media (replicar patrón existente con adaptaciones)
