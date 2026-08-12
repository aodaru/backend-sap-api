# Guía de Uso de la API

Ejemplos prácticos para interactuar con el Backend API de Automatización SAP.

## URLs Disponibles

| URL | Descripción |
|-----|-------------|
| `http://localhost:8000/docs` | Swagger UI (documentación interactiva) |
| `http://localhost:8000/redoc` | ReDoc (documentación alternativa) |
| `http://localhost:8000/openapi.json` | Especificación OpenAPI |

## Autenticación

Todos los endpoints (excepto `/api/health`) requieren una API Key en el header:

```
X-API-Key: tu-api-key
```

## Endpoints

### Health Check (público)

```bash
curl http://localhost:8000/api/health
```

**Respuesta:**
```json
{
  "status": "ok",
  "message": "Servicio listo para procesar pedidos",
  "timestamp": "2026-08-11T12:00:00Z"
}
```

### Root

```bash
curl -H "X-API-Key: tu-api-key" http://localhost:8000/
```

**Respuesta:**
```json
{
  "message": "Backend API - Automatización SAP",
  "docs": "/docs",
  "health": "/api/health"
}
```

---

## Costos (ME12)

### 1. Descargar Template

```bash
curl -H "X-API-Key: tu-api-key" \
  -o costos_template.xlsx \
  http://localhost:8000/api/costos/template
```

### 2. Upload y Validación

```bash
curl -H "X-API-Key: tu-api-key" \
  -F "file=@datos_costos.xlsx" \
  http://localhost:8000/api/costos/upload
```

**Respuesta (válido):**
```json
{
  "filename": "datos_costos.xlsx",
  "row_count": 10,
  "valid": true,
  "validations": []
}
```

**Respuesta (inválido):**
```json
{
  "filename": "datos_costos.xlsx",
  "row_count": 0,
  "valid": false,
  "validations": [
    {
      "row": 1,
      "field": "columns",
      "error": "Columnas faltantes: Material, Proveedor"
    }
  ]
}
```

### 3. Ejecutar ME12

```bash
curl -H "X-API-Key: tu-api-key" \
  -X POST \
  -F "file=@datos_costos.xlsx" \
  http://localhost:8000/api/costos/execute
```

**Respuesta (202 Accepted):**
```json
{
  "job_id": "abc123-def456",
  "status": "completed",
  "message": "ME12 ejecutado exitosamente"
}
```

### 4. Consultar Estado del Job

```bash
curl -H "X-API-Key: tu-api-key" \
  http://localhost:8000/api/costos/status/abc123-def456
```

**Respuesta:**
```json
{
  "job_id": "abc123-def456",
  "status": "completed",
  "progress": 100,
  "results": {
    "processed": 10,
    "successful": 10,
    "failed": 0,
    "message": "ME12 ejecutado exitosamente"
  }
}
```

---

## Condiciones (VK12)

### 1. Descargar Template

```bash
curl -H "X-API-Key: tu-api-key" \
  -o condiciones_template.xlsx \
  http://localhost:8000/api/condiciones/template
```

### 2. Upload y Validación

```bash
curl -H "X-API-Key: tu-api-key" \
  -F "file=@datos_condiciones.xlsx" \
  http://localhost:8000/api/condiciones/upload
```

### 3. Ejecutar VK12

```bash
curl -H "X-API-Key: tu-api-key" \
  -X POST \
  -F "file=@datos_condiciones.xlsx" \
  -F 'credentials={"system":"ERQ","mandt":"200","username":"user","password":"pass","language":"ES"}' \
  http://localhost:8000/api/condiciones/execute
```

**Respuesta (202 Accepted):**
```json
{
  "job_id": "xyz789-abc123",
  "status": "completed",
  "message": "VK12 ejecutado exitosamente"
}
```

### 4. Consultar Estado

```bash
curl -H "X-API-Key: tu-api-key" \
  http://localhost:8000/api/condiciones/status/xyz789-abc123
```

---

## Cola de Peticiones

### Ver Estadísticas

```bash
curl -H "X-API-Key: tu-api-key" \
  http://localhost:8000/api/queue/stats
```

**Respuesta:**
```json
{
  "total_queued": 2,
  "total_processing": 1,
  "total_completed": 10,
  "total_failed": 1,
  "total_cancelled": 0,
  "max_queue_size": 5
}
```

### Consultar Estado de Petición

```bash
curl -H "X-API-Key: tu-api-key" \
  http://localhost:8000/api/queue/status/abc123-def456
```

### Cancelar Petición

```bash
curl -H "X-API-Key: tu-api-key" \
  -X DELETE \
  http://localhost:8000/api/queue/abc123-def456
```

---

## Logs de Auditoría

### Consultar Logs

```bash
curl -H "X-API-Key: tu-api-key" \
  "http://localhost:8000/api/logs?limit=10&offset=0"
```

**Filtros disponibles:**
- `transaction` - Filtrar por ME12 o VK12
- `user_id` - Filtrar por usuario
- `date_from` - Fecha inicio (YYYY-MM-DD)
- `date_to` - Fecha fin (YYYY-MM-DD)
- `status` - Filtrar por estado (success, error)
- `limit` - Máximo de resultados (1-500, default: 50)
- `offset` - Offset para paginación

### Consultar Logs por Job ID

```bash
curl -H "X-API-Key: tu-api-key" \
  http://localhost:8000/api/logs/abc123-def456
```

---

## Estructura del Template Excel

### Costos (ME12)

| Columna | Descripción | Tipo |
|---------|-------------|------|
| Material | Código del material SAP | Texto |
| Proveedor | Código del proveedor | Texto |
| Org_Compras | Organización de compras | Texto |
| Tipo_Info | Tipo de info record | Texto |
| Tipo_Condicion | Tipo de condición | Texto |
| Nuevo_Precio | Nuevo precio unitario | Numérico |
| Moneda | Moneda (MXN, USD, etc.) | Texto |
| Unidad_Precio | Unidad del precio | Texto |
| Unidad_Medida | Unidad de medida | Texto |
| Valido_Desde | Fecha inicio vigencia | YYYYMMDD |
| Valido_Hasta | Fecha fin vigencia | YYYYMMDD |

### Condiciones (VK12)

| Columna | Descripción | Tipo |
|---------|-------------|------|
| MATERIAL | Código del material | Numérico |
| UNIDAD_DE_MEDIDA | Unidad (UN, KG, ST) | Texto |
| IMPORTE | Valor de la condición | Numérico |
| GRUPO_ARTICULO | Grupo de artículos (9 dígitos) | Numérico |
| ORG_VENTA | Organización de venta (1000) | Texto |
| CAN_DISTR | Canal de distribución | Texto |
| SECTOR | Sector | Texto |
| RAMO | Ramo (ZDET, ZCON, etc.) | Texto |
| TIPO_MODIFICACION | Flujo de modificación | Texto |

---

## Errores Comunes

| HTTP Status | Descripción | Solución |
|-------------|-------------|----------|
| 401 | API Key inválida o ausente | Verificar header `X-API-Key` |
| 422 | Archivo no es Excel | Usar formato .xlsx o .xls |
| 400 | Datos de Excel inválidos | Revisar validaciones en respuesta |
| 429 | Cola de peticiones llena | Esperar a que se procesen peticiones |
| 404 | Job no encontrado | Verificar el job_id |
