# Plan: Integración Real con SAP GUI (Fase 10)

Plan secuencial. Cada grupo debe completarse antes de pasar al siguiente.
Marcar checkboxes al ejecutar.

## Grupo 1: Preparación del entorno Windows y sesión SAP

1. [ ] Documentar y verificar que el host de ejecución sea Windows con SAP GUI instalado, SAP GUI Scripting habilitado y `win32com` disponible.
2. [ ] Definir la configuración de conexión y sesión activa: sistema, mandante, idioma, identificador de conexión/sesión y variables de entorno necesarias.
3. [ ] Definir el comportamiento cuando no exista una sesión SAP activa, la sesión esté bloqueada o el scripting no esté disponible.
4. [x] Establecer un proveedor de sesión SAP que permita obtener, validar y liberar la sesión sin abrir sesiones concurrentes no controladas. (Proveedor win32com opcional; validación mockeada.)

## Grupo 2: Adaptadores independientes ME12 y VK12

5. [x] Definir una interfaz común para ejecutar una transacción SAP con filas validadas, contexto de job y límites operativos.
6. [x] Implementar el adaptador ME12 para mapear el template de costos a los campos y pantallas de ME12, registrar resultado por fila y detectar mensajes de SAP. (Mock; ejecución real pendiente.)
7. [x] Implementar el adaptador VK12 para mapear el template de condiciones a sus flujos de modificación, usar la sesión autenticada y detectar mensajes de SAP. (Mock; ejecución real pendiente.)
8. [x] Mantener separados el mapeo, navegación, validación de mensajes y resultados de ME12 y VK12; no compartir lógica específica de una transacción.
9. [x] Mantener un punto de selección explícito por código de transacción y rechazar transacciones no registradas.

## Grupo 3: Cola y ejecución controlada

10. [x] Integrar ambos adaptadores con una cola de un solo proceso y un único worker SAP activo.
11. [x] Garantizar que no se ejecuten dos jobs contra la misma sesión SAP, incluso ante solicitudes simultáneas o errores del worker. (Lock probado con mocks.)
12. [ ] Definir estados, posición, timestamps y respuesta de jobs para las fases `queued`, `processing`, `completed`, `failed`, `timeout` y `cancelled` cuando aplique.
13. [x] Configurar timeout de espera y timeout de ejecución, incluyendo liberación segura de la sesión y del lock al vencer.
14. [x] Implementar reintentos limitados únicamente para fallos transitorios definidos; no reintentar errores de negocio, datos inválidos ni credenciales rechazadas.
15. [ ] Definir backoff, límite de reintentos, comportamiento ante cola llena y recuperación tras caída del proceso.

## Grupo 4: Errores, auditoría y seguridad

16. [x] Normalizar errores de conexión, sesión ausente, scripting, timeout, cola, navegación SAP y validación de negocio sin exponer detalles sensibles al cliente.
17. [x] Registrar una entrada de auditoría por job ME12/VK12 con job, transacción, usuario técnico o solicitante, timestamps, duración, resultado, filas procesadas y errores por fila.
18. [x] Redactar contraseñas, API Keys y cualquier secreto de los logs, excepciones, respuestas HTTP y metadatos persistidos.
19. [x] Definir el ciclo de vida de las credenciales VK12: transporte solo por HTTPS, validación de esquema, uso en memoria durante el job y descarte al finalizar.
20. [x] Verificar que las credenciales VK12 nunca se almacenen en archivos temporales, auditoría, trazas, mensajes de error o respuestas de status. (Cobertura mock; Windows manual pendiente.)
21. [ ] Documentar permisos mínimos del usuario Windows/SAP y la gestión externa de secretos; no hardcodear credenciales.

## Grupo 5: Contrato de templates y frontend

22. [x] Garantizar `GET /api/costos/template` autenticado con `X-API-Key`, respuesta `200`, `StreamingResponse`, nombre `costos_template.xlsx` y content-type XLSX.
23. [x] Garantizar `GET /api/condiciones/template` autenticado con `X-API-Key`, respuesta `200`, `StreamingResponse`, nombre `condiciones_template.xlsx` y content-type XLSX.
24. [ ] Definir errores de ambos endpoints: `401` sin API Key o inválida y `500` si el template no puede leerse o generarse.
25. [x] Verificar que el cliente simulado envíe `X-API-Key`, interprete `Content-Disposition`, descargue el binario y no trate la respuesta como JSON.
26. [x] Añadir pruebas HTTP simuladas para descarga, nombre, content-type y API Key ausente para ambas transacciones. (Frontend real fuera de alcance.)

## Grupo 6: Pruebas sin SAP real

27. [x] Crear mocks de la sesión SAP, `win32com`/scripts existentes, ventanas, campos, mensajes y estados de conexión.
28. [x] Cubrir unitariamente los adaptadores ME12 y VK12, incluyendo éxito y error de negocio; timeout/conexión quedan cubiertos por el worker existente y mockeable.
29. [x] Cubrir la exclusión mutua de la cola con jobs concurrentes de ambas transacciones.
30. [ ] Cubrir auditoría y comprobación automatizada de que ningún secreto aparece en logs, respuestas o snapshots.
31. [ ] Cubrir los contratos HTTP de templates y las pruebas de integración frontend/backend usando cliente HTTP simulado.
32. [x] Ejecutar toda la suite en entorno sin SAP GUI y dejar separada la validación manual de Windows/SAP real.

## Grupo 7: Validación operativa y documentación

33. [x] Documentar instalación, variables de entorno, configuración de SAP GUI Scripting, sesión activa y procedimiento de arranque.
34. [ ] Documentar operación, monitoreo, auditoría, limpieza, recuperación y diagnóstico de errores.
35. [ ] Ejecutar una prueba controlada de ME12 y otra de VK12 en Windows con SAP GUI real, con datos autorizados y trazabilidad del job.
36. [ ] Confirmar descargas de ambos templates desde los frontends objetivo.
37. [ ] Actualizar la documentación de API y marcar los criterios de validación únicamente cuando exista evidencia.
38. [ ] Commit y merge de la fase según el flujo del proyecto.
