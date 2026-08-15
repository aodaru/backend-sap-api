# Arquitectura

FastAPI expone routers bajo `/api`; los routers validan requests y delegan en
services. Los tests usan `TestClient` y mocks, por lo que no requieren SAP real.
La autenticación se realiza mediante `X-API-Key` y la ejecución usa la cola
existente para serializar trabajos SAP.
