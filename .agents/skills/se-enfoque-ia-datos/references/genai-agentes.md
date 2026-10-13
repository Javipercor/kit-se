# GenAI, RAG y agentes

## Escalera de complejidad (sube solo si el escalón anterior no basta)

1. Prompting con contexto fijo y salida estructurada (JSON con esquema).
2. RAG: recuperación sobre documentos o datos con permisos, citación de fuentes.
3. Agente con tools: el modelo decide qué herramienta usar; las tools encapsulan acceso a datos y operaciones.
4. Workflow determinista con pasos LLM: orquestación en código y LLM solo en pasos acotados (preferible a agente libre cuando el proceso es conocido).
5. Multi-agente: solo si hay dominios separables con contratos claros (orquestador + especialistas).

## Diseño RAG

- Ingesta: troceado por estructura del documento, metadatos (origen, fecha, permisos), actualización incremental.
- Recuperación: híbrida (léxica + vectorial) como punto de partida, re-ranking si la precisión lo exige, filtrado por permisos del usuario antes de generar.
- Generación: respuesta con citas, abstención explícita cuando no hay soporte.

## Diseño de agentes y tools

- Separar razonamiento (LLM), autorización (gateway/backend), acceso a datos (tools), ejecución (backends) y auditoría.
- Tools con contrato: nombre, descripción, esquema de entrada/salida, errores normalizados, idempotencia en escrituras, scopes.
- Protocolos de exposición posibles (según plataforma, `A confirmar`): API REST interna, MCP para tools, protocolos agente-a-agente.
- Escrituras con confirmación humana, snapshot vigente y clave de idempotencia.
- Estado: hilo/conversación, snapshots de propuestas, decisiones; con TTL y retención definidos.

## Guardrails

- Entrada: detección de prompt injection (incluida la indirecta desde documentos y tools), PII, temas fuera de alcance.
- Salida: validación de esquema, grounding/citas, filtros de contenido, PII.
- Operación: límites de pasos/tokens por ejecución, timeouts, presupuesto de coste.

## Prompts

- Versionados en repositorio, con plantilla, variables y changelog.
- Evaluados antes de promoción (ver `evaluacion.md`).

## Frameworks (orientativo, no imponer)

Python: SDKs nativos de proveedores, LangGraph, LlamaIndex, Pydantic AI, Microsoft Agent Framework/Semantic Kernel. .NET: Microsoft Agent Framework/Semantic Kernel, `Microsoft.Extensions.AI`. Elegir según plataforma del cliente, soporte y madurez; registrar como ADR.
