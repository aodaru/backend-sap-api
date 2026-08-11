# Validation - Sistema de Cola de Peticiones (Fase 6)

## Validación Automatizada

### Tests
```bash
# Ejecutar todos los tests
pytest -v

# Ejecutar solo tests de la cola
pytest tests/test_queue*.py -v

# Ejecutar tests de integración
pytest tests/ -v --tb=short
```

### Verificaciones requeridas
- [ ] Todos los tests existentes pasan (ME12, VK12, health, auth)
- [ ] Tests de cola pasan (modelo, servicio, endpoints)
- [ ] Tests de integración cola + servicios pasan
- [ ] No hay warnings de deprecation en pytest

---

## Validación Manual

### Escenario 1: Encolar petición
1. Enviar POST a `/api/costos/execute` (o VK12)
2. Verificar que retorna `job_id` y status `queued`
3. Verificar que `GET /api/queue/status/{job_id}` muestra posición en cola

### Escenario 2: Cancelar petición
1. Tener al menos 1 petición en cola
2. Enviar DELETE a `/api/queue/{job_id}`
3. Verificar que status cambia a `cancelled`
4. Verificar que la petición no se ejecuta

### Escenario 3: Límite de cola (5 peticiones)
1. Enviar 6 peticiones rápidas
2. Verificar que la 6ta retorna HTTP 429
3. Verificar mensaje de error indicando cola llena

### Escenario 4: Timeout
1. Configurar `SAP_EXECUTION_TIMEOUT=10` (segundos)
2. Ejecutar una petición que tome más de 10s
3. Verificar que se cancela por timeout
4. Verificar que se registra en log

### Escenario 5: Reintentos
1. Simular error transitorio en servicio SAP (mock)
2. Verificar que se reintenta automáticamente (max 2 veces)
3. Verificar que errores de negocio NO se reintentan

### Escenario 6: Múltiples transacciones
1. Encolar una petición ME12 y una VK12
2. Verificar que ambas se procesan correctamente
3. Verificar que el sistema es agnóstico a la transacción

---

## Edge Cases
- Reiniciar servidor con peticiones en cola → la cola se vacía (esperado)
- Cancelar petición que ya está procesando → retorna error (ya no se puede cancelar)
- Petición con job_id inexistente → retorna 404
- Cola vacía → dequeue retorna None

---

## Definition of Done
- [ ] Servicio de cola implementado con thread-safety
- [ ] Cancelación funcional
- [ ] Límite de 5 peticiones enforced
- [ ] Reintentos automáticos (max 2)
- [ ] Timeout configurable
- [ ] Integrado con servicios ME12 y VK12
- [ ] Endpoints de cola documentados en Swagger
- [ ] Todos los tests pasan
- [ ] Roadmap.md actualizado
