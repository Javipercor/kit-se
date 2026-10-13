---
name: se-hu-enfoque-tecnico
description: "Kit SE (Solutions Engineering). Genera o revisa el documento HU-Enfoque-Técnico-&-Arquitectura de un caso de uso (28 secciones más la 29 de IA y ciencia de datos: contexto, cobertura técnica, arquitectura objetivo basada en evidencia, componentes y madurez, dominios de datos, decisiones pendientes, NFR, opciones comparadas, flujos técnicos con mermaid, integraciones, seguridad, red, entornos, contratos, persistencia de datos, evaluación, observabilidad, DevOps, criterios técnicos, dependencias y riesgos). Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# HU Enfoque Técnico Y Arquitectura

Compatible con la estructura de la skill `rfp-hu-enfoque-tecnico-arquitectura` (secciones 1–28 sin cambios de numeración; la 29 se añade al final); si esa skill está instalada, prevalece y esta actúa como complemento para proyectos de datos, IA y Python/.NET.

## Entradas

Obligatorio `HU-Enfoque-Funcional-*.md`. Recomendado: `DATA-Analisis-Fuentes-*.md`, sección 29 ya redactada por `se-enfoque-ia-datos`, matriz, preguntas, corpus. Plantilla del cliente en `templates/` si existe; si no, `assets/template.md`.

## Salida

`proposal/HU-Enfoque-Tecnico-&-Arquitectura-<slug>.md` y `proposal/checklists/se-hu-enfoque-tecnico.md`.

## Workflow

0. Decisiones y preferencias: lee `proposal/_meta/decisiones.md` y `uv run --group se .claude/skills/se-core/scripts/preferencias.py listar`. Las decisiones `aceptada` y las preferencias `obligatoria`/`prohibida` son restricciones de diseño; registra cada elección tecnológica o de arquitectura con `decisiones.py registrar` y cita su `D-NNN` (ver `se-core/references/decisiones.md`).

1. Inventaría evidencia: canal, identidad, plataforma, runtime, fuentes, restricciones de stack y red. Busca en el corpus los términos de `references/guia-secciones.md` §Búsqueda.
2. Normaliza sistemas en categorías: canal, identidad, gateway, runtime, orquestación, dominio, tools/adaptadores, fuentes transaccionales, analíticas/batch, reglas/configuración, estado operacional, SaaS, almacenamiento, observabilidad, DevOps.
3. Marca cada decisión con su estado. Sin evidencia: `Propuesto`/`A confirmar` y entrada en dependencias.
4. Redacta las 28 secciones siguiendo `references/guia-secciones.md`. Las secciones 3–12 son la capa ejecutiva; 13–28 el cuerpo técnico. La 29 (IA y ciencia de datos) la redacta `se-enfoque-ia-datos`; no la reescribas.
5. Cada flujo de la sección 16: un `mermaid flowchart LR` y una tabla de pasos con red, seguridad y autenticación.
6. Opciones comparadas (§11): una subsección por cada decisión técnica abierta y relevante de este proyecto, sacadas de §9, de las propuestas pendientes del registro de decisiones y de las desviaciones de preferencias; no uses un catálogo fijo. Cada opción elegida cita su `D-NNN`.
7. Persistencia (§22.5): inventaría los almacenes propios de la solución (transaccional, documental, caché, vectorial, ficheros, eventos, analítico, estado de sesión, auditoría) con tecnología, propietario, volumen, consistencia, retención, backup/RPO/RTO, cifrado y residencia. Cada tecnología de almacenamiento es una decisión registrada (ámbitos `bbdd-*` o `almacenamiento`) que respeta las preferencias.
8. Integra datos e IA: fuentes `SRC-NN` del documento de datos en §8 y §22.4; componentes, flujos, evaluación y LLMOps de la sección 29 en §6, §14, §16 y §23.4, remitiendo a 29.x sin duplicar.
9. Si la solución es Azure, genera además el diagrama editable de §12 con la skill `se-diagrama-azure` (`se_diagrama_azure`) y referencia el `.drawio` junto al Mermaid.
10. §23.2 y §23.4 solo aplican con agentes o IA; si no, `No aplica: <motivo>`.
11. Valida: `uv run --group se .claude/skills/se-core/scripts/validate_doc.py <salida> .claude/skills/se-hu-enfoque-tecnico/assets/spec.json`.

## Guardrails de arquitectura

- Separar razonamiento, autorización, acceso a datos, ejecución y auditoría.
- Componentes LLM sin permisos de escritura directos sobre sistemas de negocio salvo patrón aprobado.
- Autorización por usuario, rol, objetivo, scope, operación y recurso en una capa de gobierno cuando exista.
- Escrituras con confirmación explícita, snapshot vigente y clave de idempotencia.
- Fuentes batch con frescura visible y degradación explícita.
- Prompts, reglas, tools, contratos y evaluaciones versionados y con gate de promoción.
- Entornos productivos: validar conectividad, DNS, accesos y ausencia de exposición no deseada. Documentar diferencias de `DEV`.

## No asumir por defecto

Canal concreto, sistemas fuente concretos, destino de ingesta batch, gateway/runtime/framework de agentes/store/observabilidad, patrón de identidad (OBO, app-only, managed identity...), ni stack Python vs .NET. Todo ello solo con evidencia o decisión del usuario.

## Checklist

- [ ] 29 secciones numeradas en orden (la 29 redactada por `se-enfoque-ia-datos` o `No aplica: <motivo>`); referencias cruzadas actualizadas.
- [ ] §2 mapea cada resultado funcional a cobertura técnica y estado.
- [ ] §4 y §6 usan la taxonomía de estados.
- [ ] §11 compara opciones sin convertir ejemplos en decisiones.
- [ ] §16 cada flujo con diagrama y tabla; escrituras con confirmación e idempotencia.
- [ ] §17 traza todas las reglas funcionales.
- [ ] §26 criterios `CAT-NN` en formato Dado/Cuando/Entonces.
- [ ] §27–28 recogen todos los `A confirmar` bloqueantes y riesgos.
- [ ] Validador en verde.
