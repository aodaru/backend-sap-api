# Operación manual en Windows (Fase 10)

La suite de pytest no conecta con SAP. El modo real se activa únicamente en
un host Windows controlado con `SAP_INTEGRATION_ENABLED=true`.

## Preparación

1. Instalar SAP GUI y habilitar SAP GUI Scripting en cliente y servidor SAP.
2. Abrir manualmente una sesión SAP y dejarla desbloqueada; el backend no abre
   sesiones ni realiza login concurrente.
3. Instalar `pywin32` en el mismo entorno de Python que ejecuta uvicorn.
4. Configurar `SAP_SYSTEM`, `SAP_MANDANT`, `SAP_LANG`, `SAP_CONNECTION_NAME` y
   `SAP_SESSION_INDEX` mediante variables de entorno. El flujo VK12 usa
   mandante 300 y ME12 usa EKORG 1000.
5. Mantener `API_KEYS` y las credenciales VK12 fuera del repositorio, usar HTTPS
   y permisos mínimos del usuario Windows/SAP.

## Arranque y diagnóstico

`SAP_INTEGRATION_ENABLED=false` (valor predeterminado) conserva el modo de
pruebas/simulación. En Windows, cambiarlo a `true` y arrancar uvicorn solo
después de verificar la sesión. Una sesión ausente, bloqueada o sin scripting
produce un error operativo normalizado; no se reintentan errores de negocio ni
credenciales rechazadas.

El worker es único: un lock protege toda la sesión y libera referencias en
éxito, error y timeout. VK12 recibe `credentials` por multipart, las usa solo
en memoria y las limpia en `finally`; nunca se auditan contraseñas.

## Checklist manual pendiente

- Ejecutar una fila autorizada de ME12 y verificar resultado y auditoría.
- Ejecutar una fila autorizada de VK12 y verificar que la contraseña no aparece
  en logs, status, temporales ni respuestas.
- Confirmar las dos descargas XLSX desde el frontend objetivo.
