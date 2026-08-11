# Requirements - Sistema de Cola de Peticiones (Fase 6)

## Scope

### Qué incluye
- Sistema de cola **en memoria** para gestionar peticiones concurrentes a SAP
- Soporte para **cualquier transacción futura** (ME12, VK12, y nuevas)
- Cancelación de peticiones en cola por parte del usuario
- Notificación al usuario: estado "en cola" y "próximamente se ejecutará"
- Límite máximo de **5 peticiones** en cola
- Timeout configurable para peticiones
- Reintentos automáticos en errores transitorios
- Logging de errores y resultado de cada ejecución

### Qué NO incluye
- Persistencia de cola (se pierde al reiniciar el servidor)
- Cola distribuida / Redis / base de datos
- Interfaz de usuario (solo API responses)
- Múltiples sesiones SAP concurrentes

### Datos / Campos

| Campo | Descripción |
|-------|-------------|
| `job_id` | ID único de la petición en cola |
| `transaction` | Tipo de transacción (ME12, VK12, etc.) |
| `status` | Estado: `queued`, `processing`, `completed`, `failed`, `cancelled` |
| `position` | Posición en la cola (1-N) |
| `queued_at` | Timestamp de cuando se encoló |
| `started_at` | Timestamp de inicio de ejecución |
| `completed_at` | Timestamp de finalización |
| `error_message` | Mensaje de error (si aplica) |
| `user_id` | Identificador del usuario que hizo la petición |

---

## Decisions

1. **Cola en memoria (dict/list)**: El usuario confirmó que no necesita persistencia. Se usa un `deque` o lista thread-safe de Python.

2. **Cancelación habilitada**: El usuario puede cancelar una petición mientras esté en estado `queued` mediante `DELETE /api/queue/{job_id}`.

3. **Extensible a transacciones futuras**: El sistema de cola es agnóstico a la transacción. Los servicios existentes (costos_service, condiciones_service) se integran con la cola sin cambios en su lógica interna.

4. **Máximo 5 peticiones en cola**: Si la cola está llena, se retorna HTTP 429 (Too Many Requests).

5. **Reintentos automáticos**: Máximo 2 reintentos en errores transitorios (timeout SAP, desconexión temporal). Errores de negocio NO se reintentan.

6. **Timeout configurable**: Por defecto 120 segundos por ejecución. Configurable vía variable de entorno `SAP_EXECUTION_TIMEOUT`.

7. **Logging de errores**: Los errores se registran en el log del sistema (Python logging), no se notifican al usuario en tiempo real más allá del status endpoint.

---

## Context

- **Stack existente**: FastAPI async, Pydantic models, pytest
- **Patrón actual**: `routers/` → `services/` → ejecución SAP
- **Concurrencia SAP**: Un solo proceso activo a la vez (restricción de SAP GUI)
- **Lenguaje**: Docstrings y comentarios en español
- **Tests**: Mock completo de SAP (win32com), no tocar SAP real
- **Integración**: Los endpoints existentes (ME12/VK12) deben pasar por la cola automáticamente
