---
name: se-diseno-aplicacion
description: "Kit SE (Solutions Engineering). Diseño de aplicación implementable para backend, frontend y servicios en Python (FastAPI, Pydantic, SQLAlchemy) o .NET (ASP.NET Core, EF Core): decisión de stack con ADRs, módulos, contratos API/OpenAPI, persistencia, frontend o canal embebido, transversales (identidad, errores, logging, configuración), estrategia de pruebas, arquetipo de repositorios y pipeline. Úsala solo dentro del kit SE: comandos /se-*, agentes se-* o cuando el usuario pida expresamente el kit SE."
---

# Diseño de aplicación (Python / .NET)

## Salida

`proposal/APP-Diseno-<slug>.md` (plantilla `assets/template.md`) y `proposal/checklists/se-diseno-aplicacion.md`.

## Referencias (lee solo las del stack aplicable)

- `references/python.md` · `references/dotnet.md` · `references/frontend.md` · `references/api-contratos.md`

## Workflow

0. Decisiones y preferencias: lee `proposal/_meta/decisiones.md` y `uv run --group se .claude/skills/se-core/scripts/preferencias.py listar`. Cada ADR corresponde a una decisión registrada con `decisiones.py registrar --area tecnologia|arquitectura --ambito … --valor …` y la cita (`D-NNN`); si se aparta de una preferencia, lo dice y lleva `--preferencia` o `--excepcion-de`.

1. Lee el documento técnico (componentes §14, contratos §22, interfaces §23) y, si existen, datos e IA.
2. Stack: evidenciado, decidido por el usuario o comparado en `ADR-01`. Criterios: estándar del cliente, skills del equipo, peso del componente de datos/IA (favorece Python), integración con ecosistema Microsoft/empresarial existente (favorece .NET), plataforma de despliegue, soporte LTS. Arquitectura mixta válida: servicios de dominio en .NET y servicios de IA/datos en Python con contrato API.
3. Módulos: por dominio (vertical slices / bounded contexts). Monolito modular por defecto; servicios separados solo con razón (escalado distinto, stack distinto, equipo distinto, aislamiento de seguridad).
4. Contratos API: por operación, siguiendo `references/api-contratos.md`. Coherentes con §22 del técnico.
5. Persistencia: entidades, propiedad de datos por módulo, migraciones, idempotencia, auditoría. Parte de los almacenes, tecnologías y políticas de §22.5 del documento técnico: aquí se baja a modelo de datos de la aplicación, sin redefinirlos.
6. Frontend/canal: tipo (SPA, server-side, embebido en host, chat), pantallas o interacciones derivadas de las HUs, estados (carga, vacío, error, degradado, confirmación).
7. Transversales, pruebas (pirámide + contract tests + evaluación IA si aplica), arquetipo de repos y pipeline.
8. Valida: `uv run --group se .claude/skills/se-core/scripts/validate_doc.py <salida> .claude/skills/se-diseno-aplicacion/assets/spec.json`.

## Reglas

- No dupliques el técnico; refina hasta nivel implementable y cita sus secciones.
- Versiones: LTS/soportadas; marca `A confirmar` si el cliente tiene estándares propios.
- No impongas librerías no estándar sin ADR.

## Checklist

- [ ] ADR de stack con opciones y condición.
- [ ] Cada HU tiene módulo responsable y operaciones API asociadas.
- [ ] Contratos con errores normalizados, idempotencia y autorización.
- [ ] Estrategia de pruebas incluye contract tests y, si aplica, evaluación IA.
- [ ] Validador en verde.
