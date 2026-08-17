# Test Fix Report: credentials field for /api/costos/execute

**Date:** 2026-08-17
**Status:** DONE - 293 passed, 0 failed

## Problem

The endpoint `execute_costos` in `routers/costos.py` was updated to require a `credentials: str = Form(...)` field (matching the `/api/condiciones/execute` contract). This caused 11 test failures because those tests did not include the `credentials` field in their POST requests.

Additionally, `routers/costos.py` was missing `import json`, which caused a `NameError` at runtime when trying to parse credentials.

## Root Cause

Two issues:
1. **Missing import in router:** `routers/costos.py` used `json.loads()` and `json.JSONDecodeError` but did not import `json`.
2. **Missing form field in tests:** 11 test calls to `/api/costos/execute` lacked the required `credentials` form field.

## Files Modified

### 1. `routers/costos.py`
- Added `import json` to the imports (line 9).

### 2. `tests/test_costos.py`
- Added `import json` to imports.
- Added `data={"credentials": json.dumps(...)}` to 4 calls:
  - `test_execute_valid_excel`
  - `test_execute_invalid_excel`
  - `test_execute_requires_api_key`
  - `test_status_returns_job`

### 3. `tests/test_queue.py`
- Added `import json` to imports.
- Added `data={"credentials": json.dumps(...)}` to 4 calls:
  - `test_execute_costos_creates_job`
  - `test_queue_status_after_execute`
  - `test_queue_stats_after_execute`
  - `test_execute_costos_returns_429_when_queue_full`

### 4. `tests/unit/test_sap_integration.py`
- Added `data={"credentials": json.dumps(...)}` to 3 calls (already had `import json`):
  - `test_http_disabled_integration_returns_503_failed_job_without_success_audit`
  - `test_http_costos_execute_audits_safe_code_and_failed_job`
  - `test_http_end_to_end_router_queue_worker_executor_adapter_with_fake_provider`

### 5. `tests/test_logging.py`
- Added `data={"credentials": json.dumps(...)}` to 1 call (already had `import json`):
  - `TestExecutionGeneratesLog::test_execute_generates_log`

### 6. `tests/integration/test_endpoints.py`
- Added `data={"credentials": json.dumps(...)}` to 1 call (already had `import json`):
  - `TestCostosEdgeCases::test_execute_requires_file`

## Credentials Payload Used

All tests use the same synthetic credentials:
```json
{"system": "PRD", "mandt": "300", "username": "test_user", "password": "test_pass", "language": "ES"}
```

## Verification

```
pytest -q
============================== 293 passed, 312 warnings in 3.97s ==============================
```
