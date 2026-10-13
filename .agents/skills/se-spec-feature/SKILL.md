---
name: se-spec-feature
description: "Kit SE (Solutions Engineering). Define features y especificaciones implementables (spec-driven development) a partir de HUs funcionales y del diseño técnico, de datos, IA y aplicación - índice de features F-NNN y un spec.md por feature con comportamiento, criterios Dado/Cuando/Entonces, contratos API/datos/eventos, requisitos de IA, NFR, telemetría, casos límite y Definition of Ready. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Spec de feature

## Salidas

- `proposal/specs/README.md`: índice de features (plantilla `assets/index.md`).
- `proposal/specs/F-NNN-<slug>/spec.md`: una por feature (plantilla `assets/spec.md`).
- `proposal/checklists/se-spec-feature.md`.

## Workflow

1. Lee funcional (HUs, reglas, CA), técnico (flujos §16, contratos §22, CAT §26), aplicación (módulos, API) y, si existen, datos y la sección 29 del técnico (IA y ciencia de datos).
2. Deriva features: capacidad entregable y demostrable de forma independiente, tamaño de 1–3 sprints. Separa features habilitadoras (ingesta de una fuente, evaluación IA, identidad) de las de usuario.
3. Escribe el índice con orden de implementación por dependencias. Si se pide modo gate (`indice`), detente aquí.
4. Para cada feature, rellena la plantilla:
   - Comportamiento como reglas numeradas sin ambigüedad.
   - Criterios `AC-FNNN-NN` en formato `Dado ..., cuando ..., entonces ...`, incluyendo errores, permisos y degradación.
   - Contratos concretos referenciando el técnico/aplicación; campos nuevos se marcan `Propuesto`.
   - Requisitos de IA si aplica: entradas, salida estructurada, prompts/versiones, dataset de evaluación, umbrales, guardrails, comportamiento con baja confianza.
   - NFR medibles y telemetría (eventos y métricas).
   - Definition of Ready: lista de verificación; si hay bloqueantes, `Estado: bloqueada`.
5. Valida: `uv run --group se .agents/skills/se-spec-feature/scripts/validate_spec.py`.

## Reglas

- Nada de alcance nuevo: lo no soportado va a "Preguntas abiertas".
- Cada spec traza a `HU-<ACR>-NN`, `RQ-NNN` y secciones del técnico.
- Las specs deben ser útiles para un agente de código: rutas, nombres de operaciones, esquemas y criterios verificables; sin prosa decorativa.

## Checklist

- [ ] Índice con dependencias y orden.
- [ ] Todas las HUs funcionales cubiertas por al menos una feature.
- [ ] Cada spec con ≥ 3 AC, contratos, NFR y DoR.
- [ ] Validador en verde.
