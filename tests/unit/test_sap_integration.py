"""Pruebas deterministas de la frontera SAP; nunca conectan con SAP real."""

import asyncio
import io
import json

import pytest

from services.sap_adapters import Me12Adapter, Vk12Adapter, select_adapter
from services.sap_errors import SapBusinessError, SapScriptingUnavailableError
from services.sap_executor import SapTransactionExecutor
from services.sap_session import Win32ComSapSessionProvider
from services.sap_session import NullSapSessionProvider
from fastapi.testclient import TestClient
from main import app
from tests.frontend_client import download_template


class FakeSession:
    def __init__(self):
        self.calls = []

    def execute_transaction(self, transaction, row):
        self.calls.append((transaction, row))


class FakeProvider:
    def __init__(self):
        self.session = FakeSession()
        self.active = 0
        self.max_active = 0

    def acquire(self, credentials=None):
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        return self.session

    def release(self, session):
        self.active -= 1


def test_adapters_are_explicit_and_map_their_own_fields():
    assert isinstance(select_adapter("ME12"), Me12Adapter)
    assert isinstance(select_adapter("VK12"), Vk12Adapter)
    with pytest.raises(ValueError):
        select_adapter("VA01")
    result = asyncio.run(Me12Adapter().execute(FakeSession(), [{"Org_Compras": "1000", "Material": "1"}]))
    assert result.successful == 1
    assert result.rows[0].data["EKORG"] == "1000"


def test_me12_rejects_wrong_purchasing_org_without_navigation():
    with pytest.raises(SapBusinessError):
        Me12Adapter().map_row({"Org_Compras": "2000"})


def test_adapters_navigate_fields_interpret_messages_and_return_row_failures():
    class ScriptSession:
        def __init__(self):
            self.calls = []
        def start_transaction(self, transaction):
            self.calls.append(("start", transaction))
        def set_fields(self, fields):
            self.calls.append(("fields", fields))
        def submit(self):
            self.calls.append(("submit",))
        def save(self):
            self.calls.append(("save",))
        def get_messages(self):
            return [{"type": "E", "text": "mensaje de negocio"}]

    session = ScriptSession()
    result = asyncio.run(Vk12Adapter().execute(session, [{"MATERIAL": "1"}]))
    assert result.failed == 1
    assert result.rows[0].message == "SAP rechazó los datos de la operación"
    assert session.calls[0] == ("start", "VK12")

    me_session = ScriptSession()
    me_session.get_messages = lambda: []
    me_result = asyncio.run(Me12Adapter().execute(me_session, [{"Org_Compras": "1000"}]))
    assert me_result.successful == 1
    assert me_session.calls[0] == ("start", "ME12")


def test_navigation_error_is_not_retryable_for_either_transaction():
    from services.sap_adapters import Me12SapPort, Vk12SapPort
    from services.sap_errors import SapNavigationError
    class Broken:
        def start_transaction(self, name):
            raise RuntimeError(name)
    for adapter in (Me12Adapter(port=Me12SapPort()), Vk12Adapter(port=Vk12SapPort())):
        with pytest.raises(SapNavigationError):
            asyncio.run(adapter.execute(Broken(), [{"Org_Compras": "1000"}])) if adapter.transaction == "ME12" else asyncio.run(adapter.execute(Broken(), [{}]))
    assert SapNavigationError.retryable is False


@pytest.mark.asyncio
@pytest.mark.parametrize("transaction", ["ME12", "VK12"])
async def test_connection_and_authentication_failure_matrix_has_strict_retries(monkeypatch, transaction):
    from services.sap_errors import SapAuthenticationError, SapConnectionError
    class Provider:
        def __init__(self, error):
            self.error = error
            self.calls = 0
        def acquire(self, credentials=None):
            self.calls += 1
            raise self.error
        def release(self, session):
            raise AssertionError("no session to release")

    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "max_retries": 1, "sap_execution_timeout": 1, "sap_retry_backoff": 0,
        "sap_integration_enabled": True,
    })())
    for error, expected_calls in ((SapConnectionError(), 2), (SapAuthenticationError(), 1)):
        provider = Provider(error)
        with pytest.raises(type(error)):
            await SapTransactionExecutor(provider).execute(transaction, [], {"mandt": "300"})
        assert provider.calls == expected_calls


