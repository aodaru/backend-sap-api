# Requirements - Health Check y Endpoints Básicos

## Scope

### Qué incluye
- Endpoint `GET /health` que retorna si el servicio está listo para procesar pedidos
- Modelo Pydantic para respuesta estandarizada
- Endpoint público (sin API Key) para que load balancers/monitoreo puedan consultarlo

### Qué NO incluye
- Verificación de conexión a SAP GUI (se implementará en Fase 7)
- Verificación de memoria, uptime, o métricas del sistema
- Logging de auditoría para este endpoint
- Múltiples checks de dependencias

## Decisions

| Decisión | Elección | Razón |
|----------|----------|-------|
| Endpoint público | Sí (sin API Key) | Los load balancers y sistemas de monitoreo necesitan acceso sin credenciales |
| Formato de respuesta | Modelo Pydantic | Consistencia con el resto de la API, validación automática, documentación Swagger |
| Verificación SAP | No (solo readiness básico) | SAP requiere win32com en Windows; el health check debe ser liviano y rápido |
| Método HTTP | GET | Estándar para health checks, cacheable |

## Context

- Seguir el formato estándar de respuesta del proyecto: `{"status": "ok", ...}`
- Endpoint debe ser rápido (< 100ms) ya que será consultado frecuentemente
- El frontend (Astro/Laravel) puede usar este endpoint para verificar disponibilidad antes de enviar peticiones
- Coherencia con `specs/tech-stack.md`: FastAPI, Pydantic, snake_case en Python
