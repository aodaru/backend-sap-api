# Fase 9 — Correcciones de integración

## Cambios

- `docs/INTEGRATION.md` documenta el contrato real de `POST /api/costos/upload`:
  `filename`, `row_count`, `valid` y `validations`; ya no atribuye `job_id` a
  esa respuesta.
- El ejemplo `fetch` de `POST /api/costos/execute` usa `FormData` con el campo
  `file`, como requiere `routers/costos.py`, y toma el `job_id` de la respuesta
  de ejecución.
- La consulta de estado usa ese `executeData.job_id` y describe el estado real
  devuelto por `GET /api/costos/status/{job_id}`.
- La guía conserva únicamente los orígenes CORS documentados por defecto:
  `http://localhost:4321` y `http://localhost:8080`. No se añade soporte para
  `localhost:3000` ni se modifica `tests/test_cors.py`.

## Validación

```text
pytest tests/ -v
```

Resultado: `248 passed`, `195 warnings` en `0.83s`.
