# Especificación del diagrama

```json
{
  "nombre": "arquitectura-objetivo",
  "titulo": "Título visible de la página",
  "zonas": [
    {"id": "app", "titulo": "Experiencia y API", "columna": 1, "fila": 0, "ancho": 1, "alto": 1, "color": "azul"}
  ],
  "nodos": [
    {"id": "api", "etiqueta": "API\nFunction App", "icono": "function_app", "zona": "app"},
    {"id": "usuarios", "etiqueta": "Usuarios", "zona": "cliente"}
  ],
  "notas": [
    {"id": "n1", "texto": "Todas las Function Apps usan:\n- VNet integration\n- Key Vault", "zona": "app"}
  ],
  "flujos": [
    {"id": "ingesta", "etiqueta": "Flujo de ingesta", "color": "#0078D4"}
  ],
  "conexiones": [
    {"de": "usuarios", "a": "api", "flujo": "ingesta", "etiqueta": "HTTPS", "discontinua": false}
  ]
}
```

| Campo | Reglas |
| --- | --- |
| `zonas` | Rejilla: `columna` y `fila` desde 0; `ancho`/`alto` en celdas (por defecto 1). La altura crece sola si no caben los nodos. Colores: `naranja`, `azul`, `verde`, `morado`, `amarillo`, `gris`, `blanco` |
| `nodos` | `icono` opcional (sin icono es una caja de texto, útil para actores). `\n` separa líneas de la etiqueta. Se colocan en orden dentro de su zona |
| `notas` | Texto en caja discontinua; sirven como origen de conexiones de plataforma agrupadas |
| `flujos` | Máximo 7. Color opcional; si no, se asigna de la paleta. El flujo `plataforma` existe siempre (gris, discontinuo) |
| `conexiones` | `flujo` por defecto `plataforma`. `discontinua` por defecto solo en plataforma |

La leyenda se genera sola a partir de `flujos`. Orden recomendado de columnas: 0 usuarios · 1 experiencia/API · 2 cargas de trabajo · 3 servicios compartidos; fila 1 para red y observabilidad.
