# Requirements: Logging y Auditoría

## Scope

### ¿Qué es?
Sistema de logs estructurado (JSON) para auditoría de todas las ejecuciones SAP y operaciones sensibles del backend. Los logs se almacenan en archivos JSON rotativos y se exponen vía API.

### ¿Qué incluye?
- **Logs de auditoría por ejecución SAP**: Cada ejecución ME12/VK12 genera un log entry con:
  - `timestamp`: ISO 8601 UTC
  - `user_id`: Identificador del usuario SAP que inició sesión
  - `transaction`: Tipo de transacción (ME12, VK12)
  - `job_id`: ID del job asociado
  - `status`: resultado (success, error, cancelled)
  - `duration_seconds`: Tiempo total de la ejecución
  - `sap_login_success`: Boolean - si el login a SAP fue exitoso
  - `rows_total`: Total de filas procesadas
  - `rows_success`: Filas exitosas
  - `rows_failed`: Filas con error
  - `errors`: Lista de errores detallados, cada uno con:
    - `row`: Número de fila del Excel
    - `material`: Código del material (ME12) o material (VK12)
    - `proveedor`: Proveedor (ME12) o N/A (VK12)
    - `message`: Mensaje descriptivo del error
  - `metadata`: Dict con info adicional (filename, org_compras, etc.)

- **Logs de autenticación**: Intentos de login (API Key) con éxito/fallo
- **Logs de upload**: Subida de archivos Excel con resultado de validación
- **Logs de sistema**: Errores críticos, startup/shutdown

### ¿Qué NO incluye?
- Logs de debug/trace para desarrollo (solo audit-level)
- Integración con servicios externos (Loki, Datadog, etc.)
- Alertas o notificaciones basadas en logs
- Logs de health check (son demasiado frecuentes)

---

## Decisions

| Decisión | Elección | Justificación |
|----------|----------|---------------|
| Formato de almacenamiento | JSON rotativo (archivos diarios) | Simple, sin dependencias, fácil de consultar y rotar |
| Exposición vía API | `GET /api/logs` (global) + `GET /api/logs/{job_id}` (por ejecución) | Permite al frontend consultar historial y detalles |
| Nivel de log | `AUDIT` (custom level entre INFO y WARNING) | Separar logs de negocio de logs técnicos |
| Retención | 90 días, limpieza automática en startup | Cumplimiento interno, balance almacenamiento |
| Campo `errors[].row` | Requerido en errores de ejecución | Identificar fila exacta del template con problema |
| Campo `errors[].material` | Requerido para ME12/VK12 | Contexto del registro con error |
| Campo `errors[].proveedor` | Requerido para ME12, N/A para VK12 | Contexto adicional ME12 |

---

## Context

### Stack
- Python `logging` stdlib con formatter custom JSON
- Archivos en `logs/` (directorio, gitignored)
- Rotación por tamaño o por día (configurable en `config.py`)
- Pydantic models para estructura de log entries

### Patrones existentes
- Seguir estructura `services/` → `services/logging_service.py`
- Seguir estructura `routers/` → `routers/logs.py`
- Seguir estructura `models/` → `models/log_models.py`
- Configuración centralizada en `config.py`
- Tests en `tests/test_logging.py`

### Usuarios
- Usuarios reales de SAP (no servicio único)
- Cada ejecución se asocia a un `user_id` del request
- Los logs deben serconsultables por usuario

### Naming
- Archivos de log: `logs/audit-YYYY-MM-DD.json`
- Campo `level` en cada entry: `"audit"`, `"info"`, `"error"`
- Encoding: UTF-8
