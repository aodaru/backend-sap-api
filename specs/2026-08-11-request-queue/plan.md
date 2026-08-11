# Plan - Sistema de Cola de Peticiones (Fase 6)

## Grupo 1: Modelo de Datos y Estado
1.1. Crear `models/queue_models.py` con Pydantic models:
   - `QueueRequest` (job_id, transaction, status, position, timestamps, user_id)
   - `QueueStatus` (position, estimated_wait, status)
   - `QueueStats` (total_queued, total_processing, total_completed)
1.2. Definir enum `JobStatus` (queued, processing, completed, failed, cancelled)
1.3. Crear tests unitarios para modelos

## Grupo 2: Servicio de Cola
2.1. Crear `services/queue_service.py` con clase `RequestQueue`:
   - `enqueue(job_id, transaction, user_id)` → añade a cola (máx 5)
   - `dequeue()` → saca siguiente de la cola
   - `cancel(job_id)` → cancela petición en cola
   - `get_status(job_id)` → retorna estado y posición
   - `get_stats()` → retorna estadísticas de la cola
2.2. Implementar thread-safety con `threading.Lock` o `asyncio.Lock`
2.3. Implementar lógica de reintentos (max 2, solo errores transitorios)
2.4. Implementar timeout configurable (variable de entorno `SAP_EXECUTION_TIMEOUT`)
2.5. Crear tests unitarios para el servicio de cola

## Grupo 3: Integración con Servicios Existentes
3.1. Modificar `services/costos_service.py` para encolar ejecuciones
3.2. Modificar `services/condiciones_service.py` para encolar ejecuciones
3.3. Asegurar que `execute()` pasa por la cola antes de ejecutar SAP
3.4. Crear tests de integración para cola + servicios

## Grupo 4: Endpoints de la Cola
4.1. Crear `routers/queue.py` con endpoints:
   - `GET /api/queue/status/{job_id}` → estado de una petición
   - `DELETE /api/queue/{job_id}` → cancelar petición en cola
   - `GET /api/queue/stats` → estadísticas de la cola
4.2. Modificar endpoints existentes (ME12/VK12) para retornar `job_id` y status de cola
4.3. Crear tests para endpoints de cola

## Grupo 5: Configuración y Tests Finales
5.1. Agregar variables de entorno al `.env.example`:
   - `SAP_EXECUTION_TIMEOUT=120`
   - `MAX_QUEUE_SIZE=5`
   - `MAX_RETRIES=2`
5.2. Ejecutar suite completa de tests
5.3. Verificar que no se rompen tests existentes (ME12, VK12, health, auth)
5.4. Actualizar documentación en `specs/roadmap.md`
