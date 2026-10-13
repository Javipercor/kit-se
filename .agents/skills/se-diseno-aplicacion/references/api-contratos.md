# Contratos API

## Por operación

| Campo | Contenido |
| --- | --- |
| Operación | Nombre de dominio (`proposal.create`, `context.read`) |
| Método y ruta | `POST /v1/proposals` |
| Autorización | Rol/scope requerido y validación de objetivo (actor-target) |
| Request | Esquema con tipos y obligatoriedad |
| Response | Esquema; incluir `correlationId`, versión de reglas/modelo si aplica, frescura de datos |
| Errores | Códigos normalizados (ver técnico §22.3) con HTTP status |
| Idempotencia | Cabecera `Idempotency-Key` en escrituras; comportamiento ante repetición |
| Concurrencia | ETag / versión de snapshot para evitar escrituras obsoletas |
| Paginación / límites | Cursor, tamaño máximo, rate limit |
| Observabilidad | Trazas y métricas emitidas |

## Convenciones

- Versionado en ruta (`/v1`) o cabecera; cambios incompatibles = nueva versión.
- Errores con formato Problem Details (RFC 9457) o el estándar del cliente.
- Fechas ISO 8601 en UTC; dinero con divisa explícita.
- OpenAPI como fuente de verdad; generar clientes y contract tests desde ella.
