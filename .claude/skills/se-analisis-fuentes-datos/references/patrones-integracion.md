# Patrones de integración de datos (orientativo)

| Patrón | Cuándo encaja | Riesgos | Controles mínimos |
| --- | --- | --- | --- |
| API síncrona directa | Datos transaccionales actuales, bajo volumen por petición | Latencia, throttling, acoplamiento a disponibilidad | Timeouts, reintentos con backoff, circuit breaker, caché acotada |
| Batch por fichero | Fuentes analíticas o legadas, frecuencia diaria/semanal | Frescura, cambios de formato silenciosos | Contrato de fichero, validación de esquema, control de completitud, marca de frescura |
| Extracción de BD / réplica | Acceso a tablas con permiso del propietario | Carga sobre origen, acoplamiento al esquema físico | Vistas acordadas, ventanas de extracción, cuentas de solo lectura |
| CDC | Necesidad de casi tiempo real sobre BD | Complejidad operativa, gestión de esquemas | Registro de esquemas, idempotencia, reprocesado |
| Eventos / colas | Integración desacoplada, reacción a cambios | Orden, duplicados, contratos de evento | Esquema versionado, claves de idempotencia, DLQ |
| Capa normalizada de consumo (serving) | Varias fuentes heterogéneas, consumo por IA/apps | Coste de construcción, doble verdad | Propietario claro, frescura expuesta, contratos de lectura |
| Índice de búsqueda / vectorial | Documentos y texto para RAG o búsqueda | Desalineación con origen, permisos | Sincronización incremental, filtrado por permisos, trazabilidad a documento origen |

Arquitectura por capas habitual (orientativa, no impuesta): `raw` (tal cual llega) → `curated` (limpio, tipado, deduplicado) → `serving` (modelado para consumo). Usa la terminología del cliente si existe.
