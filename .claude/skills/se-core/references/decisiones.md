# Decisiones y preferencias

Dos piezas, ambas en la raíz del repositorio:

- **Registro de decisiones** (`proposal/_meta/decisiones/eventos.jsonl`, vista en `proposal/_meta/decisiones.md`): toda decisión relevante, humana o de agente, con su motivo, alternativas, evidencia y a qué afecta. Es inmutable (eventos encadenados por hash): nada se edita ni se borra, se sustituye.
- **Preferencias** (`se.preferencias.json`): tecnologías y enfoques de arquitectura fijados por personas, con nivel `obligatoria`, `preferente`, `evitar` o `prohibida`.

Script: `uv run --group se .claude/skills/se-core/scripts/decisiones.py …` y `… preferencias.py …`.

## Qué registra un agente

Registra con `--origen agente --autor <tu-agente>` cuando eliges entre alternativas y la elección condiciona el resultado:

| Área | Ejemplos |
| --- | --- |
| `tecnologia` | Nube, lenguaje, framework, BBDD, LLM, orquestador, observabilidad. Siempre con `--ambito` y `--valor` |
| `arquitectura` | Patrón (monolito modular, eventos, RAG, agentes), separación de componentes, estrategia de integración. Con `--ambito patron-arquitectura` si es un enfoque de catálogo |
| `alcance` | Qué entra o queda fuera, faseado, MVP |
| `datos` / `ia` | Fuente elegida, estrategia de ingesta, tipo de modelo, métrica de evaluación |
| `seguridad`, `integracion`, `despliegue` | Identidad delegada vs técnica, sync vs async, entornos |
| `estimacion` | Supuestos que mueven horas (volúmenes, nº de integraciones, reutilización) |

Registra también los **supuestos de trabajo** (`--tipo supuesto`) que sostienen el diseño sin evidencia, enlazados a su pregunta `Q-NNN` en `--evidencia`.

No registres: redacción, formato, ni decisiones triviales sin alternativa real.

Campos: `--titulo` corto, `--decision` en una frase, `--motivo` (obligatorio), `--alternativas` consideradas, `--evidencia` (`RQ-`, `Q-`, documento y página), `--afecta` (`HU-`, `ADR-`, `F-`, componentes), `--fase`.

## Estados y quién decide

| Origen | Estado inicial | Cómo cambia |
| --- | --- | --- |
| agente | `propuesta` | Una persona la acepta o rechaza (`aceptar` / `rechazar --motivo`) |
| humano | `aceptada` | Solo una decisión humana posterior con `--sustituye` la deja `sustituida` |

- Un agente **nunca** ejecuta `aceptar`, `rechazar`, `registrar --origen humano`, `preferencias.py fijar` ni `quitar` por iniciativa propia. Solo cuando la persona lo pide en la conversación de forma explícita, citando lo que dijo en `--nota` o `--motivo`; en OpenCode estas acciones piden confirmación siempre.
- Las propuestas de impacto alto (áreas de `areas_impacto_alto` en `se.config.json`) bloquean el gate de la fase (`decisiones.py check --gate`) hasta que una persona las acepte o rechace.
- Una decisión `aceptada` prevalece sobre cualquier otra fuente. Para cambiarla, registra otra con `--sustituye D-NNN`.
- Un agente que no está de acuerdo con una decisión vigente no la contradice en los documentos: registra una propuesta nueva con `--sustituye` y lo explica.

## Cómo se usan las preferencias

Antes de elegir tecnología o enfoque, consulta `preferencias.py listar` (o la sección de preferencias de `decisiones.md`).

| Nivel | Qué haces |
| --- | --- |
| `obligatoria` | Úsala. Si el cliente exige otra cosa (requisito `Evidenciado`) o no encaja, registra la decisión y una excepción `--tipo excepcion --excepcion-de PREF-NN` con el motivo; queda pendiente de una persona |
| `preferente` | Es la opción por defecto. Si te apartas, registra la decisión con `--preferencia PREF-NN`, `--motivo` y `--alternativas`; queda pendiente de una persona |
| `evitar` | No la propongas salvo motivo fuerte, con excepción registrada |
| `prohibida` | No la uses ni la recomiendes. Solo con excepción aceptada por una persona |

Respeta `aplica_si`: una preferencia condicionada solo aplica si se cumple su condición. Si el pliego impone una tecnología que choca con una preferencia, el requisito del cliente manda: regístralo como excepción con la evidencia y deja que la persona confirme.

## En los documentos

- Cita la decisión que respalda cada elección: `(D-007)`. Cada ADR de `APP-Diseno-*.md` cita su `D-NNN`.
- Marca como `Preferente` o `Propuesto` lo que esté en `propuesta`; como decidido solo lo `aceptada`.
- No cites decisiones `rechazada` o `sustituida` como vigentes.

## Validación

- `decisiones.py check`: integridad de la cadena, citas `D-NNN` existentes y vigentes, ADR sin decisión, cumplimiento de preferencias y menciones de tecnologías prohibidas en los documentos.
- `decisiones.py check --gate`: además, falla si hay propuestas de impacto alto pendientes.
- `preferencias.py validar`: esquema del catálogo y preferencias editadas a mano sin decisión que las respalde.
