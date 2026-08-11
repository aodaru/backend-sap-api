# Roadmap - Backend API Automatización SAP

## Fase 1: Estructura Base del Proyecto
**Objetivo**: Establecer la estructura fundamental del backend con FastAPI.

### Tareas
1. [x] Configurar proyecto Python con virtualenv
2. [x] Instalar dependencias: fastapi, uvicorn, pydantic, python-multipart
3. [x] Crear estructura de directorios:
   - `routers/` (endpoints)
   - `services/` (lógica de negocio)
   - `models/` (Pydantic models)
   - `templates/` (archivos Excel)
   - `tests/` (pruebas)
4. [x] Crear `main.py` con FastAPI app básica
5. [x] Configurar variables de entorno (`.env.example`)
6. [x] Crear `config.py` para gestión de settings

### Criterios de Aceptación
- [x] App FastAPI ejecuta sin errores
- [x] Estructura de directorios creada
- [x] Variables de entorno configuradas

---

## Fase 2: Sistema de Autenticación ✅
**Objetivo**: Implementar autenticación por API Key.

### Tareas
1. [x] Crear `dependencies.py` con middleware de API Key
2. [x] Implementar validación de headers `X-API-Key`
3. [x] Configurar keys en variables de entorno
4. [x] Crear respuestas de error para key inválida
5. [x] Tests para autenticación

### Criterios de Aceptación
- [x] Endpoints requieren API Key
- [x] Respuesta 401 sin key o key inválida
- [x] Tests pasan para autenticación

---

## Fase 3: Health Check y Endpoints Básicos ✅
**Objetivo**: Implementar endpoints de monitoreo básico.

### Tareas
1. [x] Crear endpoint `GET /api/health`
2. [x] Implementar verificación de estado del sistema
3. [x] Crear modelo de respuesta para health check
4. [x] Tests para health check

### Criterios de Aceptación
- [x] Health check retorna 200 con estado del sistema
- [x] Tests pasan para health check

---

## Fase 4: Endpoints para ME12 (Costos) ✅
**Objetivo**: Implementar endpoints para transacción ME12.

### Tareas
1. [x] Crear `routers/costos.py` con endpoints:
   - `GET /api/costos/template` (descargar Excel)
   - `POST /api/costos/upload` (upload + validación)
   - `POST /api/costos/execute` (ejecutar ME12)
   - `GET /api/costos/status/{job_id}` (estado)
2. [x] Crear `services/costos_service.py` con lógica SAP
3. [x] Crear `models/requests.py` y `models/responses.py`
4. [x] Implementar upload de archivos Excel
5. [x] Implementar ejecución de scripts SAP
6. [x] Implementar sistema de jobs/estados
7. [x] Tests para endpoints ME12

### Criterios de Aceptación
- [x] Template Excel se descarga correctamente
- [x] Upload valida archivos Excel
- [x] Execute ejecuta SAP (mockeado en tests)
- [x] Status retorna estado del job
- [x] Tests pasan para ME12

---

## Fase 5: Endpoints para VK12 (Condiciones) ✅
**Objetivo**: Implementar endpoints para transacción VK12.

### Tareas
1. [x] Crear `routers/condiciones.py` con endpoints:
   - `GET /api/condiciones/template`
   - `POST /api/condiciones/upload`
   - `POST /api/condiciones/execute`
   - `GET /api/condiciones/status/{job_id}`
2. [x] Crear `services/condiciones_service.py`
3. [x] Implementar lógica específica VK12
4. [x] Tests para endpoints VK12

### Criterios de Aceptación
- [x] Endpoints VK12 funcionan similar a ME12
- [x] Tests pasan para VK12

---

## Fase 6: Sistema de Cola de Peticiones
**Objetivo**: Manejar concurrencia con cola de peticiones.

### Tareas
1. [ ] Diseñar sistema de queue para peticiones
2. [ ] Implementar notificación al usuario cuando SAP está ocupado
3. [ ] Crear lógica de reintentos automáticos
4. [ ] Implementar timeout para peticiones
5. [ ] Tests para sistema de cola

### Criterios de Aceptación
- [ ] Múltiples peticiones se encolan correctamente
- [ ] Usuario recibe notificación de espera
- [ ] Sistema maneja timeouts adecuadamente

---

## Fase 7: Logging y Auditoría
**Objetivo**: Implementar sistema de logs para auditoría.

### Tareas
1. [ ] Configurar logging estructurado (JSON)
2. [ ] Implementar logs de auditoría para cada ejecución
3. [ ] Crear endpoint para consultar logs (opcional)
4. [ ] Implementar rotación de logs
5. [ ] Tests para sistema de logs

### Criterios de Aceptación
- [ ] Cada ejecución genera log de auditoría
- [ ] Logs incluyen: timestamp, usuario, transacción, resultado
- [ ] Logs se almacenan de forma persistente

---

## Fase 8: Testing y Documentación
**Objetivo**: Asegurar calidad y documentación completa.

### Tareas
1. [ ] Completar suite de tests (unit, integration)
2. [ ] Configurar cobertura de código
3. [ ] Actualizar documentación API (Swagger/ReDoc)
4. [ ] Crear guía de instalación y uso
5. [ ] Configurar CI/CD básico (opcional)

### Criterios de Aceptación
- [ ] Todos los tests pasan
- [ ] Cobertura mínima del 80%
- [ ] Documentación API completa y actualizada

---

## Fase 9: Integración con Frontends
**Objetivo**: Facilitar integración con frontends Astro/Laravel.

### Tareas
1. [ ] Configurar CORS para frontends
2. [ ] Crear endpoints de compatibilidad si es necesario
3. [ ] Documentar flujo de integración
4. [ ] Tests de integración con frontends simulados

### Criterios de Aceptación
- [ ] Frontends pueden consumir API sin problemas CORS
- [ ] Documentación de integración clara

---

## Notas
- **Fases independientes**: Cada fase se puede implementar y probar por separado
- **Prioridad**: Fases 1-4 son críticas para MVP; fases 5-9 son mejoras incrementales
- **Flexibilidad**: El orden puede ajustarse según necesidades urgentes
- **Scope creep**: Mantener cada fase enfocada y acotada
