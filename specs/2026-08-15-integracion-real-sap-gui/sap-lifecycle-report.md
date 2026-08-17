# SAP GUI Lifecycle - Reporte de Implementación

**Fecha**: 2026-08-15
**Estado**: ✅ Completado
**Tests**: 293/293 passing

## Resumen

Reemplazo del enfoque `GetObject("SAPGUI")` por el ciclo completo de SAP GUI
(equivalente al desktop `SapClient`) en el backend.

## Archivos modificados

### 1. `services/sap_session.py` — `Win32ComSapSessionProvider`

**Antes**: Solo inspeccionaba conexiones/sesiones ya abiertas via `GetObject`.

**Ahora**: Ciclo completo:
- `_get_sap_gui()`: Abre SAP Logon + espera activa con reintentos (como desktop `connect()`)
- `_create_connection()`: `application.OpenConnection(system, True)`
- `_setup_session()`: Espera 3s, toma sesión, maximiza ventana
- `_login()`: Llena mandt/usuario/contraseña/idioma, `SendVKey(0)`, maneja popup "Session already open"
- `_find_existing_connection()` + `_use_existing_session()`: Ruta compatible cuando SAP ya está corriendo
- `release()`: `CloseSession` → `Exit` → `gc.collect()` → `taskkill` fallback (como desktop `close()`)

**Diseño dual-ruta**:
1. Si SAP GUI ya tiene conexiones activas → usarlas (compatibilidad)
2. Si no → ciclo completo: abrir SAP Logon → conectar → login → retornar sesión

Esto garantiza que los tests existentes (que mockean conexiones existentes) sigan pasando,
mientras el path de producción realiza el ciclo completo.

**Importaciones**: `win32com` y `pythoncom` se importan DENTRO de `acquire()` (no a nivel módulo) para CI en Linux.

### 2. `config.py` — Nuevas variables

```python
sap_logon_path: str = r"C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe"
sap_username: str = ""
sap_password: str = ""
```

Los campos existentes (`sap_system`, `sap_mandant`, `sap_lang`, `sap_integration_enabled`)
se mantienen. Los deprecated (`sap_connection_name`, `sap_session_index`) se conservan
para retrocompatibilidad.

### 3. `.env.example` — Nuevas variables

```env
SAP_LOGON_PATH=C:\Program Files (x86)\SAP\FrontEnd\SAPgui\saplogon.exe
SAP_USERNAME=
SAP_PASSWORD=
```

### 4. `services/sap_executor.py` — Provider creation

```python
self._provider = provider or (
    Win32ComSapSessionProvider(
        sap_logon_path=settings.sap_logon_path,
        system=settings.sap_system,
        mandt=settings.sap_mandant,
        username=settings.sap_username,
        password=settings.sap_password,
        language=settings.sap_lang,
    )
    if settings.sap_integration_enabled else NullSapSessionProvider()
)
```

ME12 usa credenciales del `.env` (fijas). VK12 sobreescribe via `credentials` del multipart.

## No modificados

- `services/sap_adapters.py` — Sin cambios (navegación se implementará después)
- `services/sap_errors.py` — Sin cambios
- Tests existentes — Sin cambios

## Verificación

- `pytest -q`: **293/293 passed** (0 failures)
- `./init.sh`: **Inicialización validada**
- Python 3.8 compatible (sin PEP 604 ni genéricos built-in)
- CI/Linux compatible (win32com importado dentro de métodos)

## Decisión de diseño: pythoncom separado

`pythoncom.CoInitialize()` se importa con `try/except ImportError` separado del
`win32com.client`. Razón: los tests mockean `win32com.client` pero no `pythoncom`.
En Linux/CI, `pythoncom` no existe — se omite `CoInitialize()` silenciosamente.
En Windows/producción, `pythoncom` está disponible y se ejecuta `CoInitialize()`.
