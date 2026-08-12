# Guía de Contribución

Instrucciones para contribuir al proyecto Backend API de Automatización SAP.

## Flujo de Trabajo

### 1. Branching Strategy

- `main` - Código estable, listo para producción
- `develop` - Código en desarrollo activo
- `feature/*` - Nuevas funcionalidades
- `bugfix/*` - Corrección de bugs
- `hotfix/*` - Correcciones urgentes en producción

### 2. Crear una Feature

```bash
git checkout develop
git pull origin develop
git checkout -b feature/nombre-funcionalidad
```

### 3. Desarrollo

#### Convenciones de Código

- **Python**: Seguir PEP 8 (snake_case para funciones/variables, PascalCase para clases)
- **Docstrings**: En español, formato Google
- **Type hints**: Siempre usar anotaciones de tipo
- **Imports**: Organizar en orden: stdlib, third-party, local

```python
"""
Descripción del módulo.

Más detalles sobre el módulo si es necesario.
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends

from models.responses import HealthResponse


def mi_funcion(param1: str, param2: int) -> bool:
    """
    Descripción de la función.

    Args:
        param1: Descripción del parámetro 1.
        param2: Descripción del parámetro 2.

    Returns:
        Descripción del valor retornado.

    Raises:
        ValueError: Descripción de cuándo se lanza.
    """
    pass
```

#### Tests

Escribir tests para toda funcionalidad nueva:

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests de un archivo específico
pytest tests/test_health.py -v

# Ejecutar con cobertura
pytest tests/ --cov=. --cov-report=term-missing

# Verificar umbral de cobertura (70%)
pytest tests/ --cov=. --cov-fail-under=70
```

**Estructura de tests:**
```
tests/
├── conftest.py          # Fixtures compartidos
├── test_*.py            # Tests de integración (endpoints)
├── unit/                # Tests unitarios (servicios, modelos)
│   └── test_*.py
└── integration/         # Tests de integración avanzada
    └── test_*.py
```

**Reglas para tests:**
- Todos los tests deben pasar sin SAP real (mock completo)
- Tests unitarios: rápidos, sin dependencias externas
- Tests de integración: usar FastAPI TestClient
- Fixtures en `conftest.py` para datos compartidos
- Nombre: `test_<que_se_prueba>` o `Test<Clase>`

#### Mocking SAP

Nunca tocar SAP real en tests. Usar mocks:

```python
from unittest.mock import AsyncMock, patch

# Mock de win32com (SAP GUI)
with patch("services.costos_service.win32com.client") as mock_sap:
    mock_sap.Dispatch.return_value = MagicMock()
    # Test aquí
```

### 4. Commits

Seguir convención de commits:

```
<tipo>(<scope>): <descripción corta>

[opcional: cuerpo del commit]

[opcional:-footer]
```

**Tipos:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Documentación
- `test`: Tests
- `refactor`: Refactorización
- `chore`: Tareas de mantenimiento

**Ejemplos:**
```
feat(costos): agregar validación de moneda en template
fix(queue): corregir race condition en dequeue
docs: actualizar guía de instalación
test(costos): agregar tests para execute_ME12
refactor(logging): extraer clase AuditLogger
```

### 5. Pull Request

1. Push al branch feature:
   ```bash
   git push origin feature/nombre-funcionalidad
   ```

2. Crear PR contra `develop`

3. Descripción del PR:
   - Qué se hizo
   - Por qué se hizo
   - Cómo probarlo
   - Screenshots (si aplica)

4. Esperar revisión y approval

5. Merge squash o merge commit

### 6. Después del Merge

```bash
git checkout develop
git pull origin develop
git branch -d feature/nombre-funcionalidad
git push origin --delete feature/nombre-funcionalidad
```

## Code Review Checklist

### Código
- [ ] Sigue convenciones del proyecto (snake_case, docstrings español)
- [ ] Type hints en todas las funciones públicas
- [ ] Docstrings completos (Args, Returns, Raises)
- [ ] No hay código duplicado
- [ ] Error handling adecuado

### Tests
- [ ] Tests unitarios para lógica nueva
- [ ] Tests de integración para endpoints nuevos
- [ ] Todos los tests pasan: `pytest tests/ -v`
- [ ] Cobertura >= 70%: `pytest tests/ --cov=. --cov-fail-under=70`
- [ ] No SAP real en tests (solo mocks)

### Documentación
- [ ] README actualizado (si aplica)
- [ ] Docstrings en español
- [ ] API docs actualizados (Swagger auto-generado)

### Seguridad
- [ ] No hay secrets en el código
- [ ] API Key requerida en endpoints protegidos
- [ ] Input sanitization
- [ ] No se exponen errores internos al cliente

## Herramientas de Desarrollo

### Linting (opcional)

```bash
# Instalar
pip install black isort flake8 mypy

# Formatear
black .
isort .

# Verificar
flake8 .
mypy .
```

### Git Hooks (opcional)

Usar `pre-commit` para ejecutar checks automáticos:

```bash
pip install pre-commit
pre-commit install
```

## Issues y Bugs

1. Buscar si el issue ya existe
2. Si no existe, crear uno con:
   - Título claro
   - Pasos para reproducir
   - Comportamiento esperado vs actual
   - Entorno (OS, Python version)
   - Screenshots (si aplica)

## Preguntas

Para dudas, abrir un issue con tag `question`.
