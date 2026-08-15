# Guía de Integración - Frontends

## Configuración CORS

El backend está configurado para permitir requests desde frontends Astro y Laravel.

### Orígenes permitidos

| Frontend | Puerto | URL |
|----------|--------|-----|
| Astro (dev) | 4321 | `http://localhost:4321` |
| Laravel (dev) | 8080 | `http://localhost:8080` |
| Astro (dev) | 3000 | `http://localhost:3000` |

### Variables de entorno

```env
# CORS - Orígenes permitidos (separados por coma)
CORS_ORIGINS=http://localhost:4321,http://localhost:8080,http://localhost:3000
```

## Autenticación

Todos los endpoints (excepto `/api/health`) requieren API Key via header:

```
X-API-Key: mi-api-key-secreta
```

## Endpoints disponibles

### Health Check (sin auth)

```http
GET /api/health
```

Respuesta:
```json
{
  "status": "ok",
  "message": "Backend funcionando correctamente",
  "timestamp": "2026-08-12T10:00:00"
}
```

### Costos (ME12)

```http
GET /api/costos/template          # Descargar Excel template
POST /api/costos/upload           # Subir Excel con datos
POST /api/costos/execute          # Ejecutar transacción
GET /api/costos/status/{job_id}   # Consultar estado
```

### Condiciones (VK12)

```http
GET /api/condiciones/template          # Descargar Excel template
POST /api/condiciones/upload           # Subir Excel con datos
POST /api/condiciones/execute          # Ejecutar transacción
GET /api/condiciones/status/{job_id}   # Consultar estado
```

## Ejemplos de consumo

### JavaScript (fetch)

```javascript
const API_BASE = 'http://localhost:8000';
const API_KEY = 'mi-api-key-secreta';

// Health check
const health = await fetch(`${API_BASE}/api/health`);
const healthData = await health.json();
console.log(healthData.status); // "ok"

// Descargar template
const template = await fetch(`${API_BASE}/api/costos/template`, {
  headers: { 'X-API-Key': API_KEY }
});
const blob = await template.blob();
const url = URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'template_costos.xlsx';
a.click();

// Subir Excel
const formData = new FormData();
formData.append('file', excelFile);
const upload = await fetch(`${API_BASE}/api/costos/upload`, {
  method: 'POST',
  headers: { 'X-API-Key': API_KEY },
  body: formData
});
const uploadData = await upload.json();
console.log(uploadData.job_id); // ID del job

// Ejecutar transacción
const execute = await fetch(`${API_BASE}/api/costos/execute`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({ job_id: uploadData.job_id })
});
const executeData = await execute.json();
console.log(executeData.status); // "queued"

// Consultar estado
const status = await fetch(`${API_BASE}/api/costos/status/${uploadData.job_id}`, {
  headers: { 'X-API-Key': API_KEY }
});
const statusData = await status.json();
console.log(statusData.status); // "completed", "processing", "queued"
```

### Astro

```astro
---
// src/pages/index.astro
const API_BASE = 'http://localhost:8000';
const API_KEY = import.meta.env.PUBLIC_API_KEY;

const response = await fetch(`${API_BASE}/api/health`, {
  headers: { 'X-API-Key': API_KEY }
});
const health = await response.json();
---

<h1>Status: {health.status}</h1>
<p>{health.message}</p>
```

### Laravel (PHP)

```php
<?php
// app/Http/Controllers/SapController.php

namespace App\Http\Controllers;

use Illuminate\Support\Facades\Http;

class SapController extends Controller
{
    private $apiBase = 'http://localhost:8000';
    private $apiKey = 'mi-api-key-secreta';

    public function health()
    {
        $response = Http::withHeaders([
            'X-API-Key' => $this->apiKey
        ])->get("{$this->apiBase}/api/health");

        return $response->json();
    }

    public function uploadTemplate($file)
    {
        $response = Http::attach('file', file_get_contents($file), $file->getClientOriginalName())
            ->withHeaders(['X-API-Key' => $this->apiKey])
            ->post("{$this->apiBase}/api/costos/upload");

        return $response->json();
    }
}
```

## Manejo de errores

### Respuestas de error

| Código | Significado |
|--------|-------------|
| 200 | Éxito |
| 400 | Datos inválidos |
| 401 | API Key fálida o ausente |
| 404 | Endpoint no encontrado |
| 422 | Error de validación |
| 500 | Error interno del servidor |

### Ejemplo de manejo de errores

```javascript
try {
  const response = await fetch(`${API_BASE}/api/costos/upload`, {
    method: 'POST',
    headers: { 'X-API-Key': API_KEY },
    body: formData
  });

  if (!response.ok) {
    const error = await response.json();
    console.error('Error:', error.detail);
    return;
  }

  const data = await response.json();
  console.log('Éxito:', data);
} catch (error) {
  console.error('Error de red:', error);
}
```

## CORS Preflight

Los requests OPTIONS (preflight) se manejan automáticamente. No es necesario código adicional en el frontend.

## Variables de entorno del Frontend

### Astro

```env
# .env
PUBLIC_API_KEY=mi-api-key-secreta
PUBLIC_API_BASE=http://localhost:8000
```

```javascript
// uso
const API_KEY = import.meta.env.PUBLIC_API_KEY;
```

### Laravel

```env
# .env
API_KEY=mi-api-key-secreta
API_BASE=http://localhost:8000
```

```php
// uso
$apiKey = config('services.sap.api_key');
```
