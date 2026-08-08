# Requirements - Sistema de Autenticación (Fase 2)

## Scope

### Qué SÍ incluye
- Autenticación por API Key via header `X-API-Key`
- Una única API Key global compartida por todos los clientes
- Validación de key en todos los endpoints (excepto docs de Swagger/ReDoc)
- Respuesta HTTP 401 cuando la key es incorrecta o no se proporciona
- Configuración de la key en archivo `.env`

### Qué NO incluye
- Múltiples API Keys por usuario
- Rate limiting (se implementará en fase posterior)
- Logging de auditoría de autenticación (fase posterior)
- OAuth ni autenticación avanzada

### Campos / Datos
| Campo | Tipo | Requerido | Descripción |
|-------|------|-----------|-------------|
| `X-API-Key` | Header HTTP | Sí | Key de autenticación para acceder a la API |

### Respuestas de error
| Código | Condición | Body |
|--------|-----------|------|
| 401 | Header `X-API-Key` ausente | `{"detail": "API Key required"}` |
| 401 | Header `X-API-Key` inválido | `{"detail": "Invalid API Key"}` |

---

## Decisions

1. **API Key global única**: Se utiliza una sola key compartida para todos los clientes. Razón: simplificación para uso interno, no se requiere control de acceso por usuario.

2. **Almacenamiento en `.env`**: La key se guarda como variable de entorno `API_KEY=xxx` en `.env`. Razón: sigue el patrón existente de configuración del proyecto.

3. **Solo validación, no registro**: Solo se valida que la key sea correcta. No se registra qué key realizó cada petición (el logging de auditoría es para fase posterior).

4. **Endpoints de docs públicos**: Swagger (`/docs`) y ReDoc (`/redoc`) quedan accesibles sin autenticación. Razón: facilita el desarrollo y testing.

5. **Dependencia FastAPI**: Se implementa como `APIKeyHeader` dependency en `dependencies.py`, patrón nativo de FastAPI.

---

## Context

- **Tono**: Técnico, directo, sin explicaciones innecesarias
- **Stack**: FastAPI con dependencias nativas (`fastapi.security`)
- **Patrón existente**: Seguir la estructura de `dependencies.py` ya creada en Fase 1
- **Frontend**: La key será configurada en los frontends Astro/Laravel que consuman la API
- **Seguridad**: La key viaja en headers HTTP (HTTPS recomendado en producción)
