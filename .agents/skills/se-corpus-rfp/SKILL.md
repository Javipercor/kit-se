---
name: se-corpus-rfp
description: "Kit SE (Solutions Engineering). Analiza el corpus de una oportunidad (RFP, pliegos, anexos, actas, correos, presentaciones) y genera mapa documental, resumen ejecutivo, matriz de requisitos RQ-NNN y preguntas al cliente Q-NNN. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Corpus RFP

## Salidas

| Fichero | Plantilla |
| --- | --- |
| `proposal/0-document-map.md` | `assets/0-document-map.md` |
| `proposal/1-summary.md` | `assets/1-summary.md` |
| `proposal/2-requirements-matrix.md` | Generada por `req_scan.py matrix` desde `proposal/_meta/registro-requisitos.json` |
| `proposal/3-questions-for-client.md` | `assets/3-questions-for-client.md` |
| `proposal/checklists/se-corpus-rfp.md` | Checklist de esta skill |

## Herramientas MCP

Ejecuta los pasos deterministas de esta skill con las herramientas del servidor MCP `se-tools` (cómo usarlas, argumentos y qué hacer si no está conectado: skill `se-herramientas`). Los comandos `uv run` que aparecen más abajo son la alternativa equivalente.

- `se_inventario_corpus`
- `se_barrido_requisitos`
- `se_agrupar_requisitos`
- `se_calibrar_similitud`

## Workflow

1. `uv run .agents/skills/se-core/scripts/init_workspace.py` si falta el layout.
2. `uv run --group se .agents/skills/se-core/scripts/inventory_corpus.py` (modo `--render auto`): texto por página, páginas visuales en PNG y tablas en Markdown. Revisa los avisos (herramientas que faltan, escaneados, límite `--max-render`).
3. Mapa documental y resumen: lectura general del corpus para entender propósito, jerarquía y contexto de cada documento.
4. **Barrido exhaustivo de requisitos** (ver sección siguiente): ninguna página queda sin revisar.
5. **Consolidación** en `proposal/_meta/registro-requisitos.json` y generación de la matriz con `req_scan.py matrix`. La matriz no se edita a mano.
6. Preguntas: una por ambigüedad, con supuesto de trabajo y artefacto que bloquea. Prioriza `Alta` las que afectan a alcance, datos disponibles, identidad/permisos y stack.
7. En pasadas posteriores: conserva IDs, añade al final y marca retirados como `Fuera de alcance`; nunca renumeres.

## Barrido exhaustivo de requisitos

Script: `uv run --group se .agents/skills/se-corpus-rfp/scripts/req_scan.py <subcomando>`.

1. `plan`: crea una unidad por página (o fragmento de texto, diapositiva u hoja) de cada documento. Si un documento cambia, sus unidades vuelven a pendientes y sus revisiones previas se archivan.
2. Bucle hasta que no queden pendientes:
   - `next --batch 5` muestra las siguientes unidades con su texto, la imagen obligatoria si la hay, las tablas y la plantilla JSON.
   - Para cada unidad, si tiene imagen, ábrela. Identifica **todos** los requisitos funcionales y técnicos (y también contractuales o de gestión) expresados en esa página, aunque se repitan en otras.
   - Escribe `proposal/_meta/req-scan/units/<unidad>.json` con `revisado: true`, `leido_como_imagen`, la lista de `requisitos` en forma canónica (texto normalizado, actor, acción, objeto, condición, tipo, cita literal breve, prioridad) y `notas`. Usa siempre el mismo término para el mismo objeto de negocio (ver `references/consolidacion.md`). Una página sin requisitos se registra igualmente con lista vacía y una nota breve.
3. `status`: progreso por documento y errores de formato (por ejemplo, página con imagen no leída como imagen). Debe terminar en verde.
4. `findings`: genera `req-scan/hallazgos.md` con cada hallazgo `H-xxxxxxxx` y los pendientes de consolidar.
5. Agrupación de similares: `uv run --group se .agents/skills/se-corpus-rfp/scripts/req_dedupe.py groups` genera `req-scan/grupos.md` con los grupos de hallazgos parecidos (entre sí y contra requisitos ya existentes) y los que no tienen similares.
6. Consolidación en `registro-requisitos.json` siguiendo `references/consolidacion.md`:
   - Para cada grupo decide la relación (`duplicado`, `refinamiento`, `complementario`, `conflicto`, `distinto`, `mixto`), aplícala y anótala en `decisiones`.
   - Un requisito `RQ-NNN` agrupa todos los hallazgos que expresan lo mismo (`hallazgos: [...]`); así se conservan todos los orígenes. Los matices de un refinamiento van a `detalles`.
   - Los conflictos generan una pregunta `Q-NNN` y dejan los RQ en `A confirmar`.
   - Agrupa los requisitos en capacidades de negocio (`capacidades` + campo `capacidad`); los técnicos generales son `TRANSVERSAL`.
   - Un hallazgo que no es un requisito (contexto, antecedentes) va a `descartados` con motivo.
   - Cada hallazgo termina asignado exactamente una vez.
   - Requisitos sin hallazgo solo con estado `Inferido` y justificación en `notas`.
   - `Fuera de alcance` exige `motivo_exclusion`; es una propuesta que la persona aprueba junto con las HUs.
