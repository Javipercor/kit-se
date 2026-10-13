---
description: "Kit SE · Registro de decisiones: ver pendientes, aceptar, rechazar o registrar una decisión humana"
argument-hint: [instrucciones]
---

Lee `.claude/se/REGLAS.md` y `.claude/se-lider-proyecto.md` y actúa como `se-lider-proyecto`:

Instrucción: `$ARGUMENTS`.

Usa `uv run --group se .claude/skills/se-core/scripts/decisiones.py` (ver `.claude/skills/se-core/references/decisiones.md`):
- Sin instrucción: ejecuta `listar --pendientes` y `check --gate`, y presenta las propuestas pendientes (impacto alto primero) con decisión, motivo, alternativas y preferencia afectada.
- `aceptar D-NNN [nota]` / `rechazar D-NNN <motivo>`: ejecuta `aceptar`/`rechazar` con `--por` igual al nombre del usuario (pregúntalo si no lo sabes) y su texto en `--nota`/`--motivo`.
- `registrar <decisión>`: registra una decisión humana (`registrar --origen humano --autor <usuario>`) con área, título, decisión y motivo tomados del texto; si es una elección tecnológica, añade `--ambito` y `--valor`. Si sustituye a otra, `--sustituye`.
- `ver D-NNN`: muestra la decisión y su historial.
Después, si alguna fase depende de lo decidido, indica qué artefactos hay que revisar.
