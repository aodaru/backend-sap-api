"""Guardas de sintaxis y arranque para la versión mínima soportada (Python 3.8)."""

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APPLICATION_PACKAGES = ("main", "config", "dependencies", "models", "routers", "services")


def _application_files():
    for package in APPLICATION_PACKAGES:
        path = ROOT / (package + ".py")
        if path.exists():
            yield path
        else:
            yield from (ROOT / package).glob("*.py")


def test_application_modules_import_without_python38_only_annotations():
    """El arranque no debe depender de PEP 604 ni de genéricos built-in."""
    for path in _application_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.BitOr):
                raise AssertionError("PEP 604 encontrado en %s" % path)
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                if node.value.id in {"list", "dict", "tuple", "set", "frozenset"}:
                    raise AssertionError("genérico built-in encontrado en %s" % path)

    for module_name in ("main", "routers.condiciones", "services.sap_adapters",
                        "services.sap_session", "services.sap_errors", "services.sap_executor"):
        importlib.import_module(module_name)
