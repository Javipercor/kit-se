# Evaluación y gates

## Métricas por tipo

| Tipo | Técnicas | Negocio |
| --- | --- | --- |
| Clasificación | PR-AUC, ROC-AUC, recall/precisión @umbral, calibración | Coste de errores, % casos automatizados |
| Regresión / forecasting | MAE, RMSE, MAPE/sMAPE, WAPE, sesgo | Error en unidades de negocio, roturas/excesos |
| Ranking / recomendación | NDCG@k, recall@k, cobertura | Conversión, aceptación de propuestas |
| RAG | Recall de recuperación, groundedness, relevancia, completitud, tasa de abstención correcta | Resolución sin escalado, tiempo ahorrado |
| Agentes | Éxito de tarea, uso correcto de tools, nº pasos, errores de tool, acciones bloqueadas correctamente | Aceptación de propuestas, retrabajo |
| Seguridad | Tasa de jailbreak/injection resistida, fugas de PII | Incidentes |
| Operación | Latencia p50/p95, coste por ejecución, tokens | Coste por caso resuelto |

## Dataset de evaluación

- Construido con el cliente: casos reales anonimizados + casos límite + casos adversarios.
- Con salida esperada o criterios de corrección; versionado.
- Tamaño mínimo orientativo para PoC: 50–200 casos por intención principal (`A confirmar` según dominio).

## Gates de promoción

- PoC → piloto: métricas sobre baseline con margen acordado, sin bloqueantes de seguridad.
- Piloto → producción: métricas online, aceptación de usuarios, coste dentro de presupuesto, monitorización operativa.
- Cada cambio de modelo, prompt, tool o reglas pasa la suite de evaluación en CI antes de promover.

## Monitorización

Deriva de datos y de predicción, rendimiento con etiqueta diferida, feedback de usuario, coste y latencia, alertas con umbral y responsable.
