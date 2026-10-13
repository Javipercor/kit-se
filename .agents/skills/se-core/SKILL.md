---
name: se-core
description: "Kit SE (Solutions Engineering). Políticas y utilidades comunes del kit de diseño (evidencia, estados, workspace, pipeline, estilo, trazabilidad). Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Kit core

Base común del resto de skills. No produce entregables de cliente por sí misma.

## Herramientas MCP

Ejecuta los pasos deterministas de esta skill con las herramientas del servidor MCP `se-tools` (cómo usarlas, argumentos y qué hacer si no está conectado: skill `se-herramientas`). Los comandos `uv run` que aparecen más abajo son la alternativa equivalente.

- `se_init_workspace`
- `se_inventario_corpus`
- `se_validar_documento`
- `se_trazabilidad`
- `se_cobertura_requisitos`
- `se_decisiones`
- `se_registrar_decision_agente`
- `se_preferencias`

## Cuándo leer cada referencia

- `references/politica-evidencia.md`: siempre antes de redactar o revisar. Estados, precedencia de fuentes, cómo citar y cómo tratar huecos.
- `references/estilo-redaccion.md`: antes de redactar texto `client-ready`.
- `references/decisiones.md`: siempre que elijas entre alternativas, fijes un supuesto o haya preferencias tecnológicas.
- `references/pipeline.md`: si orquestas fases, decides qué fase sigue o propagas cambios.

## Scripts

| Script | Uso |
| --- | --- |
| `scripts/init_workspace.py` | Crea el layout del workspace (raíz del repositorio) sin sobrescribir nada. |
| `scripts/inventory_corpus.py [--render auto\|all\|none] [--check]` | Inventaría `RFP/` y `data-samples/`; texto por página, páginas visuales renderizadas a PNG y tablas a Markdown en `proposal/_meta/corpus/`; manifiesto `corpus-manifest.json` con páginas marcadas y motivo. Incremental. `--check` falla si está obsoleto. |
| `scripts/req_coverage.py [--doc X] [--section13]` | Cobertura requisito → HU: exige que todo requisito funcional y técnico esté ligado a una HU, sea transversal o esté fuera de alcance con motivo. |
| `scripts/decisiones.py registrar\|aceptar\|rechazar\|comentar\|listar\|ver\|check [--gate]\|render` | Registro inmutable de decisiones humanas y de agentes (eventos encadenados por hash) con validación contra preferencias. Vista en `proposal/_meta/decisiones.md`. Ver `references/decisiones.md`. |
| `scripts/preferencias.py listar\|fijar\|quitar\|validar` | Catálogo `se.preferencias.json` de tecnologías y enfoques (obligatoria, preferente, evitar, prohibida); cada cambio queda registrado como decisión humana. |
| `scripts/check_traceability.py [--strict]` | Cruza IDs `RQ`, `HU`, `F`, `SRC`, `Q` entre artefactos y genera `proposal/_meta/traceability-report.md`. |

Los scripts usan la biblioteca estándar y aprovechan herramientas opcionales si están instaladas: `poppler-utils` (`pdftotext`, `pdftoppm`), `pdfplumber` (tablas y análisis de página), LibreOffice (DOCX/PPTX → PDF) y `openpyxl`. Si faltan, se degrada con aviso y lo registra en el manifiesto (`tools`).

## Convenciones de IDs

| Prefijo | Significado | Definido en |
| --- | --- | --- |
| `RQ-NNN` | Requisito del cliente | `2-requirements-matrix.md` |
| `RQ-HU-NNN` | Requisito inferido localmente | Documento funcional |
| `Q-NNN` | Pregunta al cliente | `3-questions-for-client.md` |
| `HU-<ACR>-NN` | Historia de usuario funcional | Documento funcional |
| `RF-<ACR>-NN` | Regla funcional | Documento funcional |
| `CA-<ACR>-NN` | Criterio de aceptación funcional | Documento funcional |
| `SRC-NN` / `DQ-NN` | Fuente de datos / hallazgo de calidad | Documento de datos |
| `CAT-NN` | Criterio de aceptación técnico | Documento técnico |
| `ADR-NN` | Decisión de arquitectura | Documento de aplicación |
| `F-NNN` / `AC-FNNN-NN` | Feature / criterio de feature | `specs/` |

## Checklist común de salida

- [ ] Cabecera de control con estado, versión, fecha y fuentes.
- [ ] Ninguna afirmación relevante sin estado de evidencia.
- [ ] Ningún resto de plantilla (`<...>`, `TODO`, ejemplos).
- [ ] Todos los `A confirmar` bloqueantes están en dependencias y preguntas.
- [ ] IDs coherentes con los artefactos previos.
- [ ] Validador de la skill ejecutado y en verde.