@pytest.mark.asyncio
async def test_executor_serializes_both_transactions_and_releases_session(monkeypatch):
    provider = FakeProvider()
    executor = SapTransactionExecutor(provider)
    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "max_retries": 0, "sap_execution_timeout": 2, "sap_retry_backoff": 1,
        "sap_integration_enabled": True,
    })())

    async def run(transaction):
        rows = [{"Org_Compras": "1000"}] if transaction == "ME12" else []
        credentials = {"mandt": "300"} if transaction == "VK12" else None
        return await executor.execute(transaction, rows, credentials)

    await asyncio.gather(run("ME12"), run("VK12"))
    assert provider.max_active == 1
    assert provider.active == 0


def test_win32com_is_optional_and_never_imported_at_module_import():
    with pytest.raises(SapScriptingUnavailableError):
        Win32ComSapSessionProvider().acquire()


@pytest.mark.asyncio
async def test_disabled_integration_never_returns_success_or_navigates(monkeypatch):
    """Regresión del 200 sin acción: el proveedor nulo debe fallar explícitamente."""
    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "max_retries": 0, "sap_execution_timeout": 1, "sap_retry_backoff": 0,
        "sap_integration_enabled": False,
    })())
    with pytest.raises(Exception) as error:
        await SapTransactionExecutor(NullSapSessionProvider()).execute("ME12", [{"Org_Compras": "1000"}])
    assert getattr(error.value, "code", "") == "integration_disabled"


