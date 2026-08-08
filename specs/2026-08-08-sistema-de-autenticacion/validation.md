# Validation - Sistema de Autenticación (Fase 2)

## Tests Automatizados

### Comandos
```bash
# Ejecutar todos los tests
pytest

# Ejecutar solo tests de autenticación
pytest tests/test_auth.py -v

# Verificar cobertura
pytest --cov=. --cov-report=term-missing
```

### Assertions requeridos
- [ ] `pytest` pasa sin errores
- [ ] Tests de auth cubren: key ausente, key inválida, key válida
- [ ] Endpoints de docs accesibles sin key
- [ ] No hay regresiones en tests existentes

---

## Validación Manual

### Escenario 1: Sin API Key
1. Enviar petición a cualquier endpoint sin header `X-API-Key`
2. **Esperado**: Respuesta 401 con `{"detail": "API Key required"}`

### Escenario 2: API Key inválida
1. Enviar petición con header `X-API-Key: wrong-key`
2. **Esperado**: Respuesta 401 con `{"detail": "Invalid API Key"}`

### Escenario 3: API Key válida
1. Enviar petición con header `X-API-Key: <key-correcta>`
2. **Esperado**: Respuesta exitosa (200 o el código esperado del endpoint)

### Escenario 4: Documentación accesible
1. Navegar a `http://localhost:8000/docs`
2. **Esperado**: Swagger UI se carga sin requerir autenticación

---

## Tone Check

N/A - Esta feature no tiene copy visible para el usuario final.

---

## Definition of Done

- [ ] `dependencies.py` implementado con `verify_api_key()`
- [ ] Variable `API_KEY` configurada en `.env` y `.env.example`
- [ ] Todos los endpoints requieren API Key (excepto docs)
- [ ] Respuestas 401 correctas para key ausente e inválida
- [ ] Tests de autenticación escritos y pasando
- [ ] Suite completa de tests pasa sin regresiones
- [ ] Documentación Swagger accesible sin autenticación
