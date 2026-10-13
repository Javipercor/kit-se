---
description: "Kit SE · Inicializa el workspace en la raíz del repositorio: carpetas, uv init, uv venv y dependencias del kit"
agent: se-lider-proyecto
---
Indicaciones: `$ARGUMENTS`.

Ejecuta en la raíz del repositorio `uv run .agents/skills/se-core/scripts/init_workspace.py`, añadiendo:
- `--embeddings` si las indicaciones piden similitud por embeddings o Azure OpenAI;
- `--no-deps` si piden no instalar dependencias.

El script crea las carpetas y `proposal/_meta/se-pipeline-state.md`; si no hay `pyproject.toml` ejecuta `uv init --bare --no-workspace`, si no hay `.venv` ejecuta `uv venv`, y añade las dependencias del kit al grupo `se` (`uv add --group se …`). No toques el resto de `pyproject.toml`.

Si uv no está instalado (exit 3), dímelo con el enlace de instalación y no sigas. Al terminar, resume qué se creó y dime qué documentos debo dejar en `RFP/` y `data-samples/`. A partir de aquí, todos los scripts del kit se ejecutan con `uv run --group se …`, nunca con `python`.
