# Referencia Python (orientativa)

| Aspecto | Opción por defecto | Alternativas / notas |
| --- | --- | --- |
| Versión | Python soportado más reciente adoptado por el cliente (3.12+) | Ajustar a estándar del cliente |
| Gestión de dependencias | `uv` con `pyproject.toml` y lockfile | Poetry, pip-tools |
| API | FastAPI + Pydantic v2 | Litestar; Django REST si hay backoffice/ORM Django |
| Persistencia | SQLAlchemy 2 (async si I/O intensivo) + Alembic | SQLModel; drivers nativos para NoSQL |
| Tareas asíncronas | Workers con cola (Celery, Arq, Dramatiq) o funciones serverless | Orquestadores de datos (Airflow, Dagster, Prefect) para pipelines |
| Datos / DS | pandas o polars, scikit-learn, MLflow | DuckDB para análisis local |
| Calidad de código | ruff (lint + format), mypy o pyright | pre-commit |
| Pruebas | pytest, pytest-asyncio, httpx TestClient, testcontainers | schemathesis para contract testing de OpenAPI |
| Configuración | pydantic-settings, variables de entorno, secretos desde gestor de secretos | |
| Observabilidad | OpenTelemetry (trazas, métricas), logging estructurado (structlog o logging JSON) | |
| Empaquetado | Imagen de contenedor slim, usuario no root, healthchecks | |

## Estructura de servicio

```text
service/
├── pyproject.toml
├── src/<paquete>/
│   ├── api/          # routers, dependencias, esquemas de request/response
│   ├── domain/       # modelos y reglas de negocio puras
│   ├── services/     # casos de uso
│   ├── adapters/     # repositorios, clientes de APIs externas, tools
│   ├── ai/           # prompts versionados, cadenas/agentes, evaluadores (si aplica)
│   └── settings.py
├── tests/{unit,integration,contract,eval}
└── Dockerfile
```

## Horquillas orientativas de esfuerzo

Ver `se-backlog-hu/references/catalogo-tareas.md`.
