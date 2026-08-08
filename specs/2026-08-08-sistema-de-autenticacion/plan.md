# Plan - Sistema de Autenticación (Fase 2)

## Grupo 1: Configuración de Variables de Entorno

1.1. Actualizar `.env.example` con variable `API_KEY=your-api-key-here`
1.2. Actualizar `config.py` para leer `API_KEY` desde variables de entorno
1.3. Crear archivo `.env` con una key de ejemplo (para desarrollo)

---

## Grupo 2: Middleware de Autenticación

2.1. Crear `dependencies.py` con función `verify_api_key()`
2.2. Implementar validación del header `X-API-Key` contra la key configurada
2.3. Definir respuestas de error 401 para key ausente o inválida
2.4. Crear modelo de respuesta de error en `models/responses.py`

---

## Grupo 3: Integración con Endpoints

3.1. Aplicar dependencia `verify_api_key` a todos los endpoints existentes
3.2. Excluir endpoints de documentación (`/docs`, `/redoc`, `/openapi.json`)
3.3. Verificar que la app principal registra la dependencia correctamente

---

## Grupo 4: Tests

4.1. Crear `tests/test_auth.py` con tests de autenticación
4.2. Test: petición sin header retorna 401
4.3. Test: petición con key inválida retorna 401
4.4. Test: petición con key válida retorna 200 (o el status esperado)
4.5. Test: endpoints de docs son accesibles sin autenticación
4.6. Ejecutar suite completa y verificar que no hay regresiones
