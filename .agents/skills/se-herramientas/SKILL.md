---
name: se-herramientas
description: "Kit SE (Solutions Engineering). Enseña a usar las herramientas deterministas del kit expuestas por el servidor MCP se-tools (se_barrido_requisitos, se_cobertura_requisitos, se_validar_documento, se_exportar_backlog, se_diagrama_azure…): qué herramienta usar en cada paso, sus argumentos, cómo leer el resultado y qué hacer si el MCP no está conectado. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Herramientas del kit SE (servidor MCP `se-tools`)

Las comprobaciones, cálculos y exportaciones del kit no los hace el modelo: los hacen scripts deterministas. El servidor MCP `se-tools` los expone como herramientas tipadas `se_*` en OpenCode, Claude Code y Codex. Las skills de cada fase dicen **cuándo** usarlas; esta skill explica **cómo**.

## Reglas

1. Usa la herramienta `se_*` antes que el comando `uv run` equivalente: valida los argumentos y devuelve un resultado estructurado.
2. El workspace es la raíz del repositorio (el directorio de trabajo del harness). No pases rutas absolutas del repositorio salvo para ficheros concretos.
3. Lee siempre el resultado: `{"ok": bool, "exit_code": int, "output": str}`. Si `ok` es `false`, el `output` dice qué corregir; corrige y vuelve a ejecutar. `exit_code` 2 significa argumentos inválidos (revisa el esquema), 1 significa que la comprobación falló.
4. Las acciones humanas no son herramientas a propósito: aprobar HUs, aceptar o rechazar decisiones, registrar decisiones humanas y fijar o quitar preferencias. Solo se ejecutan como script, cuando la persona lo pide de forma explícita (ver `se-core/references/decisiones.md`).
5. No reintentes en bucle una herramienta que falla siempre igual: informa del error en el Informe de retorno.

## Catálogo

| Herramienta | Cuándo | Argumentos | Ejemplo |
| --- | --- | --- | --- |
| `se_init_workspace` | `/se-init` | `embeddings`, `sin_dependencias` | `{}` |
| `se_inventario_corpus` | Fase 0, al empezar o si cambia `RFP/` | `render` (`auto`/`all`/`none`), `completo` | `{"render": "auto"}` |
| `se_barrido_requisitos` | Fase 0: barrido página a página | `accion` (`plan`, `next`, `status`, `findings`, `check`, `matrix`), `lote`, `documento` | `{"accion": "next", "lote": 5}` |
| `se_agrupar_requisitos` | Fase 0: similares y validación de la consolidación | `accion` (`groups`, `lint`) | `{"accion": "groups"}` |
| `se_calibrar_similitud` | Ajustar umbrales con propuestas consolidadas | `workspaces`, `precision`, `recall` | `{"workspaces": ["."]}` |
| `se_cobertura_requisitos` | Fase 1: requisitos → HUs; tabla 13.1 | `documento`, `seccion13` | `{"seccion13": true}` |
| `se_estado_hus` | Fase 1: ¿propuesta, aprobada o modificada? | `documento` | `{}` |
| `se_validar_documento` | Al terminar cada documento | `documento`, `tipo` (`funcional`, `funcional-hus`, `datos`, `tecnico`, `ia-seccion29`, `aplicacion`) | `{"documento": "proposal/HU-Enfoque-Funcional-x.md", "tipo": "funcional-hus"}` |
| `se_trazabilidad` | Revisión y antes de entregar | `estricto` | `{}` |
| `se_validar_specs` | Fase 6 | — | `{}` |
| `se_perfilar_datos` | Fase 2 | `fichero`, `max_filas` | `{}` |
| `se_validar_backlog` | Fase 7, cada etapa | `final`, `resumen` | `{"final": true}` |
| `se_resumen_esfuerzo` | Fase 7, `calcular_resumen` | `escribir` | `{"escribir": true}` |
| `se_exportar_backlog` | Tras el backlog detallado | `formato` (`todos`, `json`, `ado`, `xlsx`) | `{"formato": "todos"}` |
| `se_diagrama_azure` | Fase 4/5, soluciones Azure | `especificacion`, `salida`, `validar` | `{"especificacion": "proposal/diagramas/arquitectura.json", "validar": true}` |
| `se_decisiones` | Antes de diseñar y en cada gate | `accion` (`listar`, `ver`, `check`), `id`, `pendientes`, `gate` | `{"accion": "check", "gate": true}` |
| `se_registrar_decision_agente` | Al elegir entre alternativas o fijar un supuesto | `autor`, `area`, `titulo`, `decision`, `motivo` + opcionales | ver abajo |
| `se_preferencias` | Antes de elegir tecnología | `accion` (`listar`, `validar`), `ambito` | `{"accion": "listar", "ambito": "cloud"}` |

Registrar una decisión de agente:

```json
{"autor": "se-arquitecto-solucion", "area": "tecnologia", "titulo": "Backend", "decision": "ASP.NET Core 8",
 "motivo": "Equipo del cliente .NET (RQ-031)", "ambito": "framework-backend", "valor": "ASP.NET Core",
 "alternativas": ["FastAPI"], "evidencia": ["RQ-031"], "afecta": ["ADR-01"], "preferencia": "PREF-02"}
```

## Si el MCP no está conectado

Cada herramienta tiene el mismo comportamiento desde la línea de comandos (útil también en CI):

```bash
uv run --no-project .agents/se/tools/se_tools.py list                                   # catálogo con esquemas
uv run --no-project .agents/se/tools/se_tools.py call se_validar_backlog '{"final": true}'
```

En Claude Code la ruta es `.claude/se/tools/se_tools.py`. Si tampoco funciona: falta `uv` o el repositorio no se inicializó (`/se-init`). Las skills de cada fase indican además el script concreto (`uv run --group se …`) como último recurso.

## Entorno

- El servidor arranca con `uv run --no-project` (solo biblioteca estándar), así que se conecta aunque el repositorio no esté inicializado.
- Cada herramienta ejecuta su script con el entorno del repositorio (grupo `se` de `pyproject.toml`, que crea `/se-init`); si no existe, con el Python del servidor. `SE_PYTHON` fuerza un intérprete y `SE_WORKSPACE` otra raíz.
