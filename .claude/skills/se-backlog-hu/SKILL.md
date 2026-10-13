---
name: se-backlog-hu
description: "Kit SE (Solutions Engineering). Genera o actualiza proposal/6.0-backlog.md (backlog técnico-funcional EPIC/HU) a partir de los documentos HU-Enfoque-Funcional y HU-Enfoque-Técnico-&-Arquitectura, enriquecido con specs, datos, IA y diseño de aplicación si existen. Flujo en tres ejecuciones - catálogo preliminar, detalle tras `continuar` (criterios, dependencias, tareas por rol con horas y nivel N1-N4) y resumen de esfuerzo tras `calcular_resumen`. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Backlog HU

Contrato de salida compatible con `rfp-backlog`; las fuentes primarias son los documentos HU funcional y técnico. Si `rfp-backlog` está instalada y existen la matriz y los paquetes `proposal/4.x`/`5.x`, sus validadores de paquete pueden ejecutarse adicionalmente; no son gate de esta skill.

## Recursos

- `references/contrato-backlog.md`: formato exacto. Léelo siempre antes de escribir.
- `references/catalogo-tareas.md`: horquillas de estimación por tipo de tarea y stack. Léelo en la etapa de detalle.
- `assets/template.md`: semilla del catálogo.
- `scripts/validate_backlog.py`, `scripts/effort_summary.py`.

## Entradas

- Funcional: ruta indicada, `templates/HU-Enfoque-Funcional.md` o `proposal/HU-Enfoque-Funcional*.md`.
- Técnico: ruta indicada, `templates/HU-Enfoque-Te*cnico-&-Arquitectura.md` (tolerar normalización Unicode) o `proposal/HU-Enfoque-Te*cnico*.md`.
- Opcionales: `proposal/specs/`, `DATA-*`, `APP-*` (el enfoque de IA está en la sección 29 del técnico), matriz, preguntas, backlog previo.
- Sin funcional o sin técnico: detente y pide la ruta.

## Resolución de etapa (orden estricto)

1. La instrucción contiene `calcular_resumen` → **resumen**. Si no hay detalle válido, responde exactamente: `Para calcular el resumen de esfuerzo es necesario que exista un backlog detallado previo con tareas en proposal.`
2. Contiene `continuar` (o equivalente) y hay catálogo válido → **detalle**.
3. Cualquier otro caso → **catálogo preliminar**.

## Workflow

### Catálogo preliminar

1. Extrae del funcional: HUs, actores, alcance, flujos, reglas, datos, CA, dependencias, riesgos. Del técnico: componentes, flujos, integraciones, seguridad, infraestructura, contratos, evaluación, observabilidad, DevOps, CAT, dependencias, riesgos.
2. Construye el mapa `HU funcional → features (si hay specs) → cobertura técnica → criterios → tareas`.
3. EPICs: `1 - Arquitectura` primero; funcionales agrupadas por objetivo operativo en orden natural del caso de uso; para proyectos con componente de datos/IA, considera EPICs funcionales del tipo "Disponibilidad de datos para <decisión>" o "Propuesta inteligente de <x>" expresadas en lenguaje de negocio; `DevOps` penúltima; `Documentacion y Entregables` última.
4. Historias en lenguaje de negocio; roles técnicos prohibidos en `Como ...`. Habilitadores técnicos (ingesta, evaluación IA, identidad) van como tareas, enfoque técnico o EPICs estructurales, no como historias técnicas.
5. Una fase por HU (por defecto `Fase única - Implementación del caso de uso`).
6. Valida sin flags y responde: `Revisa el catálogo de EPICs y HUs. Si necesitas cambios, ajusta los documentos HU o el contexto de propuesta y vuelve a ejecutar la skill. Si es correcto, responde con "continuar" para generar criterios de aceptación, dependencias y tareas con estimaciones.`

### Detalle (`continuar`)

1. Replica el catálogo sin cambios bajo `## Backlog detallado`.
2. Por HU real: `##### Enfoque técnico` (si aporta, con trazas `HU-<ACR>-NN`, `F-NNN`, `§` del técnico), `##### Criterios de aceptación` (3–7, verificables), `##### Dependencias` (solo reales), `##### Tareas` por rol.
3. Estima con `references/catalogo-tareas.md`; ajusta por nivel N1–N4; tareas > 16h se dividen.
4. Valida con `--require-final`.

### Resumen (`calcular_resumen`)

`uv run --group se .claude/skills/se-backlog-hu/scripts/effort_summary.py proposal/6.0-backlog.md --write` y valida con `--require-summary`. Nunca sumes horas a mano.

## Validación

- `uv run --group se .claude/skills/se-backlog-hu/scripts/validate_backlog.py proposal/6.0-backlog.md [--require-final|--require-summary]`
- Una única reparación si falla; si sigue fallando, detente con resultado bloqueado.

## Exportación (Azure DevOps y Excel de horas)

Con el backlog detallado validado, `se_exportar_backlog` (o `uv run --group se .claude/skills/se-backlog-hu/scripts/export_backlog.py`) genera en `proposal/exports/`, sin LLM:

- `backlog-ado-import.csv`: importación en Azure DevOps Boards (Feature → User Story → Task), con el formato de `tools/backlog_to_ado`.
- `backlog-horas.xlsx`: Excel de horas con las fórmulas y estilos de `tools/backlog_to_xlsx`.
- `backlog-ado.json` y `backlog-xlsx.json`: los contratos intermedios de ambas herramientas.

Los mapeos rol → perfil ADO, bloque, tipo de actividad, rol del Excel y riesgo por nivel están en `se.config.json` → `exportacion`. Ojo: el Excel añade por su cuenta filas de Testing, PM y reuniones calculadas por porcentaje; si el backlog ya trae tareas QA explícitas, revisa que no se cuente dos veces.

## Checklist (`proposal/checklists/se-backlog-hu.md`, marcar solo lo aplicable a la etapa)

- [ ] Funcional y técnico localizados y leídos; contrato leído.
- [ ] Etapa resuelta correctamente.
- [ ] Headings exactos; EPICs estructurales en posición; sin tablas, código, comentarios ni texto meta.
- [ ] Sin HUs duplicadas ni roles técnicos en historias.
- [ ] (detalle) 3–7 criterios por HU; tareas con rol permitido y `**Nh, Nk**`; DevOps solo en su EPIC.
- [ ] (detalle) Componentes, integraciones, seguridad, datos, IA y DevOps del técnico reflejados en tareas o enfoque técnico.
- [ ] (resumen) Generado por script.
- [ ] Validador en verde.

## Informe final

Ruta del backlog y checklist, etapa, documentos fuente usados, backlog previo reutilizado o no, artefactos adicionales leídos, resultado de validaciones.
