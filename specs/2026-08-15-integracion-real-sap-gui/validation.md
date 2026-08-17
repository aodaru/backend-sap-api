# Validación: Integración Real con SAP GUI (Fase 10)

## Estado de la fase

**🟨 PARCIAL: validación automatizada sin SAP real completada; validación manual Windows pendiente.**

## Criterios de éxito

### 1. Entorno y sesión SAP

- [ ] El host Windows tiene SAP GUI, SAP GUI Scripting y `win32com` configurados.
- [x] La configuración de sistema, mandante, idioma, conexión y sesión activa está documentada y no contiene secretos en el repositorio.
- [x] El backend detecta sesión ausente, bloqueada o no disponible y devuelve un error operativo seguro (mock).
- [x] La sesión se obtiene y libera correctamente en éxito, error y timeout (mock).

### 2. Adaptador ME12

- [x] El adaptador ME12 transforma las filas válidas del template de costos en acciones de ME12 (mock de scripting).
- [x] El resultado identifica filas procesadas, exitosas y fallidas y conserva los mensajes relevantes de SAP (mock).
- [x] Errores de datos o negocio no se reintentan ni producen cambios silenciosos (matriz mock).
- [ ] Una prueba controlada en Windows ejecuta ME12 con datos autorizados y deja auditoría verificable.

### 3. Adaptador VK12 y credenciales

- [x] El adaptador VK12 transforma los flujos válidos del template de condiciones en acciones de VK12 (mock de scripting).
- [x] El contrato multipart conserva `file` y `credentials` JSON con validación previa (prueba HTTP).
- [x] Las credenciales solo se usan en memoria durante la ejecución y no aparecen en logs, auditoría, temporales, errores ni status (prueba HTTP/unitaria).
- [x] Un error de autenticación SAP se informa sin revelar la contraseña y no se reintenta automáticamente (ME12/VK12 mock).
- [ ] Una prueba controlada en Windows ejecuta VK12 con datos autorizados y deja auditoría verificable.

### 4. Cola, timeouts y reintentos

- [x] Jobs ME12 y VK12 concurrentes se procesan estrictamente de uno en uno (mock).
- [x] Un segundo job no puede adquirir la sesión mientras el primero está en ejecución.
- [x] La cola reporta posición y estados coherentes desde `queued` hasta `completed`, `failed`, `cancelled` o `timeout`.
- [x] Un timeout libera sesión, lock y recursos, y queda registrado en auditoría mock.
- [x] Los fallos transitorios aplican backoff y el máximo configurado de reintentos.
- [x] Los errores de negocio, validación y credenciales no se reintentan.
- [x] Cola llena, job inexistente, cancelación y recuperación tras fallo del worker tienen respuestas documentadas y verificadas.

### 5. Contrato de descarga y frontend

- [x] `GET /api/costos/template` con API Key válida responde `200` mediante `StreamingResponse`.
- [x] La descarga de costos incluye `Content-Disposition: attachment; filename=costos_template.xlsx`.
- [x] `GET /api/condiciones/template` con API Key válida responde `200` mediante `StreamingResponse`.
- [x] La descarga de condiciones incluye `Content-Disposition: attachment; filename=condiciones_template.xlsx`.
- [x] Ambas respuestas usan `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` y contienen un XLSX legible.
- [x] Sin `X-API-Key` o con una inválida, ambas rutas responden `401`.
- [x] Fallos de lectura/generación responden `500` sin exponer rutas ni detalles internos.
- [x] Las pruebas frontend simuladas descargan ambas respuestas como binario y respetan nombre y content-type.

### 6. Pruebas sin SAP real

- [x] La suite usa mocks de sesión, `win32com`, scripts, navegación, mensajes y errores de SAP.
- [x] Las pruebas cubren éxito, sesión ausente, desconexión, timeout, error de negocio y reintento para ambos adaptadores.
- [x] Las pruebas de cola verifican exclusión mutua entre ME12 y VK12.
- [x] Las pruebas de auditoría verifican transacción, job, timestamps, duración, filas y resultado.
- [x] Una aserción automatizada confirma que las credenciales VK12 no aparecen en status, excepciones, logs, auditoría ni temporales.
- [x] Toda la suite pasa en un entorno sin SAP GUI ni conexión SAP real.

## Cómo verificar

```bash
# Ejecutar toda la suite sin conectar con SAP real
pytest -v

# Ejecutar contratos de templates, autenticación y frontend simulado
pytest tests/test_costos.py tests/test_condiciones.py tests/test_auth.py tests/test_cors.py tests/integration/test_endpoints.py -v

# Ejecutar las pruebas de cola y resiliencia
pytest tests/test_queue.py tests/unit/test_queue_service.py -v
```

En Windows, con una sesión SAP de pruebas y datos autorizados:

1. Verificar el estado de la sesión y ejecutar un job ME12 controlado.
2. Verificar el resultado por fila, el estado final y la auditoría sin secretos.
3. Ejecutar un job VK12 controlado con credenciales suministradas por el mecanismo aprobado.
4. Verificar que la contraseña no aparece en logs, temporales ni respuesta de status.
5. Solicitar ambas URLs de template desde los frontends y confirmar la descarga con sus nombres esperados.

## Criterio de merge a main

- [ ] Todos los criterios técnicos y de seguridad están marcados con evidencia.
- [ ] La suite completa pasa sin SAP real.
- [ ] La prueba manual de Windows/SAP valida ME12 y VK12 por separado.
- [ ] Los contratos de descarga fueron probados desde los frontends objetivo.
- [ ] La documentación operativa y de configuración está actualizada.
- [ ] PR abierto y revisión completada.

## Anti-criterios (lo que NO debe pasar)

- ❌ Se ejecutan dos transacciones SAP simultáneamente sobre la misma sesión.
- ❌ Se intenta probar contra SAP real desde pytest o CI.
- ❌ Se reintenta una modificación por un error de negocio o credenciales inválidas.
- ❌ Una contraseña VK12, API Key o secreto aparece en logs, temporales, auditoría o respuestas.
- ❌ El frontend recibe JSON, un nombre incorrecto o un content-type distinto al XLSX al descargar templates.
- ❌ Los endpoints de template funcionan sin `X-API-Key` válida.
- ❌ Un timeout deja la sesión SAP o el lock ocupados para el siguiente job.
