---
description: "Kit SE · Tecnologías y enfoques de arquitectura preferidos: listar, fijar o quitar"
agent: se-lider-proyecto
---
Instrucción: `$ARGUMENTS`.

Usa `uv run --group se .agents/skills/se-core/scripts/preferencias.py`:
- Sin instrucción: `listar` y `validar`, y resume las preferencias por ámbito y nivel.
- `fijar <ámbito> <valor> <nivel> [motivo]` (o en lenguaje natural, p. ej. "Azure obligatoria en cloud porque somos partner"): ejecuta `fijar` con `--ambito`, `--valor`, `--nivel`, `--motivo` y `--por` igual al nombre del usuario. Ámbitos y niveles válidos en `se.config.json` → `decisiones`. Añade `--alias` con nombres alternativos habituales del producto y `--aplica-si` si el usuario pone condiciones.
- `quitar PREF-NN <motivo>`: ejecuta `quitar`.
Después ejecuta `decisiones.py check` y avisa de decisiones ya tomadas que ahora incumplen las preferencias.
