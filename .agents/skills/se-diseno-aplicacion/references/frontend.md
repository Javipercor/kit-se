# Referencia frontend y canal (orientativa)

| Situación | Opción habitual | Notas |
| --- | --- | --- |
| SPA de negocio | React + TypeScript (Vite) o Angular | Angular frecuente en entornos corporativos; elegir por estándar del cliente |
| Equipo .NET full-stack | Blazor | Valorar requisitos de UX y rendimiento |
| Embebido en CRM/colaboración | Componente del host (p. ej. extensión, app, componente web) | Contrato de payload e identidad con el host `A confirmar` |
| Interfaz conversacional | Widget de chat o canal existente | Estados: escribiendo, propuesta, confirmación, error, degradado |
| Herramienta interna de datos | Streamlit / Dash / Panel | Solo para usuarios internos o PoC |

## Estados de UI obligatorios por pantalla/interacción

Carga, vacío, error recuperable, error de permisos, datos desactualizados (con fecha de frescura), confirmación antes de acción con impacto, resultado de la acción.

## Pruebas

Unitarias de componentes, E2E (Playwright) para flujos críticos, accesibilidad (WCAG 2.1 AA como referencia `A confirmar`).
