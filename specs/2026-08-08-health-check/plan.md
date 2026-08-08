# Plan - Health Check y Endpoints Básicos

## Grupo 1: Modelo de Respuesta
1. Crear `models/responses.py` con modelo `HealthResponse`:
   - `status`: str ("ok" | "error")
   - `message`: str (descripción legible)
   - `timestamp`: datetime (hora de la respuesta)

## Grupo 2: Endpoint Health Check
2. Crear `routers/health.py` con endpoint `GET /health`
3. Configurar el router en `main.py` (incluir en la app)
4. Marcar como endpoint público (excluido del middleware de API Key)

## Grupo 3: Tests
5. Crear `tests/test_health.py` con tests:
   - Test health check retorna 200
   - Test respuesta tiene campos correctos
   - Test status es "ok"
   - Test endpoint no requiere API Key
