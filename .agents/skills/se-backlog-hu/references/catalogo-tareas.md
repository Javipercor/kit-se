# Catálogo orientativo de tareas y horquillas

Horquillas de referencia para un perfil senior con contexto del proyecto. Ajusta por nivel: N1 parte baja, N2 media, N3 alta, N4 alta + tarea de spike previa. Divide cualquier tarea que supere 16h. Calibra estas cifras con datos históricos del equipo cuando existan.

## Architect

| Tarea | Horquilla |
| --- | --- |
| Arquitectura objetivo y diagrama validado con cliente | 8–16h |
| ADR de decisión relevante (stack, persistencia, identidad) | 2–6h |
| Contratos de integración con sistema externo (por sistema) | 4–12h |
| Modelo de seguridad e identidad (roles, scopes, delegación) | 6–12h |
| Revisión de arquitectura de red y entornos | 4–8h |

## Backend (Python o .NET)

| Tarea | Horquilla |
| --- | --- |
| Esqueleto de servicio (estructura, config, health, logging, OpenAPI) | 6–12h |
| Endpoint de lectura con validación, autorización y tests | 4–8h |
| Endpoint de escritura con idempotencia, concurrencia y tests | 8–14h |
| Cliente de API externa con reintentos, circuit breaker y mocks | 6–12h |
| Modelo de persistencia + migraciones (por agregado) | 4–10h |
| Worker / job asíncrono con reintentos y DLQ | 8–14h |
| Tool de agente con contrato, scopes y tests | 6–12h |
| Adaptador de canal (payload, sesión, identidad del host) | 8–16h |

## Frontend / UI-UX

| Tarea | Horquilla |
| --- | --- |
| Diseño de flujo e interacciones de una HU (UI/UX) | 4–12h |
| Pantalla/vista con estados (carga, vacío, error, degradado) | 8–16h |
| Componente de confirmación de acción con impacto | 4–8h |
| Integración embebida en host (extensión, app, componente) | 8–16h |
| Pruebas E2E de flujo crítico | 4–8h |

## DataEng

| Tarea | Horquilla |
| --- | --- |
| Contrato de datos de una fuente + validación de esquema | 4–8h |
| Ingesta batch de fuente con control de completitud y frescura | 8–16h |
| Ingesta por API/CDC/eventos con idempotencia | 10–16h |
| Transformación/curado de un dominio con tests de calidad | 8–16h |
| Capa de consumo (vista/serving) para una HU | 6–12h |
| Índice documental/vectorial con sincronización y permisos | 10–16h |

## DS (ML y GenAI)

| Tarea | Horquilla |
| --- | --- |
| Análisis exploratorio y validación de hipótesis sobre muestra | 8–16h |
| Baseline (reglas o modelo simple) con evaluación | 6–12h |
| Feature engineering de un dominio con control de fuga | 8–16h |
| Entrenamiento y selección de modelo con validación temporal | 10–16h |
| Construcción de dataset de evaluación (por intención) con negocio | 8–16h |
| Diseño y versionado de prompts de una capacidad | 6–12h |
| Pipeline RAG (troceado, recuperación, citación) para un corpus | 12–16h |
| Guardrails (injection, PII, salida estructurada) | 6–12h |
| Suite de evaluación automatizada integrada en CI | 8–14h |
| Explicabilidad para el usuario (motivos, señales) | 6–12h |

## DevOps (solo EPIC DevOps)

| Tarea | Horquilla |
| --- | --- |
| Repositorios, ramas protegidas y plantillas de PR | 2–4h |
| Pipeline CI (build, lint, tests, escaneo de secretos) por servicio | 4–8h |
| Pipeline CD por entorno con aprobaciones | 6–12h |
| Infraestructura como código de un entorno (por bloque) | 8–16h |
| Identidad de carga de trabajo y gestor de secretos | 4–8h |
| Red privada, DNS y validación de conectividad por entorno | 8–16h |
| Observabilidad: trazas, dashboards y alertas | 8–14h |
| Despliegue de modelo/prompt con registro y rollback | 6–12h |
| Handover operativo y runbooks | 6–12h |

## QA

| Tarea | Horquilla |
| --- | --- |
| Plan de pruebas de una HU | 2–4h |
| Pruebas de contrato de una API | 3–6h |
| Pruebas de integración con sistema externo (mock + real) | 4–10h |
| Pruebas de rendimiento de un flujo | 6–12h |
| Pruebas de seguridad funcional (permisos, delegación) | 4–8h |

## Documentacion y Entregables

| Tarea | Horquilla |
| --- | --- |
| Documento de arquitectura final | 8–16h |
| Manual de usuario de una capacidad | 4–8h |
| Guía de operación y soporte | 6–12h |
| Informe de evaluación del modelo/IA | 6–12h |
