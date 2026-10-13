---
name: se-analisis-fuentes-datos
description: "Kit SE (Solutions Engineering). Analiza las fuentes de datos de un proyecto (APIs, ficheros, BBDD, eventos, SaaS, data lake/warehouse): inventario SRC-NN, perfilado de muestras, calidad DQ-NN, datos personales, modelo conceptual, linaje, contratos de datos, estrategia de ingesta e idoneidad para analítica o IA. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Análisis de fuentes de datos

## Salida

`proposal/DATA-Analisis-Fuentes-<slug>.md` (plantilla `assets/template.md`), perfiles en `proposal/_meta/data-profiles/` y `proposal/checklists/se-analisis-fuentes-datos.md`.

## Herramientas MCP

Ejecuta los pasos deterministas de esta skill con las herramientas del servidor MCP `se-tools` (cómo usarlas, argumentos y qué hacer si no está conectado: skill `se-herramientas`). Los comandos `uv run` que aparecen más abajo son la alternativa equivalente.

- `se_perfilar_datos`
- `se_validar_documento`
- `se_registrar_decision_agente`
- `se_preferencias`

## Workflow

1. Inventario: extrae fuentes del corpus, matriz y documento funcional. Una fila `SRC-NN` por fuente lógica. Clasifica tipo (`transaccional`, `analítico`, `batch`, `evento`, `documental`, `SaaS`, `configuración`, `operacional`) y modo de acceso (`API`, `fichero`, `BD`, `stream`, `CDC`, `scraping` — este último solo si es legal y está evidenciado).
2. Perfilado: `uv run --group se .claude/skills/se-analisis-fuentes-datos/scripts/profile_dataset.py [--max-rows 200000]`. Genera un `.md` y un `.json` por fichero (columnas, tipos, nulos, cardinalidad, claves candidatas, rangos de fechas, posibles PII, valores frecuentes). Requiere `pandas`; `pyarrow` para parquet y `openpyxl` para Excel.
3. Lee los perfiles, no los ficheros completos. Resume hallazgos por dataset en la sección 4.
4. Calidad: hallazgos `DQ-NN` por dimensión con evidencia del perfil (p. ej. "`fecha_alta` 18 % nulos").
5. Privacidad: lista campos con PII detectada o probable, su necesidad para el caso de uso y tratamiento propuesto (minimización, seudonimización, enmascarado en logs).
6. Modelo conceptual (`erDiagram`) y linaje (`flowchart LR`) solo con entidades y relaciones soportadas por evidencia o por claves candidatas del perfil.
7. Contratos de datos por fuente: esquema, claves, semántica, frecuencia/frescura, volumetría, SLA, errores, versionado, propietario. Lo no evidenciado, `A confirmar`.
8. Estrategia de integración: compara opciones (`references/patrones-integracion.md`) con ventajas, riesgos y condición.
9. Idoneidad para analítica/IA: profundidad histórica, granularidad, disponibilidad de etiqueta/target, sesgos de muestreo, riesgo de fuga, latencia requerida vs disponible.
10. Valida: `uv run --group se .claude/skills/se-core/scripts/validate_doc.py <salida> .claude/skills/se-analisis-fuentes-datos/assets/spec.json`.

## Reglas

- Muestras ≠ producción: indica siempre tamaño y representatividad de la muestra.
- La detección de PII del script es heurística: confirma por nombre y semántica de la columna.
- No publiques valores reales de PII en el documento: usa los ejemplos enmascarados del perfil.
- Volúmenes y frecuencias de producción solo con evidencia.

## Checklist

- [ ] Todas las fuentes del funcional aparecen en el inventario.
- [ ] Cada muestra de `data-samples/` tiene perfil y resumen.
- [ ] Hallazgos de calidad basados en perfil.
- [ ] PII identificada con tratamiento.
- [ ] Contrato por fuente con huecos `A confirmar` y preguntas.
- [ ] Validador en verde.
