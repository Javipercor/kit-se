---
description: "Kit SE · Ejecuta el pipeline de diseño hasta el siguiente gate humano"
argument-hint: [instrucciones]
---

Lee `.claude/se/REGLAS.md` y `.claude/se-lider-proyecto.md` y actúa como `se-lider-proyecto`:

Indicaciones: `$ARGUMENTS` (pueden estar vacías: fases a omitir, stack preferido, prioridades).
Revisa `proposal/_meta/se-pipeline-state.md`, determina las fases aplicables y ejecuta las siguientes fases pendientes delegando en los subagentes `se-*`, hasta el siguiente gate humano. Al final, actualiza el estado y resume las decisiones pendientes.
