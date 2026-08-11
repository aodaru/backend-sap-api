# Review — Fase 6: Sistema de Cola de Peticiones

**Fecha:** 2026-08-11
**Revisor:** Agente Revisor (automático)
**Veredicto:** ⚠️ CHANGES_REQUESTED

---

## Resumen Ejecutivo

La implementación de la Fase 6 es **sólida en estructura y cobertura de tests** (75/75 pasan), pero tiene **2 issues concretos** que impiden la aprobación: uno es un requisito funcional del spec no cubierto a nivel HTTP, y el otro es la ausencia de un test de validación del escenario de cola llena vía endpoint.

---

## Checkpoints

### 1. Modelos (Grupo 1) ✅

| Checkpoint | Estado |
|---|---|
| `QueueJobStatus` con QUEUED, PROCESSING, COMPLETED, FAILED, CANCELLED | [x] `queue_models.py:15-22` |
| `QueueRequest` con todos los campos del spec | [x] `queue_models.py:25-58` — job_id, transaction, status, position, queued_at, started_at, completed_at, error_message, user_id |
| `QueueStatus` con position, estimated_wait, status | [x] `queue_models.py:61-76` |
| `QueueStats` con total_queued, total_processing, total_completed | [x] `queue_models.py:79-101` — incluye additionally total_failed, total_cancelled, max_queue_size |
| No se rompió `JobStatus` existente para ME12/VK12 | [x] `responses.py:33-41` — valores originales (PENDING, PROCESSING, COMPLETED, FAILED) intactos; QUEUED y CANCELLED añadidos sin romper backward compatibility. Tests en `test_queue.py:520-541` lo confirman. |

### 2. Servicio de Cola (Grupo 2) ⚠️

| Checkpoint | Estado |
|---|---|
| `RequestQueue` con enqueue, dequeue, cancel, get_status, get_stats | [x] `queue_service.py:34-425` — todos los métodos implementados |
| Thread-safety con `asyncio.Lock` | [x] `queue_service.py:59` — `self._lock = asyncio.Lock()`, usado en todos los métodos públicos |
| Límite máximo de 5 peticiones (HTTP 429 si llena) | [ ] `queue_service.py:87-90` — raises `ValueError`, pero **los routers NO lo capturan → retorna HTTP 500 en vez de 429** |
| Reintentos automáticos (max 2, solo errores transitorios) | [x] `queue_service.py:335-409` — `process_with_retries()` itera max_retries+1 veces, solo para TRANSIENT_ERRORS (TimeoutError, ConnectionError, etc.) |
| Timeout configurable via `SAP_EXECUTION_TIMEOUT` | [x] `queue_service.py:371-373` — `asyncio.wait_for(func, timeout=self._execution_timeout)` |
| Instancia global `request_queue` | [x] `queue_service.py:428` |

### 3. Integración (Grupo 3) ✅

| Checkpoint | Estado |
|---|---|
| `execute_me12()` pasa por la cola | [x] `costos_service.py:192-269` — enqueue → dequeue → process_with_retries → mark_completed/mark_failed |
| `execute_vk12()` pasa por la cola | [x] `condiciones_service.py:307-386` — mismo patrón |
| Compatibilidad con sistema de jobs existente | [x] — `job_manager` sigue usándose, el flujo de jobs es compatible |

### 4. Endpoints (Grupo 4) ✅

| Checkpoint | Estado |
|---|---|
| `GET /api/queue/status/{job_id}` | [x] `routers/queue.py:21-50` |
| `DELETE /api/queue/{job_id}` | [x] `routers/queue.py:53-100` — retorna 409 si no se puede cancelar, 404 si no existe |
| `GET /api/queue/stats` | [x] `routers/queue.py:103-119` |
| Router registrado en `main.py` | [x] `main.py:65` — `app.include_router(queue_router, prefix="/api/queue")` |
| Autenticación por API Key en todos los endpoints | [x] — `_api_key: str = Depends(verify_api_key)` en los 3 endpoints |

### 5. Configuración (Grupo 5) ✅

| Checkpoint | Estado |
|---|---|
| `.env.example` actualizado con las 3 variables | [x] `.env.example:16-18` — SAP_EXECUTION_TIMEOUT=120, MAX_QUEUE_SIZE=5, MAX_RETRIES=2 |
| `config.py` con las nuevas variables | [x] `config.py:44-46` — con tipos estrictos (int) |
| Tests existentes no rompidos | [x] — 39 tests preexistentes pasan intactos (auth, health, costos, condiciones) |