@pytest.mark.sap_integration_disabled
def test_http_disabled_integration_returns_503_failed_job_without_success_audit(
    valid_excel_file, monkeypatch
):
    """El contrato HTTP conserva el fallo desde router hasta el job y la auditoría."""
    from services.costos_service import job_manager
    from services.logging_service import audit_logger

    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "sap_integration_enabled": False,
        "max_retries": 0,
        "sap_execution_timeout": 1,
        "sap_retry_backoff": 0,
    })())
    before = set(job_manager._jobs)
    response = TestClient(app).post(
        "/api/costos/execute",
        headers={"X-API-Key": "mi-api-key-secreta"},
        files={"file": ("disabled.xlsx", valid_excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "La integración real con SAP GUI no está habilitada"
    job_id = (set(job_manager._jobs) - before).pop()
    status = TestClient(app).get(
        f"/api/costos/status/{job_id}",
        headers={"X-API-Key": "mi-api-key-secreta"},
    )
    assert status.status_code == 200
    assert status.json()["status"] == "failed"
    entries = audit_logger.get_logs_by_job_id(job_id)
    assert entries
    assert all(entry.status != "success" for entry in entries)


def test_http_end_to_end_router_queue_worker_executor_adapter_with_fake_provider(
    valid_excel_file, monkeypatch
):
    """Prueba el recorrido completo sin conectar con SAP real."""
    from services.sap_executor import SapTransactionExecutor

    class RecordingSession:
        def __init__(self):
            self.calls = []

        def execute_transaction(self, transaction, row):
            self.calls.append((transaction, row))

    class RecordingProvider:
        def __init__(self):
            self.session = RecordingSession()

        def acquire(self, credentials=None):
            return self.session

        def release(self, session):
            pass

    provider = RecordingProvider()
    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "sap_integration_enabled": True,
        "max_retries": 0,
        "sap_execution_timeout": 1,
        "sap_retry_backoff": 0,
    })())
    monkeypatch.setattr("services.sap_executor.sap_executor", SapTransactionExecutor(provider))

    response = TestClient(app).post(
        "/api/costos/execute",
        headers={"X-API-Key": "mi-api-key-secreta"},
        files={"file": ("e2e.xlsx", valid_excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 202
    assert response.json()["status"] == "completed"
    assert provider.session.calls[0][0] == "ME12"
    assert provider.session.calls[0][1]["EKORG"] == "1000"


@pytest.mark.parametrize(
    ("path", "filename"),
    [("/api/costos/template", "costos_template.xlsx"), ("/api/condiciones/template", "condiciones_template.xlsx")],
)
def test_template_contract_is_binary_exact_and_readable(path, filename):
    response = TestClient(app).get(path, headers={"X-API-Key": "mi-api-key-secreta"})
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert response.headers["content-disposition"] == f"attachment; filename={filename}"
    assert not response.headers.get("content-type", "").startswith("application/json")
    import openpyxl
    assert openpyxl.load_workbook(io.BytesIO(response.content), read_only=True).active is not None


@pytest.mark.parametrize(
    ("path", "filename"),
    [("/api/costos/template", "costos_template.xlsx"), ("/api/condiciones/template", "condiciones_template.xlsx")],
)
def test_frontend_simulated_client_downloads_blob_without_json(path, filename):
    blob = download_template(TestClient(app), path, "mi-api-key-secreta")
    assert blob.filename == filename
    assert blob.content_type == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert blob.blob[:2] == b"PK"


@pytest.mark.parametrize("path", ["/api/costos/template", "/api/condiciones/template"])
def test_template_contract_rejects_missing_and_invalid_keys(path):
    client = TestClient(app)
    assert client.get(path).status_code == 401
    assert client.get(path, headers={"X-API-Key": "invalid"}).status_code == 401


@pytest.mark.parametrize("module_name", ["routers.costos", "routers.condiciones"])
def test_template_read_failure_is_safe(monkeypatch, module_name):
    import importlib
    module = importlib.import_module(module_name)

    class ExistingPath:
        def exists(self):
            return True

    monkeypatch.setattr(module, "get_template_path", lambda: ExistingPath())
    monkeypatch.setattr("builtins.open", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("/private/secret")))
    response = TestClient(app).get(
        "/api/costos/template" if module_name.endswith("costos") else "/api/condiciones/template",
        headers={"X-API-Key": "mi-api-key-secreta"},
    )
    assert response.status_code == 500
    assert "/private/secret" not in response.text
    assert "costos_template" not in response.text if module_name.endswith("costos") else True


@pytest.mark.asyncio
async def test_retry_backoff_timeout_and_release(monkeypatch):
    class Provider:
        def __init__(self):
            self.acquired = 0
            self.released = 0
            self.attempts = 0
        def acquire(self, credentials=None):
            self.acquired += 1
            self.attempts += 1
            if self.attempts == 1:
                from services.sap_errors import SapConnectionError
                raise SapConnectionError()
            return FakeSession()
        def release(self, session):
            self.released += 1

    provider = Provider()
    executor = SapTransactionExecutor(provider)
    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "max_retries": 1, "sap_execution_timeout": 1, "sap_retry_backoff": 3,
        "sap_integration_enabled": True,
    })())
    sleeps = []
    async def fake_sleep(seconds):
        sleeps.append(seconds)
    monkeypatch.setattr("services.sap_executor.asyncio.sleep", fake_sleep)
    result = await executor.execute("ME12", [{"Org_Compras": "1000"}])
    assert result.successful == 1
    assert provider.acquired == 2
    assert provider.released == 1
    assert sleeps == [1]


