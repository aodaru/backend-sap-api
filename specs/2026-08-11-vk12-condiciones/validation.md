# Validation - VK12 Condiciones (Fase 5)

## Pruebas Automatizadas

### Comando de ejecución
```bash
cd /home/agarcia/dev/Jurado/pythonSap/backendPy
python -m pytest tests/test_condiciones.py -v
```

### Todos los tests deben pasar
```bash
python -m pytest tests/ -v
```

### Tests requeridos (13 tests mínimo)

| # | Test | Endpoint | Escenario |
|---|------|----------|-----------|
| 1 | `test_template_download` | `GET /template` | Descarga exitosa |
| 2 | `test_template_requires_api_key` | `GET /template` | Sin API Key → 401 |
| 3 | `test_upload_valid_excel` | `POST /upload` | Excel válido → 200, valid=true |
| 4 | `test_upload_invalid_missing_columns` | `POST /upload` | Sin columnas → 200, valid=false |
| 5 | `test_upload_invalid_bad_types` | `POST /upload` | Tipos incorrectos → 200, valid=false |
| 6 | `test_upload_requires_api_key` | `POST /upload` | Sin API Key → 401 |
| 7 | `test_upload_invalid_extension` | `POST /upload` | Archivo .txt → 422 |
| 8 | `test_execute_valid_excel` | `POST /execute` | Excel válido → 202, job_id |
| 9 | `test_execute_invalid_excel` | `POST /execute` | Excel inválido → 400 |
| 10 | `test_execute_requires_api_key` | `POST /execute` | Sin API Key → 401 |
| 11 | `test_status_returns_job` | `GET /status/{id}` | Job existe → 200 |
| 12 | `test_status_job_not_found` | `GET /status/{id}` | Job no existe → 404 |
| 13 | `test_status_requires_api_key` | `GET /status/{id}` | Sin API Key → 401 |

---

## Validación Manual

### 1. Template Excel
- [ ] Descargar template desde `GET /api/condiciones/template`
- [ ] Verificar que tiene las 9 columnas correctas
- [ ] Abrir en Excel y verificar que es válido

### 2. Upload y Validación
- [ ] Subir Excel válido con flujo `mat_orgvent_candistr`
- [ ] Subir Excel válido con flujo `orgvent_candistr_gpoart`
- [ ] Subir Excel válido con flujo `orgvent_candistr_sec_ramo_mat`
- [ ] Subir Excel válido con flujo `orgven_candist_sec_gpoart`
- [ ] Subir Excel con columnas faltantes → errores claros
- [ ] Subir Excel con flujo inválido → error
- [ ] Subir Excel con MATERIAL con letras → error
- [ ] Subir Excel con GRUPO_ARTICULO con menos de 9 dígitos → error
- [ ] Subir archivo .txt → error 422

### 3. Ejecución
- [ ] Ejecutar con datos válidos → job creado
- [ ] Ejecutar con datos inválidos → error 400
- [ ] Verificar que credenciales SAP se reciben en el body
- [ ] Verificar que la ejecución mock retorna resultados

### 4. Estado de Job
- [ ] Consultar estado de job existente → 200 con datos
- [ ] Consultar estado de job inexistente → 404
- [ ] Verificar que el progreso se actualiza (0 → 10 → 100)

### 5. Autenticación
- [ ] Todos los endpoints requieren API Key
- [ ] Sin header X-API-Key → 401
- [ ] Con API Key inválida → 401

---

## Verificación de Swagger/ReDoc

1. Iniciar servidor: `uvicorn main:app --reload`
2. Abrir `http://localhost:8000/docs`
3. Verificar que aparecen los 4 endpoints de `/api/condiciones`
4. Verificar que los modelos de request/response se muestran correctamente
5. Probar endpoints directamente desde Swagger

---

## Definition of Done

- [ ] Todos los tests automatizados pasan (13/13)
- [ ] Template Excel se descarga y es válido
- [ ] Upload valida los 4 flujos correctamente
- [ ] Execute acepta credenciales SAP en el body
- [ ] Status retorna estado del job
- [ ] Swagger documenta todos los endpoints
- [ ] Sin errores de linting o tipos
- [ ] Código sigue convenciones del proyecto (docstrings español, snake_case)
- [ ] No se rompen tests existentes (ME12, health, auth)
