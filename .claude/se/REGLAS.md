# Kit SE · reglas comunes (diseño de proyectos: datos, IA y desarrollo Python/.NET)

Kit de agentes, subagentes, skills y comandos para diseñar proyectos mixtos (ciencia de datos, IA/GenAI, desarrollo front/back en Python o .NET): desde el análisis del corpus del cliente hasta el backlog estimado. Estas reglas aplican a todos los agentes y herramientas (OpenCode, Claude Code, Codex).

## Idioma y estilo

- Redacta en español profesional, con tildes, `ñ` y signos de apertura. Términos técnicos en inglés solo cuando sean estándar (API, endpoint, pipeline, feature, prompt).
- Estilo de consultoría conciso: hechos, decisiones, condiciones y consecuencias. Sin relleno comercial y sin texto meta ("a continuación voy a...", "como IA...").
- Usa backticks para sistemas, campos, endpoints, operaciones, ficheros, tablas y servicios.
- Los diagramas van en `mermaid` sencillo y renderizable.

## Workspace

El workspace es la **raíz del repositorio** donde está instalado el kit (el directorio de trabajo). No hay carpetas por cliente ni por proyecto: un repositorio, una propuesta.

```text
<raíz del repositorio>/
├── RFP/                 # Documentos del cliente (solo lectura)
├── data-samples/        # Muestras de datos (solo lectura)
├── templates/           # Plantillas del cliente; si existen, prevalecen sobre las del kit
└── proposal/
    ├── _meta/           # Manifiesto de corpus, requisitos, perfiles, informes, se-pipeline-state.md
    ├── checklists/      # Checklists visibles por skill (se-*.md)
    ├── 0-document-map.md
    ├── 1-summary.md
    ├── 2-requirements-matrix.md
    ├── 3-questions-for-client.md
    ├── HU-Enfoque-Funcional-<slug>.md
    ├── DATA-Analisis-Fuentes-<slug>.md
    ├── HU-Enfoque-Tecnico-&-Arquitectura-<slug>.md   # incluye la sección 29 de IA y ciencia de datos
    ├── APP-Diseno-<slug>.md
    ├── specs/F-<NNN>-<slug>/spec.md
    └── 6.0-backlog.md
```

Inicializa con `uv run .claude/skills/se-core/scripts/init_workspace.py`. Todos los scripts del kit trabajan sobre el directorio actual si no se les pasa otra ruta.

## Convivencia con otros kits

- Todo lo del kit lleva el prefijo `se-`: agentes `se-*`, comandos `/se-*`, skills `se-*`, configuración `se.config.json`, reglas en `.claude/se/`.
- Actúa con estas reglas solo cuando el trabajo sea del kit SE (comandos `/se-*`, agentes `se-*`, skills `se-*` o petición expresa). No apliques las skills `se-*` a artefactos de otros kits ni modifiques sus ficheros.
- Si otro kit produce artefactos compatibles en `proposal/` (p. ej. `HU-Enfoque-Funcional-*.md`), trátalos como fuentes según la precedencia de evidencia, sin reescribirlos.

## Rutas del kit

- Skills: `.claude/skills/<skill>/SKILL.md` (OpenCode y Codex). En Claude Code son copias en `.claude/skills/`.
- Agentes fuente: `.opencode/agents/`. Las variantes `.claude/agents/` y `.codex/agents/` se generan con `uv run scripts/sync_agents.py`.
- Parámetros (roles, estimación, épicas fijas, estados): `se.config.json`.
- Los scripts de las skills son deterministas; úsalos en lugar de calcular o validar "a ojo". Si falta una dependencia opcional, informa y sigue la vía degradada documentada en la skill.

## Política de evidencia

Detalle completo en `.claude/skills/se-core/references/politica-evidencia.md`. Reglas no negociables:

1. No inventes hechos de negocio, sistemas, campos, volúmenes, fechas, permisos, canales, KPIs ni contratos de integración.
2. Lo que falte se escribe `A confirmar` y se registra como dependencia, riesgo o pregunta en `proposal/3-questions-for-client.md`.
3. Cada afirmación relevante lleva estado: `Evidenciado`, `Inferido`, `Propuesto`, `Preferente`, `Alternativa condicionada`, `Dependencia crítica`, `A confirmar`, `Ejemplo orientativo`, `No aplica`.
4. Precedencia de fuentes: decisión `aceptada` en el registro de decisiones > artefactos de `proposal/` validados > documentos de `RFP/` > preferencias de `se.preferencias.json` > muestras de `data-samples/` > inferencia mínima justificada > ejemplo orientativo. Una decisión explícita del usuario en la conversación se registra como decisión humana antes de aplicarla.
5. Nunca trasladas nombres de productos o sistemas de un ejemplo o de otro cliente sin evidencia.
6. No modificas `RFP/`, `data-samples/` ni `templates/`. Un artefacto con `Estado: validado` no se reescribe: propone cambios en `proposal/_meta/cambios/`.

## Herramientas del kit

Los scripts deterministas del kit están también disponibles como herramientas `se_*`: plugin `se-tools` en OpenCode y servidor MCP `se-tools` en Claude Code y Codex (mismo registro, `.claude/se/tools/se_tools.py`). Si las tienes, úsalas en lugar de lanzar el script con `uv run`: el resultado es el mismo y los argumentos van validados. Las acciones humanas (aprobar HUs, aceptar o rechazar decisiones, registrar decisiones humanas, fijar preferencias) no son herramientas: solo se ejecutan como script, a petición expresa de la persona.