@pytest.mark.asyncio
async def test_execution_timeout_releases_and_business_error_is_not_retried(monkeypatch):
    from services.sap_errors import SapBusinessError, SapExecutionTimeoutError

    class Provider:
        def __init__(self):
            self.released = 0
        def acquire(self, credentials=None):
            return FakeSession()
        def release(self, session):
            self.released += 1

    provider = Provider()
    executor = SapTransactionExecutor(provider)
    monkeypatch.setattr("services.sap_executor.get_settings", lambda: type("S", (), {
        "max_retries": 1, "sap_execution_timeout": 0.01, "sap_retry_backoff": 1,
        "sap_integration_enabled": True,
    })())
    class SlowAdapter:
        async def execute(self, session, rows):
            await asyncio.sleep(1)
    monkeypatch.setattr("services.sap_executor.select_adapter", lambda transaction: SlowAdapter())
    with pytest.raises(SapExecutionTimeoutError):
        await executor.execute("ME12", [])
    assert provider.released == 2

    calls = []
    class BusinessAdapter:
        async def execute(self, session, rows):
            calls.append(1)
            raise SapBusinessError("sensitive SAP text")
    monkeypatch.setattr("services.sap_executor.select_adapter", lambda transaction: BusinessAdapter())
    with pytest.raises(SapBusinessError):
        await executor.execute("VK12", [], {"mandt": "300"})
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_queue_worker_fifo_wait_timeout_and_terminal_state():
    from services.queue_service import RequestQueue
    from services.sap_errors import QueueWaitTimeoutError
    queue = RequestQueue(max_size=3)
    queue._execution_timeout = 1
    queue._get_queue_wait_timeout = lambda: 0
    gate = asyncio.Event()

    async def first():
        await gate.wait()
        return {"ok": True}

    first_task = asyncio.create_task(queue.run_job("first", "ME12", first))
    await asyncio.sleep(0)
    second_task = asyncio.create_task(queue.run_job("second", "VK12", lambda: asyncio.sleep(0)))
    await asyncio.sleep(0.1)
    gate.set()
    assert await first_task == {"ok": True}
    with pytest.raises(QueueWaitTimeoutError):
        await second_task
    status = await queue.get_status("second")
    assert status is not None and status.status.value == "timeout" and status.position == 0


@pytest.mark.asyncio
async def test_vk12_secret_is_absent_from_status_audit_and_exception(monkeypatch, tmp_path):
    """El payload efímero se limpia incluso cuando el adaptador falla."""
    from services import condiciones_service
    from services.costos_service import job_manager
    from services.logging_service import AuditLogger
    from services.sap_errors import SapAuthenticationError
    secret = "super-secret-password"
    payload = {"system": "ERQ", "mandt": "300", "username": "u", "password": secret, "language": "ES"}

    async def fail(*args, **kwargs):
        assert args[2].get("password") == secret
        raise SapAuthenticationError(secret)

    monkeypatch.setattr("services.sap_executor.sap_executor.execute", fail)
    job_id = job_manager.create_job()
    with pytest.raises(SapAuthenticationError):
        await condiciones_service.execute_vk12([], job_id, payload)
    assert payload == {}
    assert secret not in json.dumps(job_manager.get_job(job_id))

    audit = AuditLogger(str(tmp_path))
    audit.log_execution(job_id, "u", "VK12", "error", 0, False, 0, 0, 0,
                        errors=[{"message": secret}], metadata={"password": secret})
    raw = (tmp_path / f"audit-{__import__('datetime').datetime.now(__import__('datetime').timezone.utc):%Y-%m-%d}.json").read_text()
    assert secret not in raw
    payload.clear()
    assert secret not in json.dumps(payload)


