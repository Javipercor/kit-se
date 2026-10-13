---
name: se-enfoque-ia-datos
description: "Kit SE (Solutions Engineering). Diseña el enfoque de IA y ciencia de datos de un caso de uso como sección 29 del documento HU-Enfoque-Técnico-&-Arquitectura: formulación del problema, elección entre reglas, ML clásico, forecasting, optimización, NLP, GenAI/RAG o agentes, datos y features, evaluación offline/online, fases PoC-piloto-producción con go/no-go, MLOps/LLMOps, IA responsable y coste. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Enfoque de IA y ciencia de datos

## Salida

La **sección 29 «Enfoque De IA Y Ciencia De Datos»** de `proposal/HU-Enfoque-Tecnico-&-Arquitectura-<slug>.md` (subsecciones 29.1–29.12 de la plantilla de `se-hu-enfoque-tecnico`) y `proposal/checklists/se-enfoque-ia-datos.md`. No hay documento de IA aparte.

- Si el documento técnico aún no existe, créalo desde `.agents/skills/se-hu-enfoque-tecnico/assets/template.md` (o la plantilla del cliente) con título y cabecera de control, y rellena solo la sección 29; el resto lo redacta después `se-arquitecto-solucion`.
- Si ya existe, edita solo la sección 29. Si algo de las secciones 1–28 contradice tu enfoque, no lo reescribas: anótalo en 29.12 y en el Informe de retorno.
- Si el caso de uso no tiene componente analítico ni de IA, la sección 29 es una sola línea `No aplica: <motivo>`.

## Referencias (lee solo las que apliquen)

- `references/ml-clasico.md`: supervisado, no supervisado, forecasting, optimización.
- `references/genai-agentes.md`: LLM, RAG, agentes, tools, guardrails.
- `references/evaluacion.md`: métricas, datasets de evaluación, gates de promoción, monitorización.

## Herramientas MCP

Ejecuta los pasos deterministas de esta skill con las herramientas del servidor MCP `se-tools` (cómo usarlas, argumentos y qué hacer si no está conectado: skill `se-herramientas`). Los comandos `uv run` que aparecen más abajo son la alternativa equivalente.

- `se_validar_documento`
- `se_registrar_decision_agente`
- `se_preferencias`
- `se_decisiones`

## Workflow

1. Lee funcional, datos (`DATA-Analisis-Fuentes-*`), matriz, preguntas, decisiones vigentes (`proposal/_meta/decisiones.md`) y preferencias (`preferencias.py listar`, ámbitos `llm`, `embeddings`, `orquestacion-agentes`, `ml`, `mlops`).
2. Clasifica el problema y responde "¿hace falta IA?" con una alternativa no-IA como baseline.
3. Formula: decisión de negocio soportada, unidad de predicción/generación, target u objetivo, horizonte, frecuencia de inferencia (batch, near-real-time, interactivo), consumidor, coste del error (falsos positivos vs negativos).
4. Datos y features: enlaza con el documento de datos; marca disponibilidad y riesgo de fuga.
5. Enfoque: baseline + candidatos (ML) o patrón GenAI (prompting, RAG, agente con tools, multi-agente) justificado por complejidad. Compara opciones en la tabla 29.6 y registra la elegida con `decisiones.py registrar --area ia` (y `--ambito`/`--valor` si fija tecnología), citando su `D-NNN` en la columna Decisión.
6. Evaluación: métricas técnicas y de negocio, dataset de evaluación y su construcción, umbrales (`A confirmar` si no hay evidencia), evaluación humana.
7. Fases y go/no-go: PoC → piloto → producción con criterios medibles por fase.
8. MLOps/LLMOps, IA responsable (sesgo, explicabilidad, supervisión humana, transparencia, clasificación regulatoria `A confirmar`), coste y latencia.
9. Valida solo tu sección: `uv run --group se .agents/skills/se-core/scripts/validate_doc.py proposal/HU-Enfoque-Tecnico-&-Arquitectura-<slug>.md .agents/skills/se-enfoque-ia-datos/assets/spec.json --section 29`.

## Reglas

- No fijes proveedor de modelos, framework de agentes ni plataforma sin evidencia; nombra familias de opciones.
- Las cifras de rendimiento esperado nunca se prometen: son hipótesis a validar en PoC.
- Si no hay datos suficientes para entrenar o evaluar, la primera fase es de recolección/etiquetado y se dice explícitamente.

## Checklist

- [ ] Alternativa no-IA evaluada.
- [ ] Problema formulado con unidad, objetivo, horizonte, frecuencia y coste del error.
- [ ] Plan de evaluación con dataset, métricas y umbrales.
- [ ] Go/no-go por fase.
- [ ] Riesgos de IA responsable y clasificación regulatoria tratados.
- [ ] Validador en verde.
