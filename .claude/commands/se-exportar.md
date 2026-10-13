---
description: "Kit SE · Exporta el backlog a CSV de Azure DevOps y al Excel de horas, y genera diagramas draw.io"
argument-hint: [instrucciones]
---

Lee `.claude/se/REGLAS.md` y `.claude/se-lider-proyecto.md` y actúa como `se-lider-proyecto`:

Instrucción: `$ARGUMENTS`.

- Por defecto (o con `backlog`): valida el backlog detallado (`se_validar_backlog` con `final`) y, si es válido, ejecuta `se_exportar_backlog` (formato `todos`; o `ado`, `xlsx`, `json` si se indica). Resume qué ficheros se generaron en `proposal/exports/` y los totales.
- Con `diagrama <ruta.json>`: ejecuta `se_diagrama_azure` con esa especificación (primero con `validar`).
Sin las herramientas `se_*`, usa los scripts equivalentes con `uv run --group se` (ver `.claude/se/REGLAS.md`).
