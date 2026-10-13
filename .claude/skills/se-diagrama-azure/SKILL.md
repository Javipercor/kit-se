---
name: se-diagrama-azure
description: "Kit SE (Solutions Engineering). Genera diagramas draw.io de arquitectura Azure al estilo de las arquitecturas de referencia (iconos oficiales, flujos por color, conectividad privada) a partir de una especificación JSON, para la §12 del documento técnico o el diseño de aplicación. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Diagrama de arquitectura Azure (draw.io)

Adaptación al kit de la skill `drawio-azure-reference`. Conserva sus reglas de estilo (iconos oficiales como data URI, icono y etiqueta separados, leyenda con muestras de color, un color por flujo principal, plataforma gris discontinua, saltos en los cruces), pero el diagrama se describe en datos y el script calcula la disposición: no hay que editar coordenadas en código.

## Cuándo

- §12 «Diagrama de arquitectura objetivo preferida» del documento técnico cuando la solución es Azure y conviene un `.drawio` editable además del Mermaid.
- Diagramas de despliegue o de red para la §20 o para `APP-Diseno`.

## Herramientas MCP

Ejecuta los pasos deterministas de esta skill con las herramientas del servidor MCP `se-tools` (cómo usarlas, argumentos y qué hacer si no está conectado: skill `se-herramientas`). Los comandos `uv run` que aparecen más abajo son la alternativa equivalente.

- `se_diagrama_azure`

## Workflow

1. Parte de la evidencia: componentes de §6/§14, flujos de §16, red de §20 y decisiones tecnológicas aceptadas (`proposal/_meta/decisiones.md`). No dibujes servicios que no estén en el documento técnico.
2. Escribe la especificación en `proposal/diagramas/<nombre>.json` siguiendo `references/especificacion.md` (ejemplo completo en `assets/ejemplo.json`):
   - 4–6 zonas en bandas: usuarios a la izquierda, experiencia/API, cargas de trabajo, servicios compartidos a la derecha, red abajo, observabilidad aparte.
   - 3–6 flujos principales (uno por flujo de §16 relevante) más el de plataforma implícito.
   - Etiquetas de conexión solo cuando aportan; para conexiones de plataforma repetidas usa una nota.
3. Valida: herramienta `se_diagrama_azure` con `validar: true`, o `uv run --group se .claude/skills/se-diagrama-azure/scripts/drawio_azure.py <spec> --validar`.
4. Genera: herramienta `se_diagrama_azure`, o el mismo script sin `--validar`. Salida por defecto `proposal/diagramas/<nombre>.drawio`.
5. Referencia el `.drawio` desde §12 (`Diagrama editable: proposal/diagramas/<nombre>.drawio`) sin quitar el Mermaid, que es lo que se lee en Markdown.
6. Si se pide una versión mejorada, genera un fichero nuevo; no sobrescribas el anterior.

## Iconos

`drawio_azure.py --iconos` lista los disponibles (App Service, plan, Function App, Storage, Azure OpenAI, AI Search, Document Intelligence, Cosmos DB, SQL Server, SQL Database, Key Vault, Private Endpoint, VNet, subred, DNS privado, Application Insights, Log Analytics). Si falta un servicio, añade su SVG oficial a `assets/icons/` y la entrada a `ICON_FILES`; mientras tanto, usa un nodo sin icono (caja de texto).