def test_log_error_and_validation_messages_never_persist_exception_text(monkeypatch, tmp_path):
    from fastapi import UploadFile
    from services.condiciones_service import validate_excel as validate_vk12
    from services.costos_service import validate_excel as validate_me12
    from services.logging_service import AuditLogger
    secret = "validation-secret-password"
    logger = AuditLogger(str(tmp_path))
    logger.log_error("test", secret, RuntimeError(secret))
    raw = next(tmp_path.glob("audit-*.json")).read_text()
    assert secret not in raw

    import openpyxl
    monkeypatch.setattr(openpyxl, "load_workbook", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError(secret)))
    me12 = asyncio.run(validate_me12(UploadFile(filename="bad.xlsx", file=io.BytesIO(b"x"))))
    vk12 = asyncio.run(validate_vk12(UploadFile(filename="bad.xlsx", file=io.BytesIO(b"x"))))
    assert secret not in json.dumps([item.model_dump() for item in me12[1] + vk12[1]])


def test_vk12_multipart_rejected_credentials_are_never_returned(client, valid_api_key, valid_condiciones_excel, monkeypatch, tmp_path):
    from services.sap_errors import SapAuthenticationError
    secret = "multipart-rejected-secret"
    captured = {}

    async def reject(rows, job_id, credentials):
        captured["credentials"] = credentials
        raise SapAuthenticationError(secret)

    monkeypatch.setattr("routers.condiciones.execute_vk12", reject)
    response = client.post(
        "/api/condiciones/execute",
        headers={"X-API-Key": valid_api_key},
        data={"credentials": json.dumps({"system": "ERQ", "mandt": "300", "username": "u", "password": secret, "language": "ES"})},
        files={"file": ("conditions.xlsx", valid_condiciones_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 422
    assert secret not in response.text
    assert captured["credentials"] == {}
    job_id = next(iter(__import__("services.costos_service", fromlist=["job_manager"]).job_manager._jobs))
    status_response = client.get(f"/api/condiciones/status/{job_id}", headers={"X-API-Key": valid_api_key})
    assert secret not in status_response.text
    assert all(secret not in path.read_text(errors="ignore") for path in __import__("pathlib").Path("logs").glob("audit-*.json"))
    assert not any(secret in str(path) for path in tmp_path.iterdir())


@pytest.mark.asyncio
async def test_worker_recovers_after_failure_and_processes_next_job():
    from services.queue_service import RequestQueue
    from services.sap_errors import SapIntegrationError
    queue = RequestQueue(max_size=3)
    async def broken():
        raise RuntimeError("internal worker detail")
    first = asyncio.create_task(queue.run_job("broken", "ME12", broken))
    with pytest.raises(SapIntegrationError):
        await first
    second = await queue.run_job("recovered", "VK12", lambda: asyncio.sleep(0, result="ok"))
    assert second == "ok"
    assert (await queue.get_status("broken")).status.value == "failed"
    assert (await queue.get_status("recovered")).status.value == "completed"


@pytest.mark.asyncio
async def test_queue_cancel_missing_and_full_are_safe(monkeypatch):
    from services.queue_service import RequestQueue
    queue = RequestQueue(max_size=1)
    await queue.enqueue("queued", "ME12")
    assert await queue.cancel("queued") is True
    assert (await queue.get_status("queued")).status.value == "cancelled"
    with pytest.raises(KeyError):
        await queue.cancel("missing")
    await queue.enqueue("one", "ME12")
    with pytest.raises(ValueError, match="Cola llena"):
        await queue.enqueue("two", "VK12")


@pytest.mark.asyncio
async def test_process_with_retries_never_logs_or_raises_secret_details(caplog):
    from services.queue_service import RequestQueue
    queue = RequestQueue(max_size=2)
    secret = "retry-secret-password"
    await queue.enqueue("retry-secret", "ME12")

    async def transient():
        raise ConnectionError(secret)

    with pytest.raises(Exception) as error:
        await queue.process_with_retries("retry-secret", transient)
    assert secret not in str(error.value)
    assert secret not in caplog.text

    await queue.clear()
    await queue.enqueue("business-secret", "VK12")
    async def business():
        raise ValueError(secret)
    with pytest.raises(Exception) as error:
        await queue.process_with_retries("business-secret", business)
    assert secret not in str(error.value)
    assert secret not in caplog.text
