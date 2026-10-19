# AI Bike Fit

Documentación base para desarrollar una plataforma de análisis biomecánico de ciclismo a partir de vídeo.

La especificación técnica y el plan de implementación están en [docs/AI-BIKE-FIT-DEVELOPMENT.md](docs/AI-BIKE-FIT-DEVELOPMENT.md).

## Alcance actual

El MVP analiza un vídeo lateral de 30-60 segundos de un ciclista pedaleando en rodillo, calcula métricas biomecánicas con MediaPipe Pose, aplica reglas expertas y genera un informe explicativo.

## Principios

- El sistema ofrece orientación de ajuste, no diagnóstico médico.
- Toda recomendación debe mostrar evidencia, confianza y limitaciones.
- Las reglas biomecánicas son la fuente de decisión del MVP; el LLM solo redacta el informe.
- Los resultados deben ser reproducibles a partir del vídeo y la configuración registrada.
