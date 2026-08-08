# Tech Stack - Backend API Automatización SAP

## Stack Actual (Confirmado)

### Backend
- **Framework**: FastAPI (async, docs automáticos Swagger/ReDoc)
- **Validación**: Pydantic models
- **Uploads**: python-multipart
- **Testing**: pytest
- **CORS**: Habilitado para frontends (Astro/Laravel)
- **Servidor**: uvicorn

### Autenticación
- **Mecanismo**: API Key via header `X-API-Key`
- **Gestión**: Keys en variables de entorno (.env)
- **Middleware**: Custom dependency en `dependencies.py`

### Integración SAP
- **Scripting**: win32com (solo Windows) para SAP GUI Scripting
- **Transacciones**: ME12, VK12 (futuras expansiones)
- **Ejecución**: Scripts VBScript/Python que interactúan con SAP GUI
- **Concurrencia**: Un solo proceso SAP a la vez

### Infraestructura
- **Plataforma**: Windows (requerido para SAP GUI)
- **Entorno**: Variables de entorno (.env)
- **Archivos**: Temporales, limpieza automática

## Dependencias Críticas
1. **SAP GUI instalado** en el servidor Windows
2. **win32com** para automatización SAP
3. **Sesión SAP activa** para ejecución de scripts

## Decisiones Técnicas
- **API Key sobre OAuth**: Simplificación para uso interno
- **FastAPI sobre Flask**: Mejor rendimiento async, docs automáticos
- **Un solo proceso**: Restricción de SAP GUI, manejo de cola
- **Logs de auditoría**: Obligatorios para trazabilidad

## Gaps identificados (Requieren implementación)
1. **Gestión de cola de peticiones**: Sistema de queue para manejar múltiples solicitudes cuando SAP está ocupado
2. **Logging centralizado**: Sistema de logs estructurados para auditoría
3. **Health checks extendidos**: Monitoreo de estado SAP GUI
4. **Rate limiting**: Control de frecuencia de llamadas
5. **Retry logic**: Reintentos automáticos para errores transitorios

## Convenciones
- **Estructura**: Seguir patrón actual (routers/, services/, models/)
- **Nomenclatura**: Python snake_case, endpoints kebab-case
- **Documentación**: Docstrings en español, README actualizado
- **Tests**: Mock completo de SAP (no tocar SAP real en tests)
