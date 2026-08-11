# Plan: Logging y Auditoría

## Grupo 1: Configuración y Modelos

### 1.1 Configurar logging en `config.py`
- Agregar variables: `log_dir`, `log_retention_days`, `log_max_file_size_mb`
- Agregar `log_level` (default: "audit")

### 1.2 Crear `models/log_models.py`
- `AuditLogEntry`: Modelo base con todos los campos de auditoría
- `ErrorDetail`: Modelo para errores individuales (row, material, proveedor, message)
- `LogQueryParams`: Filtros para endpoint de consulta (transaction, user_id, date_from, date_to, status)
- `LogResponse`: Respuesta paginada del endpoint

### 1.3 Crear `logs/` directorio + `.gitignore`
- Crear directorio `logs/`
- Agregar `logs/` a `.gitignore`

---

## Grupo 2: Servicio de Logging

### 2.1 Crear `services/logging_service.py`
- `AuditLogger` class:
  - `__init__(log_dir, retention_days)`: Configura handler JSON rotativo
  - `log_execution(job_id, user_id, transaction, status, duration, sap_login_success, rows_total, rows_success, rows_failed, errors, metadata)`: Escribe log de ejecución
  - `log_auth(user_id, success, ip_address, message)`: Log de autenticación
  - `log_upload(user_id, filename, row_count, valid, validations)`: Log de upload
  - `log_error(context, message, exception)`: Log de errores del sistema
  - `cleanup_old_logs()`: Elimina archivos > retention_days
  - `get_logs(filters: LogQueryParams) -> List[AuditLogEntry]`: Consulta logs
  - `get_logs_by_job_id(job_id) -> List[AuditLogEntry]`: Logs de una ejecución

### 2.2 Integrar con JSON formatter custom
- `JsonAuditFormatter`: Formatea log records como JSON con campos estandarizados
- Timestamps en ISO 8601 UTC
- Encoding UTF-8

### 2.3 Implementar rotación de archivos
- Rotación diaria: `audit-YYYY-MM-DD.json`
- Limpieza automática en startup (via lifespan de FastAPI)
- Manejo de concurrencia de escritura (thread-safe con Lock)

---

## Grupo 3: Integración con Endpoints Existentes

### 3.1 Integrar logging en `routers/costos.py`
- Log en `execute`: Después de ejecutar ME12, llamar a `audit_logger.log_execution()`
- Capturar errores por fila (material + proveedor)
- Registrar duración total

### 3.2 Integrar logging en `routers/condiciones.py`
- Log en `execute`: Después de ejecutar VK12, llamar a `audit_logger.log_execution()`
- Capturar errores por fila (material)
- Registrar duración total

### 3.3 Integrar logging en `dependencies.py`
- Log en `verify_api_key`: Registrar intentos de autenticación (éxito/fallo)

### 3.4 Integrar logging en `main.py`
- Llamar `cleanup_old_logs()` en el lifespan startup
- Log de startup y shutdown

---

## Grupo 4: Endpoint de Consulta

### 4.1 Crear `routers/logs.py`
- `GET /api/logs`: Listar logs globales con filtros
  - Query params: `transaction`, `user_id`, `date_from`, `date_to`, `status`, `limit`, `offset`
  - Respuesta paginada con total
- `GET /api/logs/{job_id}`: Logs de una ejecución específica
- Autenticación: Requiere API Key (misma dependencia existente)

### 4.2 Registrar router en `main.py`
- Agregar `app.include_router(logs_router, prefix="/api/logs")`

---

## Grupo 5: Tests

### 5.1 Crear `tests/test_logging.py`
- Test `AuditLogger.log_execution()`: Verificar que escribe JSON válido
- Test `AuditLogger.log_auth()`: Verificar formato
- Test `AuditLogger.cleanup_old_logs()`: Verificar eliminación de archivos antiguos
- Test `AuditLogger.get_logs()`: Verificar consulta con filtros
- Test `AuditLogger.get_logs_by_job_id()`: Verificar filtrado por job
- Test endpoint `GET /api/logs`: Respuesta 200 con estructura correcta
- Test endpoint `GET /api/logs/{job_id}`: Respuesta 200 o 404
- Test autenticación del endpoint: 401 sin API key

### 5.2 Test de integración
- Test flujo completo: upload → execute → log generado
- Verificar campos del log post-ejecución

---

## Orden de implementación
1. Grupo 1 (config + models) — base sin dependencias
2. Grupo 2 (servicio) — core del sistema
3. Grupo 3 (integración) — conecta con endpoints existentes
4. Grupo 4 (endpoint) — expone los logs
5. Grupo 5 (tests) — validación completa
