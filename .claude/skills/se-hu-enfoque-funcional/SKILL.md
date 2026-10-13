---
name: se-hu-enfoque-funcional
description: "Kit SE (Solutions Engineering). Genera el documento HU-Enfoque-Funcional en dos etapas con aprobación humana: primero propone las historias de usuario (Como/quiero/para con trazas a requisitos) y, cuando el usuario las aprueba, genera el resto del documento (objetivo, actores, disparadores, alcance, flujos, reglas, datos, criterios de aceptación, trazabilidad, dependencias, riesgos y métricas) anclado a las HUs aprobadas. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# HU Enfoque Funcional

El documento se construye en dos etapas. Las historias de usuario son la decisión de alcance: se proponen, se revisan y se aprueban; el resto del documento se deriva de ellas sin modificarlas.

```text
Etapa 1: propuesta de HUs ──► revisión humana (editar o pedir cambios) ──► "aprobar"
                                                                              │
Etapa 2: hu_gate.py approve ──► secciones 3–17 derivadas de las HUs aprobadas ┘
```

## Entradas

- Obligatorio: corpus (`proposal/_meta/corpus/`) o descripción del caso de uso por el usuario.
- Recomendado: `2-requirements-matrix.md`, `3-questions-for-client.md`, `1-summary.md`.
- Plantilla: `templates/HU-Enfoque-Funcional.md` del cliente si existe; si no, `assets/template.md`.

## Salida

`proposal/HU-Enfoque-Funcional-<slug>.md`, la instantánea de aprobación `proposal/_meta/hu-aprobadas-<slug>.json` y `proposal/checklists/se-hu-enfoque-funcional.md`.

## Resolución de etapa

Consulta primero `uv run --group se .claude/skills/se-hu-enfoque-funcional/scripts/hu_gate.py status <doc>` si el documento existe.

| Situación | Etapa |
| --- | --- |
| No existe documento, o estado `propuesta` sin instrucción de aprobar | **1 · Propuesta de HUs** (crear o revisar) |
| Estado `propuesta` y el usuario aprueba explícitamente (`aprobar`, "apruebo las HUs", "ok, adelante con estas HUs") | **2 · Documento completo** |
| Estado `aprobada` | **2** (completar o actualizar secciones 3–17) |
| Estado `modificada` (la sección 2 cambió tras aprobar) | Detente: muestra los cambios de `status` y pide reaprobar o revertir |

La aprobación debe ser explícita y referida a las HUs. Una respuesta ambigua ("vale", "sigue") no basta si no queda claro que se aprueban: pregunta.

## Etapa 1 · Propuesta de HUs

1. Lee matriz, preguntas, resumen y los textos de corpus relevantes.
2. Elige un acrónimo estable `<ACR>` (2–6 letras).
3. Redacta solo título, cabecera de control (`Estado: HUs en revisión`), `## 1. Contexto` (breve: problema, actores principales, por qué ahora) y `## 2. Historia De Usuario`.
4. Entre 3 y 8 HUs. Cada una con:
   - `### HU-<ACR>-NN. <Nombre>`
   - `**Como** <rol de negocio>,` / `**quiero** <capacidad>,` / `**para** <resultado>.`
   - `**Requisitos:** <IDs de la matriz o RQ-HU-NNN si es inferido>`
5. Deriva las HUs de las capacidades del registro (`proposal/2-requirements-matrix.md`, sección Capacidades): normalmente una HU por capacidad, o varias si hay actores o resultados distintos. Una HU no mezcla más de dos capacidades. Si no hay capacidades (sin registro), agrupa tú los requisitos por objetivo de negocio.
6. Requisitos transversales: los requisitos técnicos que aplican a todas las HUs (disponibilidad, autenticación, auditoría…) se declaran una vez al final de la sección 2 con `**Requisitos transversales:** RQ-0XX, RQ-0YY`. Los que aplican solo a algunas HUs se ligan a esas HUs.
7. Criterios para el conjunto:
   - Cada HU es una capacidad con valor propio, no un paso técnico ni una pantalla.
   - Sin solapes: dos HUs no comparten el mismo objetivo.
   - Cobertura total: todo requisito funcional y técnico del registro queda ligado a alguna HU, declarado transversal o propuesto como `Fuera de alcance` (estado en el registro + `motivo_exclusion`). Los contractuales y de gestión no se exigen (van al backlog).
   - En casos con IA, la IA nunca es actor; la HU describe qué recibe y decide la persona (propuesta, validación, corrección, feedback).
