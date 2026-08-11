# Review — Refactorización del Logging Service (Direct File Writing)

**Fecha:** 2026-08-11
**Reviewer:** Agente Revisor (mimo-v2.5)
**Archivos revisados:** 3 (`services/logging_service.py`, `tests/test_logging.py`, `config.py`)

---

## Checklist Técnico

- [x] **NO `RotatingFileHandler` o `logging.handlers` references remain**
  - `grep` en `logging_service.py` y en todo el proyecto: 0 coincidencias. Import `logging` se usa solo para `addLevelName`.

- [x] **NO attribute hacking (`baseFilename`, `stream`, etc.)**
  - No hay acceso a atributos internos del handler. Toda la gestión de archivos es directa con `open()` y `Path`.

- [x] **`_write_log` usa simple `open()` in append mode**
  - Línea 117: `open(path, "a", encoding="utf-8")`. Sin buffering manual, sin handlers.

- [x] **`_rotate_if_needed()` handles both date change AND size-based segmentation**
  - Líneas 132-170: 3 casos claros: (1) no hay archivo abierto → buscar último segmento, (2) fecha cambió → nuevo archivo, (3) tamaño excedido → nuevo segmento.

- [x] **File naming: `audit-YYYY-MM-DD.json` and `audit-YYYY-MM-DD.N.json`**
  - `_build_file_path` (líneas 71-84): segment 0 → `audit-{date}.json`, segment > 0 → `audit-{date}.{N}.json`.

- [x] **Thread safety maintained with `threading.Lock`**
  - Línea 56: `self._lock = threading.Lock()`. `_write_log` (línea 179) y `cleanup_old_logs` (línea 356) usan `with self._lock`.

- [x] **Flush after every write**
  - Línea 184: `self._current_file.flush()` después de cada `write()`.

- [x] **`get_logs` and `get_logs_by_job_id` handle both file formats**
  - `_get_files_for_range` (líneas 444-491) parsea `audit-*.json` y extrae fecha de `YYYY-MM-DD` o `YYYY-MM-DD.N`.
  - `get_logs_by_job_id` (líneas 433-442) globs `audit-*.json` directamente.

- [x] **`cleanup_old_logs` handles segmented files**
  - Línea 366: `self._log_dir.glob("audit-*.json")` captura todos los segmentos.

- [x] **Global `audit_logger` reads from config**
  - Líneas 573-581: usa `get_settings()` para `log_dir`, `log_retention_days`, `log_max_file_size_mb`.

- [x] **All existing test signatures unchanged**
  - Los 20 tests originales mantienen mismas firmas, fixtures y asserts.

- [x] **New segmentation tests exist and are meaningful**
  - 4 tests nuevos en `TestSizeBasedSegmentation` (líneas 297-512):
    - `test_creates_new_segment_when_file_exceeds_max_size` (max_file_size_mb=0.001 → 1KB)
    - `test_daily_rotation_creates_new_date_file` (ayer vs hoy)
    - `test_reads_from_segmented_files` (get_logs y get_logs_by_job_id con archivos segmentados)
    - `test_cleanup_removes_segmented_files` (limpieza de segmentos antiguos)

---

## Tests

**24/24 PASSED** (20 originales + 4 nuevos)

```
tests/test_logging.py::TestLogExecution::test_log_execution_writes_json PASSED
tests/test_logging.py::TestLogExecution::test_log_execution_error_fields PASSED
tests/test_logging.py::TestLogAuth::test_log_auth_success PASSED
tests/test_logging.py::TestLogAuth::test_log_auth_failure PASSED
tests/test_logging.py::TestLogUpload::test_log_upload PASSED
tests/test_logging.py::TestSizeBasedSegmentation::test_creates_new_segment_when_file_exceeds_max_size PASSED
tests/test_logging.py::TestSizeBasedSegmentation::test_daily_rotation_creates_new_date_file PASSED
tests/test_logging.py::TestSizeBasedSegmentation::test_reads_from_segmented_files PASSED
tests/test_logging.py::TestSizeBasedSegmentation::test_cleanup_removes_segmented_files PASSED
tests/test_logging.py::TestCleanupOldLogs::test_cleanup_old_logs PASSED
tests/test_logging.py::TestCleanupOldLogs::test_cleanup_keeps_recent PASSED
tests/test_logging.py::TestGetLogs::test_get_logs_filters_by_transaction PASSED
tests/test_logging.py::TestGetLogs::test_get_logs_filters_by_user PASSED
tests/test_logging.py::TestGetLogs::test_get_logs_filters_by_date PASSED
tests/test_logging.py::TestGetLogs::test_get_logs_by_job_id PASSED
tests/test_logging.py::TestGetLogs::test_get_logs_by_job_id_not_found PASSED
tests/test_logging.py::TestLogsEndpoint::test_endpoint_get_logs_requires_auth PASSED
tests/test_logging.py::TestLogsEndpoint::test_endpoint_get_logs_returns_200 PASSED
tests/test_logging.py::TestLogsEndpoint::test_endpoint_get_logs_by_job_id PASSED
tests/test_logging.py::TestExecutionGeneratesLog::test_execute_generates_log PASSED
tests/test_logging.py::TestLogModels::test_error_detail_model PASSED
tests/test_logging.py::TestLogModels::test_audit_log_entry_model PASSED
tests/test_logging.py::TestLogModels::test_log_query_params_defaults PASSED
tests/test_logging.py::TestLogModels::test_log_response_model PASSED
```

---

## Observaciones (No bloqueantes)

1. **`_rotate_if_needed` — caso segment 0 lleno crea segment 1 sin verificar si ya existe completo** — Si el proceso se reinicia con segmentos 0 y 1 llenos, el primer write abre segment 1 (que ya está lleno). El siguiente write corrige a segment 2. Funcional pero con un write extra en el segmento lleno. **No bloqueante.**

2. **`_find_latest_segment` usa `break` al primer hueco** — Si hay segmentos 0, 1, 3 (hueco en 2), retorna 1. Correcto para escritura secuencial, pero si se eliminan archivos manualmente podría crear segmentos duplicados. **No bloqueante** (patrón estándar de rotación).

3. **`config.py:51` — `log_max_file_size_mb: int = 10`** — El tipo es `int` pero `AuditLogger.__init__` acepta `float`. Compatible (int es subtipo de float en Python), pero si alguien configura `log_max_file_size_mb=0.5` en `.env`, pydantic lo parseará como `0` (int). **No bloqueante** (10MB es un default razonable).

---

## Veredicto

# ✅ APPROVED

**Resumen:** La refactorización cumple con todos los criterios. El `RotatingFileHandler` fue completamente eliminado. La escritura directa con `open()` en append mode es simple y robusta. La rotación maneja correctamente fecha, tamaño, y segmentación. Los 4 tests nuevos validan los escenarios críticos. Los 24 tests pasan. Las 3 observaciones son menores y no bloqueantes.
