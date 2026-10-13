# Referencia .NET (orientativa)

| Aspecto | Opción por defecto | Alternativas / notas |
| --- | --- | --- |
| Versión | .NET LTS vigente adoptado por el cliente | Ajustar a estándar del cliente |
| API | ASP.NET Core Minimal APIs o Controllers | gRPC para comunicación interna de alto rendimiento |
| Arquitectura | Vertical slices o Clean Architecture ligera | Evitar capas vacías; MediatR solo si aporta |
| Persistencia | EF Core + migraciones | Dapper para lectura intensiva |
| Validación | Validación de modelo / FluentValidation | |
| Tareas en segundo plano | `BackgroundService`, colas del proveedor cloud, Hangfire | Durable Functions / workflows gestionados |
| IA | `Microsoft.Extensions.AI`, Microsoft Agent Framework / Semantic Kernel | Llamar a servicios Python de IA vía API cuando el componente de ML viva en Python |
| Pruebas | xUnit, `WebApplicationFactory`, Testcontainers, NSubstitute/Moq | Pact o pruebas de contrato OpenAPI |
| Calidad | Analizadores Roslyn, `dotnet format`, `TreatWarningsAsErrors` en CI | |
| Configuración | `IOptions`, User Secrets en local, gestor de secretos en entornos | |
| Observabilidad | OpenTelemetry, logging estructurado (`ILogger` + Serilog opcional) | .NET Aspire para orquestación local y dashboard |
| Empaquetado | Imagen de contenedor, usuario no root, healthchecks `/health` | |

## Estructura de solución

```text
src/
├── <Producto>.Api/            # endpoints, auth, OpenAPI
├── <Producto>.Application/    # casos de uso por feature (vertical slices)
├── <Producto>.Domain/         # entidades y reglas
├── <Producto>.Infrastructure/ # EF Core, clientes externos, tools
tests/
├── <Producto>.UnitTests/
├── <Producto>.IntegrationTests/
└── <Producto>.ContractTests/
```
