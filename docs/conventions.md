# Convenciones

- Python usa `snake_case`; la documentación y docstrings están en español.
- Los endpoints se agrupan por router bajo `/api`.
- Las credenciales solo se reciben por configuración segura o por el campo
  multipart requerido; nunca se imprimen ni se versionan.
- Los tests deben mockear SAP y ejecutarse con `pytest tests/ -v`.
