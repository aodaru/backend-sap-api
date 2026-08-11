# Validation: Logging y Auditoría

## Pruebas Automatizadas

### Unit Tests (`tests/test_logging.py`)
```bash
pytest tests/test_logging.py -v
```

| Test | Qué valida |
|------|------------|
| `test_log_execution_writes_json` | `log_execution()` crea archivo JSON válido con todos los campos |
| `test_log_execution_error_fields` | Campo `errors` contiene row, material, proveedor, message |
| `test_log_auth_success` | `log_auth()` registra intento exitoso |
| `test_log_auth_failure` | `log_auth()` registra intento fallido |
| `test_log_upload` | `log_upload()` registra upload con resultado |
| `test_cleanup_old_logs` | `cleanup_old_logs()` elimina archivos > retention_days |
| `test_cleanup_keeps_recent` | `cleanup_old_logs()` NO elimina archivos recientes |
| `test_get_logs_filters_by_transaction` | Filtrado por tipo de transacción |
| `test_get_logs_filters_by_user` | Filtrado por usuario |
| `test_get_logs_filters_by_date` | Filtrado por rango de fechas |
| `test_get_logs_by_job_id` | Retorna logs de una ejecución específica |
| `test_get_logs_by_job_id_not_found` | Retorna lista vacía para job inexistente |

### Integration Tests (`tests/test_logging.py`)
```bash
pytest tests/test_logging.py -v -k integration
```

| Test | Qué valida |
|------|------------|
| `test_endpoint_get_logs_requires_auth` | `GET /api/logs` retorna 401 sin API key |
| `test_endpoint_get_logs_returns_200` | `GET /api/logs` retorna 200 con estructura paginada |
| `test_endpoint_get_logs_by_job_id` | `GET /api/logs/{job_id}` retorna 200 o 404 |
| `test_execute_generates_log` | Después de `POST /api/costos/execute`, existe log entry |

### Todos los tests
```bash
pytest tests/ -v
```

---

## Pruebas Manuales

### 1. Verificar generación de logs
1. Ejecutar `POST /api/costos/execute` con datos válidos
2. Verificar que se creó archivo `logs/audit-YYYY-MM-DD.json`
3. Abrir el archivo y confirmar estructura JSON con todos los campos requeridos

### 2. Verificar logs de error por fila
1. Ejecutar `POST /api/costos/execute` con archivo que tenga errores
2. Verificar que el log incluye `errors[]` con `row`, `material`, `proveedor`, `message`
3. Confirmar que `rows_failed` coincide con cantidad de errores

### 3. Verificar endpoint de consulta
1. `GET /api/logs` → Retorna lista paginada de logs
2. `GET /api/logs?transaction=ME12` → Solo logs de ME12
3. `GET /api/logs?user_id=ADMIN` → Solo logs de ese usuario
4. `GET /api/logs/{job_id_existente}` → Retorna logs de esa ejecución
5. `GET /api/logs/{job_id_inexistente}` → Retorna 404 o lista vacía

### 4. Verificar rotación y limpieza
1. Crear archivos de log fake con fecha de hace 91 días
2. Reiniciar la app
3. Verificar que los archivos antiguos fueron eliminados
4. Verificar que archivos de hoy se mantienen

### 5. Verificar autenticación del endpoint
1. `GET /api/logs` sin header → 401
2. `GET /api/logs` con key inválida → 401
3. `GET /api/logs` con key válida → 200

---

## Criterios de Aceptación (Definition of Done)

- [ ] Cada ejecución SAP genera un log de auditoría con todos los campos del spec
- [ ] Logs incluyen: timestamp, user_id, transaction, resultado, duration, errors con row/material/proveedor
- [ ] Logs se almacenan en archivos JSON rotativos diarios
- [ ] Endpoint `GET /api/logs` funciona con filtros y paginación
- [ ] Endpoint `GET /api/logs/{job_id}` funciona correctamente
- [ ] Limpieza automática de logs > 90 días en startup
- [ ] Todos los tests pasan (`pytest tests/ -v`)
- [ ] No se rompen tests existentes
- [ ] Archivos de log están en `.gitignore`
- [ ] Código sigue convenciones del proyecto (docstrings español, snake_case)
