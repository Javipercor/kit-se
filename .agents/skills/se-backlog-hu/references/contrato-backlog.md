# Contrato de `proposal/6.0-backlog.md`

## Reglas globales

- Sin tablas, sin bloques de código, sin comentarios HTML, sin texto meta ni cabecera de control.
- Solo estos H2, en este orden: `## Catálogo preliminar de épicas y HUs`, `## Backlog detallado`, `## Resumen de esfuerzo (control de consistencia)`.
- Primera línea exacta: `# Backlog técnico-funcional`.
- Numeración correlativa: `EPIC 1..N`, `HU X.1..X.M` dentro de la EPIC X.
- EPIC 1 `Arquitectura`; penúltima `DevOps`; última `Documentacion y Entregables`. Si una no tiene trabajo defendible: una única HU `No aplica` con una línea de motivo.

## Catálogo

```text
# Backlog técnico-funcional

## Catálogo preliminar de épicas y HUs

### EPIC 1 - Arquitectura

#### HU 1.1 - Definición de arquitectura objetivo y contratos

Como Responsable de negocio del caso de uso, quiero disponer de una arquitectura validada, para asegurar que la solución es viable, segura y operable.

* **Fase única - Implementación del caso de uso**
```

## Detalle

```text
## Backlog detallado

### EPIC 2 - <Título>

#### HU 2.1 - <Título>

Como <rol de negocio>, quiero <capacidad>, para <valor>.

* **Fase única - Implementación del caso de uso**

##### Enfoque técnico

<1–4 líneas: componentes, flujos (§16.x), contratos, trazas HU-<ACR>-NN / F-NNN.>

##### Criterios de aceptación

* <criterio verificable>
* <criterio verificable>
* <criterio verificable>

##### Dependencias

* <dependencia real con referencia>

##### Tareas

* **Backend**
  * Implementar operación `proposal.create` con idempotencia y errores normalizados **8h, N2**
* **QA**
  * Pruebas de contrato y de integración de `proposal.create` **4h, N1**
```

- Subsecciones permitidas y en este orden: `Enfoque técnico` (opcional), `Criterios de aceptación` (obligatoria, 3–7 bullets), `Dependencias` (opcional, solo si hay), `Tareas` (obligatoria).
- Roles de tarea: los de `se.config.json` → `backlog.roles` (por defecto `Architect`, `Backend`, `Frontend`, `DS`, `DataEng`, `DevOps`, `UI/UX`, `QA`).
- Tareas `DevOps` solo dentro de la EPIC `DevOps`.
- Cada tarea termina en `**<1-16>h, N<1-4>**`; descripción con verbo y entregable observable.

## Resumen

Generado por `effort_summary.py`:

```text
## Resumen de esfuerzo (control de consistencia)

### Total global

* **Total: 312h**
* Architect: 40h

### Horas por épica, HU y rol

* **EPIC 1 - Arquitectura: 40h**
  * HU 1.1 - Definición de arquitectura objetivo y contratos: 40h (Architect 32h, DataEng 8h)
```
