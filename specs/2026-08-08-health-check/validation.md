# Validation - Health Check y Endpoints Básicos

## Automated
- [ ] `pytest tests/` pasa sin errores
- [ ] `pytest tests/test_health.py` - todos los tests de health pasan
- [ ] FastAPI inicia sin errores
- [ ] Swagger docs (`/docs`) muestra el endpoint GET /health

## Manual
1. Iniciar servidor: `uvicorn main:app --reload`
2. Abrir `http://localhost:8000/health`
3. Verificar respuesta:
   ```json
   {
     "status": "ok",
     "message": "Servicio listo para procesar pedidos",
     "timestamp": "2026-08-08T..."
   }
   ```
4. Verificar que NO requiere header `X-API-Key`
5. Verificar Swagger en `http://localhost:8000/docs` muestra el endpoint

## Definition of Done
- [ ] Endpoint GET /health retorna 200 con modelo HealthResponse
- [ ] Endpoint es público (sin autenticación)
- [ ] Tests cubren: status code, campos de respuesta, sin auth requerida
- [ ] Documentación Swagger actualizada automáticamente
