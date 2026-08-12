# Validación: Integración con Frontends (Fase 9)

## Estado de la fase

**⬜ PENDIENTE**

## Criterios de éxito

### 1. Configuración CORS
- [ ] CORS habilitado en `main.py`
- [ ] Orígenes configurados para Astro y Laravel
- [ ] Métodos HTTP permitidos: GET, POST, OPTIONS
- [ ] Headers permitidos: X-API-Key, Content-Type
- [ ] Configuración via variables de entorno

### 2. Endpoints Compatibles
- [ ] Todos los endpoints responden a requests OPTIONS (preflight)
- [ ] Endpoints funcionan con headers de origen
- [ ] Autenticación API Key funciona con CORS

### 3. Documentación
- [ ] Guía de integración para Astro creada
- [ ] Guía de integración para Laravel creada
- [ ] Ejemplos de código de consumo documentados
- [ ] Flujo de comunicación Backend-Frontend documentado

### 4. Tests
- [ ] Tests de CORS pasan
- [ ] Tests de preflight pasan
- [ ] Tests de integración con origins simulados pasan

## Criterio de merge a main
- [ ] Todos los criterios marcados
- [ ] PR abierto
- [ ] Validación manual ejecutada

## Anti-criterios (lo que NO debe pasar)
- ❌ Frontends reciben errores CORS al consumir API
- ❌ Preflight requests fallan
- ❌ Autenticación API Key no funciona desde frontend
- ❌ Headers de respuesta incompletos

## Cómo verificar

```bash
# Ejecutar tests
pytest tests/ -v

# Verificar CORS manualmente
curl -X OPTIONS http://localhost:8000/api/health \
  -H "Origin: http://localhost:4321" \
  -H "Access-Control-Request-Method: GET"

# Verificar respuesta con origen
curl http://localhost:8000/api/health \
  -H "Origin: http://localhost:4321" \
  -H "X-API-Key: tu-api-key"

# Ejecutar servidor y probar desde frontend
uvicorn main:app --reload
```
