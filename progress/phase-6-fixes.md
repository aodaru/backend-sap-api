# Phase 6 - Fixes post-review

**Fecha:** 2026-08-11

## ISSUE-1 (Critico): HTTP 429 no se retorna cuando la cola esta llena

**Archivos modificados:**
- `routers/costos.py` (lineas 175-181)
- `routers/condiciones.py` (lineas 189-199)

**Cambio:** Se envolvieron las llamadas a `execute_me12()` y `execute_vk12()` en bloques `try/except ValueError` que capturan el error de cola llena y lo convierten en `HTTPException(status_code=429)`. Anteriormente, el `ValueError` propagado por el servicio resultaba en un HTTP 500 generico.

## ISSUE-2 (Menor): Falta test de integracion HTTP para cola llena

**Archivo modificado:**
- `tests/test_queue.py`

**Cambio:** Se agrego la clase `TestQueueFullHTTP` con dos tests:
- `test_execute_costos_returns_429_when_queue_full`: Llena la cola con 5 items directamente via `request_queue.enqueue()`, luego verifica que `POST /api/costos/execute` retorna HTTP 429.
- `test_execute_condiciones_returns_429_when_queue_full`: Mismo enfoque para el endpoint de condiciones VK12.

Ambos tests mockean `validate_excel` para aislar la prueba en el comportamiento de la cola, y verifican tanto el status code 429 como que el detalle contiene "Cola llena".

## Verificacion

Todos los 77 tests pasan (75 existentes + 2 nuevos).
