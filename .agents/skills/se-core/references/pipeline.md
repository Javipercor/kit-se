# Pipeline de diseño

```mermaid
flowchart LR
    C[0 Corpus] --> F[1 Funcional]
    C --> D[2 Fuentes de datos]
    F --> D
    D --> IA[3 IA / DS · §29 del técnico]
    F --> T[4 Técnico]
    D --> T
    IA --> T
    T --> A[5 Aplicación]
    F --> S[6 Specs]
    T --> S
    A --> S
    S --> B[7 Backlog]
    F --> B
    T --> B
```

## Dependencias mínimas por fase

| Fase | Requiere | Opcional |
| --- | --- | --- |
| 1 Funcional | Corpus o descripción del usuario | Matriz, preguntas |
| 2 Datos | Corpus o funcional | Muestras |
| 3 IA/DS (sección 29 del documento técnico) | Funcional | Datos |
| 4 Técnico | Funcional | Datos, IA |
| 5 Aplicación | Técnico | Restricciones de stack |
| 6 Specs | Funcional + técnico | Aplicación, datos, IA |
| 7 Backlog | Funcional + técnico | Specs, datos, IA, aplicación |

## Estado del pipeline

`proposal/_meta/se-pipeline-state.md` contiene una tabla `Fase | Aplica | Estado | Artefacto | Última actualización | Notas` con estados `pendiente`, `en curso`, `borrador`, `en revisión`, `validado`, `bloqueado`, `no aplica`.

## Propagación de cambios

Cuando cambia un artefacto validado aguas arriba:
1. Ejecuta `check_traceability.py`.
2. Marca como `en revisión` los artefactos aguas abajo afectados.
3. Lista en el estado qué IDs cambiaron y qué documentos los consumen.
