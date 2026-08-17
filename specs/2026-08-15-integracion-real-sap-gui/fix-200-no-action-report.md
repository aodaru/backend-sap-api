# Diagnóstico y corrección: `200` sin acción en ME12/VK12

Fecha: 2026-08-15

## Diagnóstico del flujo real

El endpoint no devolvía un `200` HTTP de ejecución: declaraba `202`, pero
esperaba el job de la cola antes de responder y devolvía el estado
`completed` aunque la ejecución no hubiera navegado SAP. La causa era el
camino por defecto:

1. `routers/costos.py` y `routers/condiciones.py` crean el job y llaman al
   servicio de ejecución antes de construir la respuesta.
2. El servicio actualiza el job a `queued`/`processing`, lo entrega a
   `RequestQueue._worker_loop` y espera su callback.
3. El callback llama a `sap_executor.execute`, que selecciona `Me12Adapter` o
   `Vk12Adapter` y adquiere la sesión.
4. Con `SAP_INTEGRATION_ENABLED=false`, el executor construía
   `NullSapSessionProvider`; su `acquire()` retornaba `None`.
5. `_Adapter._run_rows()` interpretaba `session is None` como “no navegar” y
   aun así agregaba cada fila como exitosa. El servicio marcaba el job como
   `completed`, y el router registraba auditoría de éxito.

Por tanto, el worker sí llamaba el adaptador, pero el proveedor nulo y el
adaptador convertían una no-ejecución en éxito. Los adaptadores no eran solo
mapeo: sus puertos sí navegan (`start_transaction`, campos, submit/ENTER y
save), interpretan mensajes y confirman el resultado. También se verificó que
`Win32ComSapSessionProvider` obtiene `SAPGUI`, `GetScriptingEngine`, filtra la
conexión, comprueba el índice/estado ocupado y entrega el objeto `session` al
adaptador. Esa parte no se modifica y no se ha probado contra Windows.

## Cambios realizados

- Añadido `SapIntegrationDisabledError` (`integration_disabled`, HTTP 503).
- `NullSapSessionProvider.acquire()` ahora falla explícitamente; nunca puede
  simular una sesión.
- El executor rechaza cualquier ejecución cuando
  `SAP_INTEGRATION_ENABLED` no es verdadero, incluso si el proveedor fue
  inyectado. Con integración habilitada conserva el proveedor real o el
  proveedor/script inyectado y llama al adaptador seleccionado.
- Los adaptadores rechazan una sesión nula antes de procesar filas.
- Los errores siguen el camino queue → servicio → router: el job queda
  `failed` con mensaje seguro y la API devuelve 503/422/504 según el error,
  nunca `completed`.
- VK12 exige mandante `300`; ME12 conserva `EKORG=1000`.
- `.env.example`, README y pruebas documentan `SAP_INTEGRATION_ENABLED` y la
  configuración de conexión/sesión.
- La suite usa un proveedor falso inyectado, sin SAP real. Se añadió la
  regresión que demuestra que el proveedor nulo no navega ni devuelve éxito,
  además de cobertura de proveedor, configuración, sesión y adaptador.

## Uso correcto de `.env`

Modo seguro/local (no ejecuta SAP):

```env
SAP_INTEGRATION_ENABLED=false
```

En Windows, con SAP GUI abierto, Scripting habilitado y una sesión activa:

```env
SAP_INTEGRATION_ENABLED=true
SAP_SYSTEM=PRD
SAP_MANDANT=300
SAP_LANG=ES
SAP_CONNECTION_NAME=Nombre visible de la conexión SAP GUI
SAP_SESSION_INDEX=0
```

VK12 debe enviar credenciales con `mandt: "300"`; no se guarda la contraseña.
ME12 usa filas con `Org_Compras=1000`. La API Key y las credenciales deben
permanecer fuera del repositorio.

## Evidencia

- `pytest -q`: **280 passed**, 312 warnings, 0 failures.
- No se conectó a SAP real.
- No se ejecutó ni se marca como verificada la ejecución real en Windows.
- La prueba de regresión está en
  `tests/unit/test_sap_integration.py::test_disabled_integration_never_returns_success_or_navigates`.
- La prueba HTTP deshabilitada está en
  `test_http_disabled_integration_returns_503_failed_job_without_success_audit`.
- El recorrido completo está en
  `test_http_end_to_end_router_queue_worker_executor_adapter_with_fake_provider`.

## Correcciones del review

- Se añadió una prueba HTTP real con `SAP_INTEGRATION_ENABLED=false` que verifica
  `503`, el detalle explícito, el estado `failed` del job y la ausencia de una
  auditoría `success`. La fixture global que habilita SAP quedó excluida de esa
  prueba mediante un marker.
- Se añadió una prueba end-to-end router → queue → worker → executor → adaptador
  usando un proveedor fake que registra la navegación ME12 y confirma `EKORG=1000`.
- El docstring de VK12 y el default de `config.py` usan ahora mandante `300`,
  coherente con el contrato y la validación del executor.
- No se validó Windows ni SAP real; los tests siguen usando dobles y no conectan
  con SAP GUI.

## Cierre de bloqueantes restantes

- Se unificaron las referencias de mandante VK12 a `300` en `docs/INSTALL.md`,
  `docs/USAGE.md`, el modelo y las pruebas, manteniendo `config.py`, el router y
  este reporte coherentes.
- Se retiraron del working tree los artefactos `.pyc` generados/modificados; no
  se eliminaron fuentes ni trabajo no relacionado.
- La ejecución real contra SAP GUI en Windows continúa sin validar.
- Verificaciones finales: `pytest -q` (**280 passed**, 312 warnings) y
  `./init.sh` (**Inicialización validada**).
