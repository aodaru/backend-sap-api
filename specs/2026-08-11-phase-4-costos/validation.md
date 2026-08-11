# Validation: Phase 4 - Endpoints ME12 (Costos)

## Automated Tests

### Command
```bash
pytest tests/ -v
```

### Required Test Cases

#### Template Download
- `test_costos_template_download_success` - GET retorna archivo Excel
- `test_costos_template_download_content_type` - Content-Type es application/vnd.openxmlformats-officedocument.spreadsheetml.sheet

#### Upload Validation
- `test_costos_upload_valid_excel` - Upload exitoso con archivo válido
- `test_costos_upload_missing_columns` - Error cuando faltan columnas requeridas
- `test_costos_upload_invalid_types` - Error con tipos de datos incorrectos
- `test_costos_upload_empty_file` - Error con archivo vacío
- `test_costos_upload_invalid_format` - Error con formato no Excel

#### Execute
- `test_costos_execute_creates_job` - Execute retorna job_id y status pending
- `test_costos_execute_invalid_file` - Execute rechaza archivo inválido
- `test_costos_execute_sap_called` - Execute invoca lógica SAP (mock)

#### Status
- `test_costos_status_returns_state` - Status retorna estado del job
- `test_costos_status_not_found` - Status retorna 404 para job inexistente
- `test_costos_status_completed` - Status retorna completed con resultados

## Manual Validation

### Template Download
1. Abrir Swagger UI (`/docs`)
2. Ejecutar `GET /api/costos/template`
3. Verificar que se descarga `template_me12.xlsx`
4. Abrir Excel y verificar que tiene 11 columnas correctas

### Upload
1. Subir template válido → debe retornar 200 con resumen
2. Subir Excel con columnas faltantes → debe retornar 400
3. Subir CSV → debe retornar 422

### Execute
1. Subir archivo válido
2. Ejecutar `POST /api/costos/execute`
3. Verificar que retorna `job_id` y `status: pending`

### Status
1. Ejecutar execute para obtener `job_id`
2. Consultar `GET /api/costos/status/{job_id}`
3. Verificar que retorna estado válido

## Edge Cases

- **Concurrency**: Intentar execute mientras otro está en proceso → debe encolar
- **Large file**: Subir archivo con 1000+ filas → debe procesar sin error
- **Special characters**: Material con caracteres especiales → debe validar

## Definition of Done

- [x] Todos los tests automatizados pasan (25 tests)
- [x] Manual validation completa sin errores
- [x] Swagger UI muestra endpoints correctamente
- [x] Sin errores en logs del servidor
- [ ] Code review completado
