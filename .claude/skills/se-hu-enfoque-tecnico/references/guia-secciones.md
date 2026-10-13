# Guía de secciones del enfoque técnico

## Búsqueda en el corpus

HU, alcance, actores, canal, embebido, portal, app, CRM, ERP, SaaS, API, fichero, batch, evento, cola, fuente, dato maestro, histórico, reglas, configuración, trazabilidad, auditoría, permisos, roles, IdP, OIDC, OAuth2, OBO, RBAC, gateway, APIM, MCP, A2A, REST, agente, orquestador, tool, runtime, sesión, snapshot, idempotencia, DEV/PRE/PRO, VNet, private endpoint, DNS, observabilidad, evaluación, prompts, contratos, Python, .NET, Azure, AWS, GCP, on-premise, Kubernetes, contenedores.

## Secciones

| § | Contenido mínimo | Formato |
| --- | --- | --- |
| 1 Contexto | Necesidad, intención arquitectónica, canal (o `A confirmar`), actores, fases funcionales, sistemas con los que convive | Prosa + citas |
| 2 Objetivo técnico | 1–2 párrafos + tabla `Resultado funcional / Cobertura técnica requerida / Evidencia / estado` | Tabla |
| 3 Resumen técnico | 6–10 líneas: canal, patrón de ejecución, gobierno, familias de fuentes, resultado, modelo de escritura, trazabilidad | Prosa |
| 4 Arquitectura objetivo basada en evidencia | 8–12 puntos numerados, cada uno con estado | Lista |
| 5 Flujo técnico de referencia | 8–12 pasos end-to-end agnósticos de canal | Lista |
| 6 Componentes y madurez | `Componente / Responsabilidad / Estado / Dependencia pendiente` | Tabla |
| 7 Alcance técnico | 10–18 puntos | Lista |
| 8 Dominios de datos | `Dominio / Fuentes / Uso / Tipo de dato / Observaciones` (tipo: transaccional, batch, evento, configuración, conversacional, auditoría, documental, analítico, externo SaaS) | Tabla |
| 9 Contratos/decisiones pendientes | `Decisión / Impacto / Responsable sugerido / Urgencia` | Tabla |
| 10 No funcionales | `Categoría / Requisito / Evidencia` (seguridad, privacidad, trazabilidad, control humano, idempotencia, frescura, robustez, rendimiento, escalabilidad, observabilidad, red, evaluación IA, cumplimiento) | Tabla |
| 11 Opciones comparadas | Sin catálogo fijo: una subsección 11.N por cada decisión técnica abierta y relevante del proyecto (de §9, de las propuestas pendientes del registro y de las desviaciones de preferencias), entre 2 y 8, por impacto. Ejemplos según el caso: Python vs .NET, batch vs streaming, monolito modular vs servicios, síncrono vs eventos, identidad delegada vs técnica, capa normalizada vs consulta directa a fuente, almacén gestionado vs propio. Las de IA van en §29.6. Cada opción elegida cita su `D-NNN` | `Opción / Ventajas / Riesgos / Recomendación-condición / Decisión` |
| 12 Diagrama preferido | Mermaid ejecutivo con clases evidenciado/crítica/preferente/alternativa | Mermaid |
| 13 Principios | `Principio / Aplicación / Estado` | Tabla |
| 14 Componentes | `Componente / Rol técnico / Estado` | Tabla |
| 15 Arquitectura objetivo | Mermaid detallado: entrada, identidad, gobierno, runtime, dominio, tools, fuentes, estado, reglas, externos, observabilidad | Mermaid |
| 16 Flujos detallados | 16.1 inicio; 16.2 ámbito; 16.3 criterios; 16.4 consolidación; 16.5 decisión/resultado; 16.6 escritura confirmada; 16.7 actualización posterior; 16.8 rechazo/feedback; 16.9 modificación; 16.10 validación especializada; 16.11 degradación; 16.12 auditoría y cierre; 16.13 batch/asíncrono. Omitir los que no apliquen indicando `No aplica` | Mermaid + `Paso / Componente / Acción técnica / Red, seguridad y autenticación / Recurso` |
| 17 Trazabilidad | `Flujo o regla funcional / Flujo técnico` | Tabla |
| 18 Integraciones | `Integración / Patrón / Uso / Consideración clave / Estado` | Tabla |
| 19 Seguridad e identidad | `Control / Requisito / Estado` (autenticación, federación, autorización, delegación, identidad de carga, secretos, minimización, confirmación de escritura, auditoría, protección de prompts, aislamiento de memoria, DLP) | Tabla |
| 20 Infraestructura y red | `Elemento / Requisito / Estado` | Tabla |
| 21 Recursos por entorno | 21.1 perfil de entornos; 21.2 recursos base | Tablas |
| 22 Datos y contratos | 22.1 contratos; 22.2 campos de respuesta; 22.3 errores normalizados; 22.4 matriz de fuentes y disponibilidad (enlaza `SRC-NN`); 22.5 persistencia de datos: una fila por almacén propio de la solución (tipo, tecnología con su `D-NNN`, propietario, volumen, consistencia, retención y borrado, backup/RPO/RTO, cifrado y residencia) y políticas (datos personales, cachés, migraciones, aislamiento, auditoría). No repite las fuentes de 22.4; el diseño de entidades va en `APP-Diseno` §5 | Tablas |
| 23 Desarrollo, interfaces y evaluación | 23.1 modalidad; 23.2 interfaces de agente (`No aplica` si no hay agentes); 23.3 repositorios; 23.4 prompting, evaluación y calidad (con IA, resumen que remite a §29.7 y §29.9; sin IA, `No aplica`) | Tablas |
| 24 Observabilidad | `Señal / Uso operativo / Estado` | Tabla |
| 25 DevOps y gobierno | Versionado, pipelines, identidad de despliegue, entornos, gates, contract tests, evaluación IA, rollback | Lista o tabla |
| 26 Criterios técnicos | `CAT-NN` Dado/Cuando/Entonces | Tabla |
| 27 Dependencias | Todas las `A confirmar` bloqueantes | Lista |
| 28 Riesgos | `Riesgo / Impacto / Mitigación` | Tabla |
| 29 IA y ciencia de datos | La redacta `se-arquitecto-ia-datos` (skill `se-enfoque-ia-datos`): 29.1–29.12. El resto del documento la integra y remite a ella; `No aplica: <motivo>` si no hay componente analítico ni de IA |

## Errores normalizados de referencia (adaptar)

`AUTH_REQUIRED`, `FORBIDDEN_SCOPE`, `TARGET_NOT_ALLOWED`, `VALIDATION_ERROR`, `SOURCE_UNAVAILABLE`, `SOURCE_STALE`, `THROTTLED`, `CONFLICT_STALE_SNAPSHOT`, `DUPLICATE_REQUEST`, `CONFIRMATION_REQUIRED`, `LOW_CONFIDENCE`, `INTERNAL_ERROR`.
