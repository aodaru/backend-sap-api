# Diagnóstico de HTTP 503 en `/api/costos/execute`

## Hallazgo

El flujo ejecuta el job de forma síncrona dentro del POST. El worker normaliza
los errores para el cliente, pero antes no conservaba un código operativo
consultable: por eso todos los fallos podían aparecer como `No se pudo
completar el job SAP`. Además, el proveedor Win32 distinguía `win32com` ausente,
SAPGUI no encontrado, conexión inexistente, sesión inexistente y sesión ocupada
solo parcialmente (o los convertía en un error de conexión genérico).

## Cambio aplicado

- Los errores de la frontera SAP tienen códigos operativos no sensibles, por
  ejemplo `integration_disabled`, `scripting_unavailable`, `sapgui_not_found`,
  `connection_unavailable`, `session_unavailable` y `session_busy`.
- La auditoría de ME12 y VK12 registra `operational_code`, etapa diagnóstica y
  si el fallo es reintentable. El nombre de archivo se reduce a su basename.
- El HTTP continúa usando mensajes públicos fijos y estados seguros (503 para
  disponibilidad/configuración, 504 para timeout, 429 para cola llena). No se
  devuelve texto de excepciones, rutas, credenciales ni secretos.
- Los tests usan mocks y no validan SAP real.
- Los códigos operativos pasan por una whitelist cerrada; códigos arbitrarios
  se normalizan a `sap_error`. Las respuestas HTTP usan mensajes constantes
  por código y nunca toman `public_message` de excepciones arbitrarias.
- Las pruebas HTTP y de auditoría cubren integración deshabilitada,
  `win32com` ausente, SAPGUI/conexión/sesión ausente y sesión ocupada, además
  de comprobar que no se filtran secretos ni rutas.
- ME12 tiene una prueba HTTP específica que verifica `integration_disabled`,
  job `failed`, ausencia de auditoría `success`, basename seguro y ausencia de
  secretos/rutas.

## Checklist de diagnóstico en Windows

1. Confirmar que `SAP_INTEGRATION_ENABLED=true` en el proceso del backend.
2. Confirmar `win32com`/pywin32 instalado en el mismo entorno virtual que ejecuta
   Uvicorn.
3. Abrir SAP Logon y verificar que el proceso SAP GUI está iniciado.
4. Verificar que SAP GUI Scripting está habilitado en cliente y servidor.
5. Confirmar `SAP_CONNECTION_NAME` (si se usa) y que existe una conexión abierta.
6. Confirmar que `SAP_SESSION_INDEX` apunta a una sesión activa del mandante
   300 y que no está ocupada por otra automatización.
7. Consultar el log de auditoría por `job_id` y usar `operational_code`; nunca
   solicitar ni registrar contraseñas, API keys o rutas internas.

La integración SAP real no queda validada por esta mejora; solo se validan
clasificación, seguridad y flujo con dobles de prueba.

## Verificación final

- `pytest`: 292 pruebas aprobadas.
- `./init.sh`: entorno y tests disponibles.
- `git diff --check`: sin errores.
- Los `.pyc` generados/modificados durante esta sesión no forman parte del
  diff; no se eliminó trabajo preexistente no relacionado.
- Evidencia final: `git diff --name-only -- '*.pyc'` no devuelve archivos.
