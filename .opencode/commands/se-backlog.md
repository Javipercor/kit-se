---
description: "Kit SE · Fase 7 · Backlog (catálogo → continuar → calcular_resumen)"
agent: se-planificador-backlog
---
Instrucción: `$ARGUMENTS`. Ejecuta la skill `se-backlog-hu` resolviendo la etapa según contenga `continuar`, `calcular_resumen` o ninguna de las dos. Si contiene `continuar` o `calcular_resumen`, registra antes esa aprobación como decisión humana: `uv run --group se .agents/skills/se-core/scripts/decisiones.py registrar --origen humano --autor <usuario> --area estimacion --fase 7 --titulo "Backlog: <continuar|calcular_resumen>" --decision "<qué se aprueba>" --motivo "Gate del backlog"`.
