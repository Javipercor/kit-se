# Política de evidencia

## Estados

| Estado | Cuándo usarlo |
| --- | --- |
| `Evidenciado` | Hay fuente citable: documento y sección/página, acta, muestra de datos o decisión del usuario. |
| `Inferido` | Deducción directa y razonable de algo evidenciado. Explica la inferencia en una frase. |
| `Propuesto` | Recomendación del equipo sin validar por el cliente. |
| `Preferente` | Opción recomendada entre varias comparadas, condicionada a confirmación. |
| `Alternativa condicionada` | Opción válida solo si se cumple una condición explícita. |
| `Dependencia crítica` | Elemento externo sin el cual no se puede construir o probar. |
| `Nueva capacidad requerida` | Algo que no existe en el cliente y hay que construir o contratar. |
| `Gobernado por plataforma` | Lo decide o provee un equipo de plataforma del cliente. |
| `A confirmar` | No hay evidencia. Genera pregunta `Q-NNN` y, si bloquea, dependencia. |
| `Ejemplo orientativo` | Ilustración, nunca decisión. |
| `No aplica` | Excluido con motivo. |

## Precedencia de fuentes

1. Decisión explícita del usuario en la conversación (regístrala como fuente: "Decisión del usuario, AAAA-MM-DD").
2. Artefactos de `proposal/` con `Estado: validado`.
3. Otros artefactos de `proposal/`.
4. Documentos del cliente en `RFP/` (los más recientes prevalecen; si se contradicen, pregunta).
5. Muestras en `data-samples/` y perfiles derivados.
6. Inferencia mínima justificada.
7. Ejemplos y buenas prácticas genéricas (siempre etiquetados).

## Cómo leer el corpus

- Fuente principal: el texto extraído en `proposal/_meta/corpus/*.txt`, con marcas `--- página N ---`.
- Las páginas listadas en `flagged_pages` de `corpus-manifest.json` (tablas, diagramas, imágenes, escaneados, presentaciones) se leen también como imagen antes de basar en ellas una afirmación. Ante discrepancia entre texto e imagen, prevalece la imagen.
- Para no saturar el contexto, abre solo las imágenes de las páginas relevantes para la tarea en curso.

## Cómo citar

- Formato: `RFP/<fichero>, §<sección>` o `RFP/<fichero>, p. <n>`; si el dato procede de una tabla o figura leída como imagen, `p. <n>, tabla` / `p. <n>, figura`. Para datos, `data-samples/<fichero>` + perfil.
- Una cita por afirmación relevante, no por párrafo entero.
- No pegues párrafos literales del cliente; resume.

## Huecos de información

- Escribe `A confirmar` en la celda o frase concreta, no en todo el documento.
- Añade la pregunta en `3-questions-for-client.md` con supuesto de trabajo y artefacto bloqueado.
- Si el hueco bloquea la entrega, añádelo a dependencias; si añade incertidumbre de coste o plazo, a riesgos.
- Nunca rellenes un hueco con un valor "típico" sin etiquetarlo como `Ejemplo orientativo`.

## Prohibido

- Nombres de sistemas, productos, campos o volúmenes no presentes en las fuentes.
- Convertir un ejemplo de la plantilla o de otro cliente en hecho.
- Marcar como incluido algo que una pregunta abierta deja sin cerrar.
