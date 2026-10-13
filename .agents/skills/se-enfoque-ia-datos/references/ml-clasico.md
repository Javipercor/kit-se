# ML clásico, forecasting y optimización

## Selección orientativa

| Problema | Baseline obligatorio | Candidatos habituales | Validación |
| --- | --- | --- | --- |
| Clasificación / scoring | Regla de negocio o clase mayoritaria; regresión logística | Gradient boosting (LightGBM, XGBoost, CatBoost), RF | Estratificada; temporal si hay deriva |
| Regresión | Media/mediana por segmento | Gradient boosting, GLM | Temporal si hay tiempo |
| Forecasting | Naive, estacional naive, media móvil | ETS/ARIMA, modelos globales con boosting, Prophet-like, modelos neuronales si hay muchas series | Backtesting con ventanas deslizantes |
| Segmentación | Reglas RFM o de negocio | K-means, clustering jerárquico, GMM | Estabilidad + interpretabilidad negocio |
| Anomalías | Umbrales estadísticos | Isolation Forest, modelos de densidad | Revisión con expertos, tasa de alertas |
| Recomendación / priorización | Popularidad, reglas | Ranking supervisado, filtrado colaborativo | Métricas de ranking + test A/B |
| Optimización / planificación | Heurística greedy | Programación lineal/entera, CP-SAT | Factibilidad y gap vs óptimo |

## Riesgos típicos

- Fuga de información: variables posteriores al momento de decisión, agregados calculados con el futuro.
- Desbalanceo: usa métricas adecuadas (PR-AUC, recall@k) y calibración.
- Deriva: define monitorización de datos y de rendimiento y criterio de reentrenamiento.
- Explicabilidad: SHAP o importancia por permutación cuando la decisión afecta a personas o requiere justificación.

## Stack habitual (orientativo)

Python: `pandas`/`polars`, `scikit-learn`, boosting, `statsmodels`, `optuna`, `MLflow` u otro registro de experimentos, paquetes en lugar de notebooks para producción. Consumo desde .NET: servicio de inferencia vía API, ONNX o `ML.NET` si el cliente lo exige.
