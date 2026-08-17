# Requisitos: Integración Real con SAP GUI (Fase 10)

## Alcance

Esta fase convierte la ejecución simulada de las transacciones soportadas en una integración operativa con SAP GUI en Windows, preservando el contrato REST y la capacidad de probar el backend sin tocar SAP real.

### Incluido

- Ejecución real en Windows mediante `win32com` y/o scripts SAP existentes.
- Soporte completo y separado para ME12 (costos) y VK12 (condiciones).
- Obtención y validación de una sesión SAP GUI activa, con configuración documentada.
- Cola de un solo proceso y un único job SAP activo a la vez.
- Timeouts, reintentos acotados, backoff y liberación segura de recursos.
- Errores normalizados para conexión, sesión, scripting, navegación, negocio y cola.
- Auditoría por ejecución y por transacción, sin secretos.
- Protección de credenciales usadas por VK12.
- Contratos autenticados de descarga para `GET /api/costos/template` y `GET /api/condiciones/template`.
- Pruebas unitarias y de integración con mocks completos de SAP GUI, `win32com` y scripts.
- Pruebas frontend simuladas para las dos descargas.

### No incluido

- Desarrollo o rediseño funcional de las transacciones SAP; se consumen los flujos aprobados existentes.
- Soporte para Linux, macOS, contenedores sin escritorio Windows o múltiples hosts SAP concurrentes.
- Más de una sesión SAP o más de un proceso SAP activo simultáneamente.
- Nuevas transacciones distintas de ME12 y VK12.
- Persistencia distribuida de la cola, Redis, base de datos de jobs o alta disponibilidad.
- Almacenamiento local de contraseñas, gestión de identidad corporativa o sustitución del API Key por OAuth.
- Desarrollo de un frontend nuevo; solo se define y prueba el consumo del contrato existente.
- Pruebas automatizadas contra un sistema SAP real o datos productivos.
- Cambios en `changelog.md` como parte de esta fase.

## Contrato funcional y técnico

### Templates

Ambos endpoints requieren el header `X-API-Key` y deben devolver un `StreamingResponse` binario:

| Endpoint | Archivo descargado | Content-Type esperado |
|----------|--------------------|-----------------------|
| `GET /api/costos/template` | `costos_template.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |
| `GET /api/condiciones/template` | `condiciones_template.xlsx` | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` |

La respuesta exitosa es `200` y debe incluir `Content-Disposition: attachment; filename=<nombre>`. Sin API Key o con una inválida se responde `401`; un fallo de lectura o generación del archivo se responde `500` sin filtrar rutas internas.

El frontend debe enviar `X-API-Key`, leer la respuesta como Blob/stream, respetar el nombre indicado por `Content-Disposition` y ofrecer la descarga sin intentar parsear el XLSX como JSON. Deben probarse ambas rutas desde un cliente frontend simulado.

### Ejecución SAP

- ME12 recibe las filas del template de costos y usa exclusivamente su adaptador.
- VK12 recibe las filas del template de condiciones y usa exclusivamente su adaptador.
- Cada adaptador traduce datos, navega por la transacción, interpreta mensajes de SAP y devuelve resultados por fila.
- La sesión se valida antes de ejecutar y se libera o deja en estado seguro al terminar.
- La cola serializa todos los jobs de ambas transacciones; un job en ejecución bloquea cualquier otro acceso SAP.

## Decisiones

| ID | Decisión | Racional | Alternativa descartada |
|----|----------|----------|------------------------|
| D1 | Un adaptador independiente para ME12 y otro para VK12 | Sus pantallas, campos, mensajes y reglas de negocio son diferentes | Un script monolítico con condicionales mezclados |
| D2 | `win32com` y scripts existentes como frontera de infraestructura | SAP GUI exige Windows y ya existen automatizaciones reutilizables | Reimplementar SAP con llamadas HTTP no disponibles |
| D3 | Una cola con un solo proceso/worker SAP | SAP GUI no admite ejecuciones concurrentes seguras en la misma sesión | Ejecutar jobs en paralelo |
| D4 | Reintentar solo fallos transitorios y con límite | Evita duplicar cambios ante errores de negocio o de datos | Reintentar cualquier excepción |
| D5 | `StreamingResponse` para los templates | Mantiene el contrato de descarga binaria y reduce acoplamiento con el frontend | Responder JSON con contenido codificado |
| D6 | Credenciales VK12 solo en memoria durante el job | Reduce exposición y mantiene compatibilidad con el contrato multipart actual | Persistir credenciales o incluirlas en auditoría |
| D7 | Mocks completos en CI y prueba real manual separada | Los tests deben ser deterministas y no alterar SAP | Conectar SAP real durante pytest |

## Contexto

- **Misión**: `specs/mission.md` establece automatización REST de ME12/VK12, API Key, un proceso SAP y auditoría obligatoria.
- **Stack**: FastAPI, Pydantic, `python-multipart`, pytest, uvicorn y CORS para Astro/Laravel, según `specs/tech-stack.md`.
- **Integración**: SAP GUI instalado en un servidor Windows, scripting habilitado, `win32com` y sesión SAP activa.
- **Autenticación**: header `X-API-Key`, configurado mediante variables de entorno.
- **Entrada**: archivos Excel validados por los servicios existentes; VK12 conserva el campo multipart `credentials` con JSON validado.
- **Salidas**: estado de job, resultados por fila, auditoría y descarga de templates XLSX.

## Configuración requerida

- Host Windows dedicado o controlado con SAP GUI Scripting habilitado.
- Identificador de conexión/sesión SAP y parámetros de sistema, mandante e idioma mediante configuración segura.
- `SAP_EXECUTION_TIMEOUT`, límites de reintentos y backoff configurables sin secretos en el repositorio.
- API Keys fuera del código fuente y permisos mínimos para el proceso Windows.
- Política de HTTPS y almacenamiento/rotación externa de secretos para credenciales VK12.

## Dependencias

- **Fase 2**: autenticación por API Key.
- **Fase 4**: endpoint y validación de archivos de ME12.
- **Fase 5**: endpoint, validación y credenciales de VK12.
- **Fase 6**: cola, timeout y reintentos.
- **Fase 7**: logging y auditoría.
- **Fase 9**: CORS y consumo desde frontends.
- **Infraestructura Windows/SAP**: SAP GUI, scripting, sesión activa, `win32com` y scripts aprobados.

## Riesgos identificados

| Riesgo | Mitigación |
|--------|------------|
| SAP GUI no tiene sesión activa o pierde conexión | Health check previo, error explícito, liberación del lock y reintento solo si es transitorio |
| Automatización depende de pantallas o tiempos variables | Adaptadores aislados, esperas acotadas, detección de mensajes y timeout por etapa |
| Reintento duplica una modificación SAP | Clasificación estricta de errores y confirmación de estado antes de reintentar |
| Dos jobs acceden simultáneamente a SAP | Lock/worker único probado con jobs ME12 y VK12 concurrentes |
| Contraseña VK12 termina en logs o temporales | Redacción, no persistencia, descarte en `finally` y pruebas de ausencia de secretos |
| Frontend descarga una respuesta incorrecta | Contrato explícito de status, headers, nombre, content-type y pruebas de Blob/stream |
| Diferencias entre mocks y SAP real | Checklist manual en Windows con una ejecución controlada de cada transacción |
