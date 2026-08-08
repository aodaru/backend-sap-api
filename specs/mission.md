# Mission: Backend API - Automatización SAP GUI

## Propósito
Crear un backend centralizado y extensible para ejecutar flujos/scripts en SAP GUI mediante API REST, permitiendo la automatización de transacciones SAP para usuarios finales.

## Objetivos Principales
1. **Automatización de transacciones SAP**: Ejecutar scripts que interactúen con SAP GUI (ME12, VK12, y futuras transacciones).
2. **API REST segura**: Endpoints con autenticación por API Key para controlar acceso.
3. **Gestión de concurrencia**: Manejar ejecuciones SAP de forma secuencial (un proceso a la vez) con cola de peticiones.
4. **Logging y auditoría**: Registrar todas las ejecuciones para trazabilidad.
5. **Extensibilidad**: Diseñar el backend para agregar nuevas transacciones SAP con mínimo esfuerzo.

## Audiencia Objetivo
- **Usuarios finales**: Personal que necesita ejecutar transacciones SAP de forma automatizada sin conocimientos técnicos avanzados.
- **Desarrolladores**: Equipos que construirán frontends (Astro/Laravel) para interactuar con el backend.
- **Equipos SAP**: Administradores que supervisan y controlan las automatizaciones.

## Alcance Actual (Fase 1)
- **Transacciones soportadas**: ME12 (modificación masiva de precios - Info Records de compra) y VK12 (modificación masiva de condiciones de precio).
- **Scripts existentes**: Lógica ya desarrollada en carpeta "web" de ME12 (archivo Excel) y logs en carpeta web de costos de ME12.
- **Integración**: Backend接收ará datos de formularios Astro/Laravel y devolverá logs con resultados.

## Restricciones
- **Plataforma**: Windows obligatorio (SAP GUI requiere win32com).
- **SAP GUI**: Instalado y configurado en el servidor.
- **Concurrencia**: Un solo proceso SAP activo a la vez; el backend notificará al usuario o gestionará cola.
- **Seguridad**: Autenticación por API Key, logs de auditoría obligatorios.

## Fuera de Alcance (Fase 1)
- Desarrollo de scripts SAP (ya existen para ME12/VK12).
- Frontend (se desarrollará por separado en Astro/Laravel).
- Soporte para múltiples sesiones SAP concurrentes.
