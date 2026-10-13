# Consolidación de requisitos

Objetivo: un requisito por necesidad real, sin perder detalle ni origen, agrupado en capacidades de negocio de las que salen las HUs.

## 1. Forma canónica al extraer

Cada hallazgo se registra como: **actor** (quién lo necesita), **acción** (verbo), **objeto** (entidad de negocio), **condición** (frecuencia, valor, regla, restricción) y **texto** normalizado.

- Atómico: un verbo y un resultado verificable. "Consultar y exportar" son dos hallazgos.
- Objeto con el vocabulario del negocio y siempre igual: si el pliego dice "cartera", "clientes asignados" y "clientes del gestor", elige uno y úsalo en todos los hallazgos. La agrupación depende de ello.
- Valores explícitos en la condición (99,5 %, 24 h, 5 años).
- Durante el barrido no se deduplica: si se repite, se registra otra vez.

## 2. Agrupar

`req_dedupe.py groups` compara los hallazgos sin consolidar entre sí y contra los requisitos existentes, dentro de la misma categoría. Las pistas por par son orientativas; la decisión es tuya.

## 3. Decidir la relación de cada grupo

| Relación | Cuándo | Qué hacer en el registro |
| --- | --- | --- |
| `duplicado` | Mismo actor, acción, objeto y condición con distinta redacción | Un único RQ con todos los hallazgos |
| `refinamiento` | Uno añade precisión al otro (criterio, valor, alcance) | Un RQ con la redacción más específica; lo añadido va a `detalles` |
| `complementario` | Mismo objeto o capacidad, aspectos distintos (generar / exportar) | RQ separados, misma capacidad |
| `conflicto` | Valores o reglas incompatibles | RQ separados en `A confirmar`, pregunta `Q-NNN` en `3-questions-for-client.md` |
| `distinto` | Parecido solo en las palabras | RQ separados |
| `mixto` | El grupo combina varias relaciones | Detállalo en `motivo` |

Anótalo en `decisiones`: `{"grupo": "G-…", "relacion": "…", "motivo": "…", "pregunta": "Q-NNN"}`. `motivo` es obligatorio salvo en `duplicado`.

Reglas:
- No fusiones requisitos de actores distintos ni con valores distintos (eso es conflicto).
- Ante la duda entre `duplicado` y `refinamiento`, elige `refinamiento`: conserva el detalle.
- Si un hallazgo nuevo coincide con un RQ existente, asígnalo a ese RQ; no crees uno nuevo.
- Revisa también la lista "sin similares": en modo léxico no se detectan paráfrasis con objetos redactados distinto (con embeddings sí, en buena parte). Si ves dos equivalentes, unifica su objeto y vuelve a ejecutar `groups`.
- No renumeres nunca.

## 4. Capacidades

Una capacidad es algo que el negocio hace con la solución: verbo + objeto en lenguaje de negocio ("Planificar visitas", "Gestionar descartes"). No es un módulo técnico ni una pantalla.

- Todo requisito funcional pertenece a una capacidad (`"capacidad": "CAP-NN"`).
- Los técnicos pertenecen a la capacidad a la que afectan o son `TRANSVERSAL` si aplican a toda la solución.
- Cada capacidad tiene al menos un requisito funcional. "Seguridad" o "Rendimiento" no son capacidades: son transversales.
- Tamaño orientativo: 2–8 requisitos. Más indica que mezcla capacidades; uno solo y trivial indica que debe integrarse en otra.
- Proyectos típicos: 4–12 capacidades.

De las capacidades salen las HUs: normalmente una HU por capacidad, o varias si hay actores o resultados distintos. Una HU no debería mezclar más de dos capacidades (`req_coverage.py` lo avisa).

## 5. Validación

`req_scan.py check` (incluye `req_dedupe.py lint`) falla si:
- hay hallazgos sin pasar por la agrupación o grupos sin decisión;
- la decisión contradice el registro (p. ej., `duplicado` repartido en dos RQ, `conflicto` fusionado);
- un conflicto no tiene pregunta o sus RQ no están `A confirmar`;
- dos RQ son casi idénticos sin decisión que lo justifique;
- un requisito funcional no tiene capacidad o una capacidad no tiene requisitos funcionales.
