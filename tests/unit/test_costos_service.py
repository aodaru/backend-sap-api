"""
Tests unitarios para services/costos_service.py.

Verifica la lógica de negocio de costos (ME12):
- JobManager (create, update, get)
- get_template_path
- Constantes de validación

Nota: Tests de validate_excel y execute_me12 están en tests/test_costos.py
como tests de integración (usan FastAPI TestClient).
"""

import pytest

from models.responses import JobStatus
from services.costos_service import JobManager, REQUIRED_COLUMNS, get_template_path


# ============================================================
# Tests para JobManager
# ============================================================


class TestJobManager:
    """Tests para la clase JobManager."""

    @pytest.fixture
    def manager(self):
        """Fixture que retorna un JobManager limpio."""
        return JobManager()

    def test_create_job_returns_uuid(self, manager):
        """Test: create_job retorna un string UUID."""
        job_id = manager.create_job()
        assert isinstance(job_id, str)
        assert len(job_id) > 0

    def test_create_job_unique_ids(self, manager):
        """Test: create_job genera IDs únicos."""
        id1 = manager.create_job()
        id2 = manager.create_job()
        assert id1 != id2

    def test_create_job_initial_status(self, manager):
        """Test: Job creado tiene estado PENDING y progress 0."""
        job_id = manager.create_job()
        job = manager.get_job(job_id)
        assert job is not None
        assert job["status"] == JobStatus.PENDING
        assert job["progress"] == 0
        assert job["results"] is None
        assert "created_at" in job

    def test_get_job_existing(self, manager):
        """Test: get_job retorna el job si existe."""
        job_id = manager.create_job()
        job = manager.get_job(job_id)
        assert job is not None
        assert job["job_id"] == job_id

    def test_get_job_nonexistent(self, manager):
        """Test: get_job retorna None si el job no existe."""
        job = manager.get_job("nonexistent-id")
        assert job is None

    def test_update_job_status(self, manager):
        """Test: update_job actualiza el estado."""
        job_id = manager.create_job()
        manager.update_job(job_id, JobStatus.PROCESSING, progress=50)
        job = manager.get_job(job_id)
        assert job["status"] == JobStatus.PROCESSING
        assert job["progress"] == 50

    def test_update_job_results(self, manager):
        """Test: update_job actualiza los resultados."""
        job_id = manager.create_job()
        results = {"processed": 10, "successful": 8, "failed": 2}
        manager.update_job(job_id, JobStatus.COMPLETED, progress=100, results=results)
        job = manager.get_job(job_id)
        assert job["results"] == results

    def test_update_job_nonexistent_raises(self, manager):
        """Test: update_job lanza KeyError si el job no existe."""
        with pytest.raises(KeyError):
            manager.update_job("nonexistent", JobStatus.COMPLETED)

    def test_update_job_results_none(self, manager):
        """Test: update_job con results=None no modifica results existentes."""
        job_id = manager.create_job()
        manager.update_job(
            job_id,
            JobStatus.COMPLETED,
            progress=100,
            results={"data": "test"},
        )
        # Update sin results
        manager.update_job(job_id, JobStatus.COMPLETED, progress=100)
        job = manager.get_job(job_id)
        assert job["results"] == {"data": "test"}


# ============================================================
# Tests para get_template_path
# ============================================================


class TestGetTemplatePath:
    """Tests para get_template_path."""

    def test_returns_path_object(self):
        """Test: get_template_path retorna un objeto Path."""
        from pathlib import Path

        path = get_template_path()
        assert isinstance(path, Path)

    def test_ends_with_template_name(self):
        """Test: La ruta termina con el nombre correcto del template."""
        path = get_template_path()
        assert path.name == "costos_template.xlsx"

    def test_is_relative_to_project(self):
        """Test: La ruta es relativa al directorio del proyecto."""
        path = get_template_path()
        # Debería estar en templates/ relativo al proyecto
        assert "templates" in str(path)


# ============================================================
# Tests para constantes REQUIRED_COLUMNS
# ============================================================


class TestRequiredColumns:
    """Tests para la constante REQUIRED_COLUMNS."""

    def test_has_all_expected_columns(self):
        """Test: REQUIRED_COLUMNS contiene todas las columnas esperadas."""
        expected = [
            "Material",
            "Proveedor",
            "Org_Compras",
            "Tipo_Info",
            "Tipo_Condicion",
            "Nuevo_Precio",
            "Moneda",
            "Unidad_Precio",
            "Unidad_Medida",
            "Valido_Desde",
            "Valido_Hasta",
        ]
        assert REQUIRED_COLUMNS == expected

    def test_is_list(self):
        """Test: REQUIRED_COLUMNS es una lista."""
        assert isinstance(REQUIRED_COLUMNS, list)

    def test_has_11_columns(self):
        """Test: REQUIRED_COLUMNS tiene 11 columnas."""
        assert len(REQUIRED_COLUMNS) == 11
