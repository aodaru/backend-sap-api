# Plan: Phase 4 - Endpoints ME12 (Costos)

## 1. Models (`models/`)

### 1.1 `models/requests.py`
- Crear modelo `CostosUploadRequest` (si es necesario para metadata)
- Crear modelo `CostosExecuteRequest` con `job_id`

### 1.2 `models/responses.py`
- Agregar `CostosTemplateResponse` (mensaje de éxito)
- Agregar `CostosUploadResponse` con `filename`, `row_count`, `validations`
- Agregar `CostosExecuteResponse` con `job_id`, `status`
- Agregar `CostosStatusResponse` con `job_id`, `status`, `progress`, `results`
- Agregar `JobStatus` enum: `pending`, `processing`, `completed`, `failed`

## 2. Services (`services/`)

### 2.1 `services/costos_service.py`
- Crear clase `CostosService` con:
  - `validate_excel(file)` → valida columnas, tipos, retorna errores
  - `execute_me12(file_data)` → lógica SAP (mock en tests)
  - `get_template_path()` → ruta al template Excel
- Crear `JobManager` para gestionar jobs en memoria:
  - `create_job()` → crea job pending
  - `update_job(job_id, status, results)` → actualiza estado
  - `get_job(job_id)` → retorna estado del job

## 3. Routers (`routers/`)

### 3.1 `routers/costos.py`
- `GET /api/costos/template`
  - Descarga template Excel
  - Responses: 200 (file), 500 (error)
  
- `POST /api/costos/upload`
  - Recibe archivo Excel via `UploadFile`
  - Valida estructura y contenido
  - Retorna resumen de validación
  - Responses: 200 (válido), 400 (validación falla), 422 (error formato)
  
- `POST /api/costos/execute`
  - Ejecuta ME12 con datos del archivo
  - Crea job y retorna `job_id`
  - Responses: 202 (job creado), 400 (archivo inválido)
  
- `GET /api/costos/status/{job_id}`
  - Consulta estado del job
  - Responses: 200 (estado), 404 (job no encontrado)

### 3.2 Actualizar `main.py`
- Incluir router de costos en la app

## 4. Tests (`tests/`)

### 4.1 `tests/test_costos.py`
- Test template download (200)
- Test upload válido (200)
- Test upload inválido (400) - columnas faltantes
- Test upload inválido (400) - tipos incorrectos
- Test execute crea job (202)
- Test status retorna estado (200)
- Test status job inexistente (404)

### 4.2 Fixtures en `tests/conftest.py`
- Agregar fixture `valid_excel_file`
- Agregar fixture `invalid_excel_file`
- Agregar fixture `mock_sap_service`

## 5. Validación

### 5.1 Criterios de Aceptación
- [ ] Template Excel se descarga correctamente
- [ ] Upload valida archivos Excel (columnas, tipos)
- [ ] Execute ejecuta SAP (mockeado en tests)
- [ ] Status retorna estado del job
- [ ] Tests pasan para ME12

### 5.2 Definition of Done
- Todos los tests pasan
- Endpoints documentados en Swagger
- Sin dependencias nuevas sin aprobar