8. Valida:
   - `uv run --group se .claude/skills/se-core/scripts/validate_doc.py <doc> .claude/skills/se-hu-enfoque-funcional/assets/spec-hu.json`
   - `uv run --group se .claude/skills/se-core/scripts/req_coverage.py --doc <doc>`: debe quedar sin huecos. Si quedan, crea o amplía HUs, declara transversales o propone exclusión; no presentes las HUs con huecos.
9. Presenta al usuario, fuera del documento:
   - la lista de HUs en una línea cada una, con su capacidad y sus requisitos;
   - los requisitos en conflicto (`A confirmar`) que afectan a alguna HU;
   - los transversales;
   - los requisitos propuestos como fuera de alcance, con motivo (se aprueban junto con las HUs);
   - preguntas abiertas que condicionan alguna HU;
   - el cierre: `Revisa las historias de usuario. Puedes editarlas directamente en el documento o pedirme cambios. Cuando estén correctas, responde "aprobar" para generar el resto del documento funcional.`
10. Antes de aprobar se puede renumerar, fusionar o dividir HUs libremente.

## Etapa 2 · Documento completo

1. Si el estado es `propuesta`, ejecuta `uv run --group se .claude/skills/se-hu-enfoque-funcional/scripts/hu_gate.py approve <doc> --by "<nombre si se conoce>"`. La aprobación exige cobertura total y congela HUs, transversales y exclusiones. Si falla, corrige el formato (sin cambiar el contenido aprobado) o pregunta.
2. La sección 2 queda congelada: no cambies títulos, actores, capacidades, finalidades ni requisitos de las HUs. Si al desarrollar el resto detectas que una HU es incorrecta o falta otra, no la toques: anótalo en el informe y propón reaprobar.
3. Redacta secciones 3–17 derivándolas de las HUs aprobadas:
   - Actores (§4) = actores de las HUs + secundarios necesarios para sus flujos.
   - Alcance incluido (§6) = capacidades de las HUs; fuera de alcance (§7) = requisitos sin HU y exclusiones explícitas.
   - Flujo principal y alternativos (§8–9): rechazo, modificación, datos no disponibles, baja confianza, permisos insuficientes, excepción de negocio.
   - Reglas `RF-<ACR>-NN` y criterios `CA-<ACR>-NN` (`Dado/Cuando/Entonces`), cada criterio asociado a una HU aprobada; mínimo 2 criterios por HU.
   - Trazabilidad (§13): la tabla 13.1 se genera con `req_coverage.py --doc <doc> --section13`; 13.2 detalla `HU` → `RQ` → `RF` → `CA`.
   - Dependencias, riesgos y métricas solo con soporte o marcadas `Propuesto`.
4. Cambia la cabecera a `Estado: borrador`.
5. Valida:
   - `uv run --group se .claude/skills/se-core/scripts/validate_doc.py <doc> .claude/skills/se-hu-enfoque-funcional/assets/spec.json`
   - `uv run --group se .claude/skills/se-hu-enfoque-funcional/scripts/hu_gate.py check <doc>`
   - `uv run --group se .claude/skills/se-core/scripts/req_coverage.py --doc <doc>`

## Cambios después de aprobar

- Si cambia el registro de requisitos (nuevo documento, respuesta del cliente), `status` mostrará huecos o exclusiones modificadas: amplía HUs y pide nueva aprobación.
- El usuario pide cambiar HUs: aplica el cambio en la sección 2, muestra `status`, pide nueva aprobación y, tras ella, ejecuta `approve` (versión +1) y revisa las secciones 3–17 afectadas.
- Los IDs aprobados no se reutilizan: una HU eliminada deja su número libre sin reasignar; una nueva toma el siguiente número.
- Si ya existen artefactos posteriores (técnico, specs, backlog), indica cuáles deben revisarse (`check_traceability.py`).

## Reglas

- No modificar `templates/`. No copiar el ejemplo de la plantilla.
- Si un diagrama no tiene información suficiente, se omite junto con su subencabezado.
- Lo abierto en preguntas no se marca como incluido: va a dependencias o a "pendiente de cierre".
- Nunca ejecutes `approve` sin aprobación explícita del usuario en la conversación.

## Checklist

- [ ] (Etapa 1) 3–8 HUs con actor de negocio y requisitos; sin solapes.
- [ ] (Etapa 1) `req_coverage.py` sin huecos; exclusiones con motivo presentadas para aprobación.
- [ ] (Etapa 1) Validador `spec-hu.json` en verde y mensaje de aprobación mostrado.
- [ ] (Etapa 2) Aprobación registrada (`hu_gate.py status` = aprobada).
- [ ] (Etapa 2) Sección 2 intacta (`hu_gate.py check` en verde).
- [ ] (Etapa 2) Cada HU con ≥ 2 CA; trazabilidad completa en §13.
- [ ] (Etapa 2) Validador `spec.json` en verde.
