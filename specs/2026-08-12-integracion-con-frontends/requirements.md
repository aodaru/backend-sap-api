# Requirements: Integración con Frontends (Fase 9)

## Alcance

### Incluido
- Configuración CORS para frontends Astro y Laravel
- Endpoints de compatibilidad si se necesitan
- Documentación de integración para ambos frontends
- Tests de integración con requests simulados
- Ejemplos de código para consumo de API

### No incluido
- Desarrollo de frontends (se hacen por separado)
- Autenticación OAuth (se mantiene API Key)
- WebSockets o comunicación en tiempo real
- Deploy de frontends

## Decisiones

| ID | Decisión | Racional | Alternativa descartada |
|----|----------|----------|------------------------|
| D1 | CORS configurable via .env | Flexibilidad por entorno | Hardcoded en código |
| D2 | Mantener API Key | Simplificación para uso interno | OAuth (complejidad innecesaria) |
| D3 | Sin endpoints nuevos | Los existentes ya son consumibles | Crear endpoints redundantes |
| D4 | Documentación en Markdown | Consistencia con proyecto | Swagger personalizado |

## Contexto
- **Backend**: FastAPI con CORS ya habilitado en tech-stack.md
- **Frontends**: Astro (estático) y Laravel (PHP)
- **Auth**: API Key via header `X-API-Key`
- **Endpoints existentes**: `/api/health`, `/api/costos/*`, `/api/condiciones/*`

## Dependencias
- **Fase 2**: Sistema de autenticación por API Key
- **Fase 4**: Endpoints ME12 (costos)
- **Fase 5**: Endpoints VK12 (condiciones)
- **Fase 7**: Sistema de logging

## Riesgos identificados

| Riesgo | Mitigación |
|--------|------------|
| CORS mal configurado bloquea frontends | Tests de CORS con diferentes orígenes |
| Preflight requests fallan | Configurar OPTIONS correctamente |
| Credentials no funcionan | Verificar config de credenciales |