| Herramienta | Script |
| --- | --- |
| `se_init_workspace` | `se-core/scripts/init_workspace.py` |
| `se_inventario_corpus` | `se-core/scripts/inventory_corpus.py` |
| `se_barrido_requisitos` · `se_agrupar_requisitos` · `se_calibrar_similitud` | `se-corpus-rfp/scripts/req_scan.py` · `req_dedupe.py` · `req_calibrate.py` |
| `se_cobertura_requisitos` · `se_estado_hus` | `se-core/scripts/req_coverage.py` · `se-hu-enfoque-funcional/scripts/hu_gate.py status` |
| `se_validar_documento` · `se_trazabilidad` · `se_validar_specs` | `validate_doc.py` · `check_traceability.py` · `validate_spec.py` |
| `se_perfilar_datos` | `se-analisis-fuentes-datos/scripts/profile_dataset.py` |
| `se_validar_backlog` · `se_resumen_esfuerzo` · `se_exportar_backlog` | `se-backlog-hu/scripts/validate_backlog.py` · `effort_summary.py` · `export_backlog.py` |
| `se_diagrama_azure` | `se-diagrama-azure/scripts/drawio_azure.py` |
| `se_decisiones` · `se_registrar_decision_agente` · `se_preferencias` | `se-core/scripts/decisiones.py` (consulta / registrar como agente) · `preferencias.py` (listar, validar) |

## Decisiones y preferencias

Detalle en `.claude/skills/se-core/references/decisiones.md`. Resumen:

- Antes de diseñar, lee `proposal/_meta/decisiones.md` (decisiones vigentes y pendientes) y `se.preferencias.json` (tecnologías y enfoques fijados).
- Registra con `decisiones.py registrar --origen agente` cada elección entre alternativas que condicione alcance, arquitectura, tecnología, datos, IA, seguridad o estimación, y los supuestos de trabajo. Cita la decisión (`D-NNN`) en el documento.
- Las preferencias `obligatoria` y `prohibida` solo se incumplen con una excepción aceptada por una persona; apartarse de una `preferente` exige motivo y alternativas.
- Nunca aceptas, rechazas ni registras decisiones humanas, ni fijas preferencias, por tu cuenta: solo cuando la persona lo pide de forma explícita.
- Las propuestas de impacto alto pendientes bloquean el gate de su fase (`decisiones.py check --gate`).

## Pipeline

| Fase | Subagente | Skill | Artefacto | Gate |
| --- | --- | --- | --- | --- |
| 0. Corpus | `se-analista-corpus` | `se-corpus-rfp` | `0..3-*.md` + registro de requisitos | Barrido de todas las páginas completo; revisión de preguntas abiertas |
| 1. Funcional | `se-analista-funcional` | `se-hu-enfoque-funcional` | `HU-Enfoque-Funcional-*.md` | Aprobación de HUs con cobertura total de requisitos (`aprobar`); el resto del documento se genera después sin nuevo gate |
| 2. Fuentes de datos | `se-analista-datos` | `se-analisis-fuentes-datos` | `DATA-Analisis-Fuentes-*.md` | Inventario y gaps de datos |
| 3. IA / ciencia de datos | `se-arquitecto-ia-datos` | `se-enfoque-ia-datos` | Sección 29 de `HU-Enfoque-Tecnico-&-Arquitectura-*.md` | `No aplica` si no hay componente analítico o IA |
| 4. Técnico | `se-arquitecto-solucion` | `se-hu-enfoque-tecnico` | `HU-Enfoque-Tecnico-&-Arquitectura-*.md` | Decisiones y dependencias críticas |
| 5. Aplicación | `se-disenador-aplicacion` | `se-diseno-aplicacion` | `APP-Diseno-*.md` | Stack y contratos API |
| 6. Specs | `se-redactor-specs` | `se-spec-feature` | `specs/F-*/spec.md` | Definition of Ready |
| 7. Backlog | `se-planificador-backlog` | `se-backlog-hu` | `6.0-backlog.md` | Catálogo → `continuar` → `calcular_resumen` |
| Transversal | `se-revisor-coherencia` | `se-core` | `_meta/revision-*.md` | Antes de entregar cualquier fase |

El orquestador es `se-lider-proyecto` (agente primario en OpenCode). En Claude Code y Codex la sesión principal asume ese rol: en Claude Code lo activan los comandos `/se-*` leyendo `.claude/se-lider-proyecto.md`; en Codex, lee y sigue `.codex/se-lider-proyecto.md` al empezar cualquier trabajo del kit SE. Las fases 2 y 3 pueden ir en paralelo con la 1 si hay muestras de datos. Las fases son iterativas: un cambio aguas arriba obliga a revisar trazabilidad aguas abajo (`check_traceability.py`).

## Delegación entre agentes

- OpenCode: herramienta `task` con el nombre del subagente. Claude Code: herramienta de subagentes (Task/Agent). Codex: subagentes de `.codex/agents/`.
- Si la herramienta no soporta subagentes, ejecuta tú mismo la skill de la fase.
- Pasa siempre al subagente: slug, artefactos de entrada y restricciones del usuario.

## Informe de retorno

Todo subagente termina con este bloque (fuera de los artefactos):

```text
### Informe de retorno — <agente>
- Artefactos: <rutas creadas o actualizadas>
- Validaciones: <script → OK/KO>
- Nuevos `A confirmar`: <n> (ver sección X)
- Preguntas añadidas: <Q-xxx, ...>
- Decisiones registradas: <D-xxx (propuesta/aceptada), ...> · pendientes de aceptación humana: <n>
- Bloqueos: <ninguno | descripción>
- Siguiente paso recomendado: <fase / acción>
```

## Cabecera de control de artefactos

Todo artefacto de `proposal/` (salvo `6.0-backlog.md`, que tiene contrato estricto) empieza tras el título con:

```markdown
> **Estado:** borrador · **Versión:** 0.1 · **Fecha:** AAAA-MM-DD · **Fuentes:** `RFP/...`, `proposal/...`
```