### 6. Code Quality ✅

| Checkpoint | Estado |
|---|---|
| Docstrings en español | [x] — todos los módulos, clases y métodos documentados en español |
| Type hints correctos | [x] — return types, parameters, Optional, Dict, List correctamente usados |
| Sin imports circulares | [x] — lazy imports en costos_service.py:192 y condiciones_service.py:307-308 |
| Maneo de errores apropiado | [x] — ValueError para cola llena, KeyError para job no encontrado, HTTPException en routers |
| Logging donde sea necesario | [x] — logger.info/warning/error en puntos clave del queue_service.py |

### 7. Tests ✅

| Checkpoint | Estado |
|---|---|
| `pytest -v` TODOS pasan | [x] — 75 passed, 0 failed |
| Cobertura de cola llena | [x] `test_queue.py:169-177` — `test_enqueue_full_queue_raises` |
| Cobertura cancelar processing | [x] `test_queue.py:232-239` — `test_cancel_processing_fails` |
| Cobertura job inexistente | [x] `test_queue.py:242-246` — `test_cancel_nonexistent_raises` |
| Cobertura estado mixto | [x] `test_queue.py:279-295` — `test_get_stats_mixed` |

---

## Issues Encontrados

### ISSUE-1: HTTP 429 no se retorna cuando la cola está llena (CRÍTICO)

**Spec reference:** `requirements.md:45` — "Si la cola está llena, se retorna HTTP 429 (Too Many Requests)."
**Validation reference:** `validation.md:39-41` — "Verificar que la 6ta retorna HTTP 429"

**Ubicación:**
- `services/costos_service.py:196-209` — `execute_me12()` hace `enqueue()` que raises `ValueError`
- `services/condiciones_service.py:311-325` — `execute_vk12()` hace `enqueue()` que raises `ValueError`
- `routers/costos.py:175` — `await execute_me12(rows_data, job_id)` **sin try/except**
- `routers/condiciones.py:189` — `await execute_vk12(rows_data, job_id, ...)` **sin try/except**

**Resultado:** Cuando la cola está llena, el `ValueError` se propaga sin capturar → FastAPI retorna **HTTP 500 Internal Server Error** en vez de **HTTP 429 Too Many Requests**.

**Fix requerido:** Agregar try/except en `routers/costos.py:execute_costos()` y `routers/condiciones.py:execute_condiciones()` para capturar `ValueError` y retornar HTTP 429:
```python
try:
    await execute_me12(rows_data, job_id)
except ValueError as e:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail=str(e),
    )
```

---

### ISSUE-2: Falta test de integración HTTP para cola llena (MENOR)

**Spec reference:** `validation.md:39-41` — "Enviar 6 peticiones rápidas → Verificar que la 6ta retorna HTTP 429"

**Ubicación:** `tests/test_queue.py` — existe `test_enqueue_full_queue_raises` (línea 169) pero solo testea a nivel de servicio, NO a nivel de endpoint HTTP.

**Fix requerido:** Agregar test en `TestQueueEndpoints` que:
1. Llene la cola (max 5) vía execute endpoints
2. Envíe una 6ta petición
3. Verifique que retorna HTTP 429 con mensaje "Cola llena"

---

## Warnings (No bloqueantes)

1. **`datetime.utcnow()` deprecation** — `queue_service.py:99,127,170,304,327` y `costos_service.py:47` usan `datetime.utcnow()` que Python 3.14+ depreca. Recomendado: `datetime.now(datetime.UTC)`. Afecta warnings en pytest pero no rompe funcionalidad.

---

## Veredicto

**CHANGES_REQUESTED**

Los 2 issues son concretos y acotados:
1. **ISSUE-1** es un requisito funcional del spec (HTTP 429) que no está implementado a nivel HTTP.
2. **ISSUE-2** es un test de validación del spec que falta.

Ambos se pueden resolver en <30 minutos de trabajo.

---

## Recomendaciones (Post-fix)

1. **Serie real de cola:** La implementación actual encola → desencola → ejecuta inmediatamente (en el mismo handler). Esto significa que bajo carga concurrente, múltiples requests podrían estar en PROCESSING simultáneamente. Para true serialization, se necesitaría un background worker que procese la cola secuencialmente. Esto es **out of scope** para la Fase 6 actual.
2. **Migrar de `datetime.utcnow()`** a `datetime.now(datetime.UTC)` antes de que Python lo elimine.