7. `check`: valida barrido completo, consolidación total, IDs, tipos, estados, prioridades, decisiones de agrupación, ausencia de duplicados y capacidades.
8. `matrix`: genera `2-requirements-matrix.md` con el origen de cada requisito (documento, página, si se leyó como imagen).

### Similitud por embeddings (opcional)

Por defecto la agrupación es léxica y sin dependencias. Para detectar paráfrasis con distinto vocabulario se puede activar Azure OpenAI en `se.config.json`:

```json
"dedupe": {"backend": "azure",
           "azure": {"endpoint_env": "AZURE_OPENAI_ENDPOINT", "api_key_env": "AZURE_OPENAI_API_KEY",
                     "api_version": "2024-10-21", "deployment": "text-embedding-3-small",
                     "alta": 0.85, "revisar": 0.72}}
```

- Requiere el SDK en el grupo `se`: `uv run .agents/skills/se-core/scripts/init_workspace.py --embeddings` (o `/se-init embeddings`), que añade `openai` y `azure-identity`.
- Los embeddings se guardan en `req-scan/embeddings.jsonl`; solo se calculan los textos nuevos.
- Un par es candidato si lo es por la vía léxica o por la de embeddings. Los conflictos de valores se siguen detectando por números.
- Si falta configuración o falla la llamada, se continúa en modo léxico con un aviso; `grupos.md` indica qué similitud se usó.
- Los umbrales de partida son orientativos. Calíbralos con propuestas ya consolidadas: `uv run --group se .agents/skills/se-corpus-rfp/scripts/req_calibrate.py [. ruta/a/otro/workspace …] [--write-config]`. Toma los hallazgos fusionados en un mismo RQ como pares positivos y el resto como negativos, y propone `alta` (precisión ≥ 0,9) y `revisar` (recall ≥ 0,95) para el léxico y para los embeddings. Necesita al menos 15 pares fusionados.

Corpus grandes: el barrido se puede repartir por documento (`next --doc RUTA`) entre varias instancias de `se-analista-corpus` en paralelo; cada unidad es un fichero independiente, así que no hay conflictos. La consolidación la hace una sola instancia al final.

Formato del registro:

```json
{"capacidades": [{"id": "CAP-01", "nombre": "Planificar visitas", "descripcion": "..."}],
 "requisitos": [{"id": "RQ-001", "texto": "...", "tipo": "Funcional", "prioridad": "Obligatorio",
                 "estado": "Evidenciado", "capacidad": "CAP-01", "hallazgos": ["H-3e327017", "H-ef0270de"],
                 "detalles": ["Orden por potencial de venta"], "notas": "", "motivo_exclusion": ""}],
 "descartados": [{"hallazgo": "H-1a2b3c4d", "motivo": "Antecedentes, no es un requisito"}],
 "decisiones": [{"grupo": "G-714fe0b2", "relacion": "refinamiento", "motivo": "El anexo añade el criterio de orden"}]}
```

Tipos y estados válidos en `se.config.json` → `requirements`.

## Reglas específicas de proyectos de datos e IA

- Extrae como requisitos explícitos: fuentes y sistemas citados, volúmenes, histórico disponible, frecuencias, métricas de éxito del modelo, requisitos de explicabilidad, supervisión humana, idioma, residencia de datos y restricciones de uso de modelos externos.
- Si el pliego exige un stack (.NET, Python, nube concreta, framework), regístralo como `Restricción tecnológica` con su cita.

## Checklist

- [ ] Manifiesto generado y sin obsolescencia (`inventory_corpus.py --check`).
- [ ] Todos los documentos del manifiesto aparecen en el mapa documental.
- [ ] Todas las páginas de `flagged_pages` con imagen se han leído como imagen y constan en el mapa documental.
- [ ] `req_scan.py status` en verde: todas las unidades revisadas, con imagen cuando la tienen.
- [ ] `req_scan.py check` en verde: todos los hallazgos consolidados o descartados con motivo, todos los grupos decididos, sin duplicados y con capacidades.
- [ ] Matriz generada con `req_scan.py matrix`.
- [ ] Cada `A confirmar` de la matriz tiene pregunta `Q-NNN`.
- [ ] Sin restos de plantilla.
