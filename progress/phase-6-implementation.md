# Implementación Fase 6 - Sistema de Cola de Peticiones

**Fecha**: 2026-08-11
**Branch**: `feature/request-queue`
**Estado**: COMPLETADO

## Resumen

Se implementó un sistema de cola en memoria para gestionar peticiones concurrentes a transacciones SAP (ME12, VK12). El sistema es agnóstico a la transacción, thread-safe, y soporta cancelación, reintentos automáticos y timeout configurable.

## Archivos Creados

| Archivo | Descripción |
|---------|-------------|
| `models/queue_models.py` | Modelos Pydantic: `QueueJobStatus`, `QueueRequest`, `QueueStatus`, `QueueStats` |
| `services/queue_service.py` | Clase `RequestQueue` con cola FIFO thread-safe |
| `routers/queue.py` | Endpoints: `GET /status/{job_id}`, `DELETE /{job_id}`, `GET /stats` |
| `tests/test_queue.py` | 36 tests: modelos, servicio, endpoints, integración |

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `models/responses.py` | Agregados `QUEUED` y `CANCELLED` al enum `JobStatus` |
| `services/costos_service.py` | `execute_me12()` pasa por la cola de peticiones |
| `services/condiciones_service.py` | `execute_vk12()` pasa por la cola de peticiones |
| `main.py` | Registro de `queue_router` con prefix `/api/queue` |
| `config.py` | Variables: `sap_execution_timeout`, `max_queue_size`, `max_retries` |
| `.env.example` | Documentación de las nuevas variables |

## Estado de Tests

```
75 passed, 214 warnings in 0.42s
```

- **Tests existentes**: 39 (sin cambios)
- **Tests nuevos**: 36 (cola: modelos, servicio, endpoints, integración)

## Funcionalidad Implementada

### Grupo 1: Modelo de Datos
- `QueueJobStatus` enum con 5 estados: QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED
- `QueueRequest`: Modelo completo de petición con timestamps
- `QueueStatus`: Estado con posición y tiempo estimado
- `QueueStats`: Estadísticas de la cola
- `JobStatus` extendido sin romper funcionalidad existente

### Grupo 2: Servicio de Cola
- `RequestQueue` con `asyncio.Lock` para thread-safety
- `enqueue()`: Añade a cola, máximo 5, retorna posición
- `dequeue()`: Extrae siguiente en estado QUEUED
- `cancel()`: Solo para peticiones en estado QUEUED
- `get_status()`: Retorna posición y estado
- `get_stats()`: Contadores por estado
- `process_with_retries()`: Reintentos automáticos (max 2, solo errores transitorios)
- Timeout configurable via `SAP_EXECUTION_TIMEOUT` (default 120s)

### Grupo 3: Integración
- `execute_me12()` y `execute_vk12()` ahora pasan por la cola
- Flujo: enqueue → dequeue → process_with_retries → mark_completed/mark_failed
- Compatibilidad total con sistema de jobs existente

### Grupo 4: Endpoints
- `GET /api/queue/status/{job_id}` → Estado de petición
- `DELETE /api/queue/{job_id}` → Cancelar petición (solo QUEUED)
- `GET /api/queue/stats` → Estadísticas de la cola

### Grupo 5: Configuración
- Variables de entorno documentadas
- Tests completos para todos los componentes

## Notas de Implementación

1. **Thread-safety**: Se usa `asyncio.Lock` en todas las operaciones de la cola
2. **Posiciones**: Se calculan solo entre peticiones en estado QUEUED (las PROCESSING no cuentan)
3. **Historial**: La cola mantiene un historial de todas las peticiones para consultas
4. **Compatibilidad**: El enum `JobStatus` se extendió con QUEUED y CANCELLED sin romper valores existentes
5. **Limpieza de tests**: Se usa `asyncio.new_event_loop()` para limpiar el estado global en tests síncronos

## Pendiente (Out of Scope)

- Persistencia de cola (se pierde al reiniciar)
- Cola distribuida / Redis
- Interfaz de usuario
- Múltiples sesiones SAP concurrentes
