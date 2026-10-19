# AI Bike Fit: documentación de desarrollo

## 1. Resumen

AI Bike Fit es una plataforma de análisis biomecánico para ciclismo que transforma un vídeo lateral grabado con un teléfono móvil en recomendaciones concretas de configuración de la bicicleta.

El MVP no intenta sustituir a un especialista ni emitir diagnósticos clínicos. Su objetivo es detectar patrones de posición observables, explicar la evidencia utilizada y proponer ajustes pequeños, priorizados y revisables.

## 2. Objetivos y límites

### Objetivos del MVP

- Analizar un vídeo lateral de 30-60 segundos.
- Verificar automáticamente si el vídeo es suficientemente válido.
- Detectar la pose del ciclista y seguirla durante varios ciclos de pedalada.
- Calcular métricas angulares y de estabilidad.
- Aplicar reglas biomecánicas versionadas.
- Generar recomendaciones con evidencia y nivel de confianza.
- Presentar un informe visual que permita revisar el razonamiento.

### Fuera de alcance inicial

- Análisis frontal, posterior o multicámara.
- Diagnóstico de lesiones o patología.
- Recomendaciones basadas exclusivamente en un LLM.
- Detección completa de componentes de cualquier bicicleta.
- Sustitución del criterio de un bike fitter.
- Modelo predictivo entrenado antes de disponer de datos etiquetados de calidad.

## 3. Usuario y flujo principal

1. El usuario crea un análisis y acepta las condiciones de uso.
2. Sube un vídeo lateral del ciclista en un rodillo.
3. El sistema valida duración, orientación, visibilidad, iluminación y calidad de pose.
4. El usuario confirma el lado analizado y, si procede, la configuración básica de la bicicleta.
5. El backend procesa el vídeo de forma asíncrona.
6. El usuario consulta el estado del análisis.
7. La aplicación muestra métricas, diagnósticos, capturas clave y recomendaciones.
8. El usuario puede descargar o compartir el informe.
9. Más adelante podrá registrar el ajuste aplicado y repetir el análisis.

## 4. Arquitectura propuesta

```text
[Next.js]
    |
    | HTTPS/JSON + carga de vídeo
    v
[FastAPI]
    |-- Autenticación y análisis
    |-- Validación de entrada
    |-- Orquestación de jobs
    |
    +--> [Object Storage: vídeo y capturas]
    +--> [Worker de procesamiento]
              |-- extracción de frames
              |-- MediaPipe Pose
              |-- normalización temporal
              |-- cálculo de métricas
              |-- motor experto
              |-- generación de evidencias
    |
    +--> [PostgreSQL: metadatos y resultados]
    +--> [LLM: redacción controlada del informe]
```

### Decisiones de arquitectura

- El procesamiento de vídeo será asíncrono; la petición de subida no debe esperar a terminar el análisis.
- Los vídeos y las imágenes derivadas vivirán en almacenamiento de objetos. PostgreSQL guardará metadatos, métricas y resultados, no blobs grandes.
- MediaPipe Pose será determinista dentro de la versión fijada del pipeline. La versión del modelo y sus parámetros deben persistirse con cada análisis.
- El motor experto producirá diagnósticos estructurados antes de invocar al LLM.
- El LLM recibirá únicamente datos estructurados y deberá devolver texto validado. No podrá crear diagnósticos ni cambiar umbrales.
- Todas las reglas tendrán versión para poder reproducir informes históricos.

## 5. Componentes del sistema

### 5.1 Frontend: Next.js

Pantallas del MVP:

- Inicio / creación de análisis.
- Guía de grabación con requisitos visibles.
- Subida y validación del vídeo.
- Estado del procesamiento.
- Informe de resultados.
- Historial básico de análisis.

Responsabilidades:

- Validar tamaño y formato antes de subir cuando sea posible.
- Mostrar errores accionables, no solo códigos técnicos.
- Representar estados `draft`, `uploading`, `queued`, `processing`, `completed` y `failed`.
- Mostrar que la recomendación es orientativa y que la confianza expresa la evidencia del vídeo, no certeza clínica.

### 5.2 Backend: FastAPI

Módulos sugeridos:

```text
app/
  api/              # rutas HTTP
  domain/           # entidades y reglas de negocio
  processing/       # vídeo, pose y métricas
  expert_engine/    # reglas, diagnósticos y confianza
  reports/          # DTOs e integración con LLM
  persistence/      # SQLAlchemy/repositories
  workers/          # jobs asíncronos
  config/           # configuración y versionado
```

El backend debe separar la lógica de dominio del framework HTTP para poder ejecutar reglas y métricas desde tests sin levantar la API.

### 5.3 Procesamiento de vídeo

Pipeline:

1. Descargar o abrir el objeto de vídeo.
2. Extraer metadatos: duración, FPS, resolución, orientación y códec.
3. Muestrear frames a una frecuencia configurable.
4. Ejecutar MediaPipe Pose.
5. Rechazar o marcar frames con visibilidad insuficiente.
6. Suavizar coordenadas y eliminar outliers sin ocultar la calidad original.
7. Identificar ciclos de pedalada mediante la trayectoria de una articulación del pie o tobillo.
8. Normalizar cada ciclo a 0-100% de la pedalada.
9. Calcular métricas por ciclo y agregarlas con mediana, percentiles y dispersión.
10. Seleccionar capturas representativas.
11. Ejecutar el motor experto.
12. Persistir resultados y dejar el informe listo para consulta.

La salida debe conservar métricas de calidad: porcentaje de frames válidos, frames descartados, ciclos utilizables y estabilidad de la detección.

## 6. Requisitos de grabación

El producto debe pedir al usuario:

- Cámara fija, perpendicular al plano de la bicicleta.
- Bicicleta completa dentro del encuadre.
- Ciclista visible de cabeza a pies y sin prendas que oculten las articulaciones.
- Iluminación uniforme y fondo con contraste suficiente.
- Rodillo estable y cadencia constante durante varios segundos.
- Vídeo de 30-60 segundos, preferiblemente sin zoom ni cambios de cámara.
- Lado a analizar claramente visible; para comparar lados se requerirá otro vídeo o una captura válida del lado contrario.

La validación debe diferenciar entre:

- `rejected`: no es posible obtener un resultado fiable.
- `accepted_with_warnings`: puede procesarse, pero la confianza máxima se limita.
- `accepted`: cumple los requisitos mínimos.

## 7. Modelo de datos inicial

### `users`

- `id`
- `created_at`
- `consent_version`

### `analyses`

- `id`
- `user_id`
- `status`
- `video_object_key`
- `side`
- `created_at`
- `completed_at`
- `pipeline_version`
- `ruleset_version`
- `error_code`

### `video_quality`

- `analysis_id`
- `duration_seconds`
- `fps`
- `width`
- `height`
- `valid_frame_ratio`
- `usable_cycle_count`
- `quality_status`
- `warnings` JSONB

### `biomechanical_metrics`

- `analysis_id`
- `metric_name`
- `value`
- `unit`
- `min_value`
- `max_value`
- `confidence`
- `sample_count`
- `calculation_version`

### `diagnoses`

- `id`
- `analysis_id`
- `code`
- `title`
- `severity`
- `confidence`
- `evidence` JSONB
- `rule_version`

### `recommendations`

- `id`
- `diagnosis_id`
- `action_type`
- `amount_min`
- `amount_max`
- `unit`
- `priority`
- `rationale`

### `report_snapshots`

- `id`
- `analysis_id`
- `timestamp_ms`
- `object_key`
- `overlays` JSONB
- `caption`

### Evolución para aprendizaje

Cuando exista consentimiento explícito y un proceso de revisión humana, añadir:

- `adjustments_applied`: ajuste, magnitud, fecha y quién lo realizó.
- `follow_up_analyses`: relación entre análisis inicial y posterior.
- `expert_reviews`: diagnóstico experto, corrección aplicada y calidad de la revisión.
- `outcomes`: dolor percibido, comodidad, rendimiento subjetivo y resultado posterior.

No se debe usar este dataset para entrenar un modelo sin separar datos de entrenamiento, validación y prueba por ciclista. De lo contrario se produciría fuga de identidad entre sesiones del mismo usuario.

## 8. Métricas biomecánicas

Todas las métricas deben almacenar unidad, lado, ventana temporal, número de ciclos y confianza de observación.

### Geometría básica

- Extensión máxima de rodilla.
- Flexión máxima de rodilla.
- Ángulo de cadera.
- Ángulo de tobillo.
- Ángulo de tronco.
- Ángulo de codo.

### Dinámica

- Oscilación vertical o lateral de pelvis, según la vista disponible.
- Trayectoria de la rodilla durante el ciclo.
- Variación del tronco a lo largo de la pedalada.
- Simetría izquierda-derecha cuando ambos lados sean observables y comparables.

### Reglas de medición

- Definir explícitamente los puntos anatómicos y el sistema de coordenadas.
- Usar ángulos articulares orientados de forma consistente, no ángulos de pantalla ambiguos.
- No presentar una media aislada como verdad: mostrar rango, variabilidad y calidad de pose.
- Calcular métricas sobre varios ciclos y descartar transitorios de inicio y parada.
- Documentar la tolerancia esperada de cada métrica mediante validación contra mediciones de referencia.

## 9. Motor experto

### Contrato de una regla

Cada regla debe declarar:

```json
{
  "code": "KNEE_EXTENSION_LOW",
  "version": "1.0.0",
  "inputs": ["knee_extension_max_deg", "pelvic_rocking_deg"],
  "condition": "knee_extension_max_deg < 145",
  "diagnosis": "Probable sillín bajo",
  "recommendation": {
    "action": "RAISE_SADDLE",
    "min": 3,
    "max": 5,
    "unit": "mm"
  },
  "confidence_policy": "quality_adjusted_threshold",
  "priority": "medium"
}
```

### Reglas iniciales orientativas

Los umbrales siguientes son hipótesis de producto y deben validarse con un bike fitter antes de presentarse como recomendaciones fiables:

- Extensión máxima de rodilla menor de 145 grados: posible sillín bajo.
- Extensión máxima mayor de 155 grados junto con oscilación de pelvis: posible sillín alto.
- Codo muy abierto junto con tronco excesivamente inclinado: posible reach excesivo.
- Alta variabilidad de pelvis durante el ciclo: posible pérdida de estabilidad o altura de sillín no adecuada.
- Diferencia persistente entre lados: posible asimetría que requiere revisión, no una corrección automática.

### Confianza

La confianza no debe ser un número arbitrario. Propuesta inicial:

```text
confianza = confianza_de_pose
           * estabilidad_temporal
           * consistencia_entre_ciclos
           * fuerza_de_la_regla
```

La puntuación debe limitarse si el vídeo contiene advertencias. Cada diagnóstico debe incluir:

- Evidencia observada.
- Umbral aplicado.
- Calidad de los datos.
- Factores que podrían invalidarlo.
- Acción recomendada y magnitud sugerida.

## 10. API inicial

### Crear análisis

`POST /api/v1/analyses`

Crea un análisis y devuelve una URL de subida o una referencia de carga.

### Completar subida

`POST /api/v1/analyses/{analysis_id}/upload-complete`

Valida que el objeto exista y encola el procesamiento.

### Consultar estado

`GET /api/v1/analyses/{analysis_id}`

Respuesta mínima:

```json
{
  "id": "analysis_123",
  "status": "processing",
  "progress": 0.65,
  "warnings": []
}
```

### Consultar informe

`GET /api/v1/analyses/{analysis_id}/report`

Debe devolver puntuación, diagnósticos, recomendaciones, métricas, capturas y limitaciones.

### Reintentar

`POST /api/v1/analyses/{analysis_id}/retry`

Solo para errores recuperables y con idempotencia.

## 11. Informe de usuario

El informe debe organizarse por decisión, no por implementación técnica:

1. Resumen de la calidad del vídeo.
2. Puntuación global de posición, con explicación de qué representa.
3. Tres problemas prioritarios como máximo en la primera vista.
4. Para cada problema: diagnóstico, confianza, evidencia y captura anotada.
5. Recomendación concreta con rango prudente de ajuste.
6. Métricas detalladas y visualización del ciclo.
7. Limitaciones y cuándo consultar a un profesional.
8. Comparación histórica cuando el usuario tenga análisis previos.

La puntuación global no debe sugerir precisión clínica. Debe ser una puntuación de consistencia con los criterios implementados y mostrar sus componentes.

## 12. Uso del LLM

El LLM solo redacta lenguaje natural a partir de un objeto estructurado generado por el motor experto.

Controles obligatorios:

- Prompt versionado.
- Esquema de entrada y salida validado.
- Temperatura baja o configuración equivalente.
- Prohibición explícita de inventar métricas, diagnósticos o ajustes.
- Fallback determinista si el LLM falla.
- Registro de modelo, versión de prompt y hash de entrada.
- No enviar vídeo ni imágenes al LLM en el MVP salvo que exista una decisión específica de privacidad.

## 13. Privacidad, seguridad y seguridad física

- Obtener consentimiento para procesar vídeo y conservar datos derivados.
- Permitir eliminar vídeo, capturas y resultados.
- Cifrar tráfico y almacenamiento.
- Evitar exponer URLs permanentes de objetos.
- Separar identificadores de usuario de los artefactos de procesamiento cuando sea posible.
- Definir retención configurable para vídeos originales.
- No usar el resultado para diagnosticar dolor o lesiones.
- Mostrar que cualquier ajuste debe hacerse gradualmente y verificarse en una salida segura.
- Recomendar detener el uso y consultar a un profesional ante dolor, entumecimiento o pérdida de control.

## 14. Observabilidad y operaciones

Registrar por análisis:

- Duración de cada etapa.
- Versión de pipeline, modelo y reglas.
- Número de frames y ciclos.
- Ratio de frames válidos.
- Errores clasificados y reintentos.
- Tiempo de cola y tiempo total.
- Coste estimado de almacenamiento y LLM.

Métricas operativas:

- Porcentaje de vídeos procesados correctamente.
- Porcentaje rechazado por calidad.
- Tiempo p50/p95 de procesamiento.
- Porcentaje de informes generados sin fallback.
- Correcciones posteriores realizadas por usuarios o expertos.

## 15. Plan de implementación

### Fase 0: definición y validación

- Revisar reglas con uno o más bike fitters.
- Definir protocolo de grabación.
- Crear un conjunto pequeño de vídeos consentidos y anotados.
- Fijar definiciones matemáticas de cada ángulo y métrica.

### Fase 0.5: laboratorio en notebook

Antes de construir la API y la interfaz, validar el núcleo técnico en una notebook reproducible:

- Generar o cargar señales de articulaciones para comprobar el cálculo de ángulos.
- Visualizar la pose y las métricas por ciclo de pedalada.
- Medir estabilidad, frames válidos y sensibilidad al ruido.
- Ejecutar las primeras reglas con entradas conocidas y revisar sus evidencias.
- Incorporar después un vídeo real consentido y guardar sus resultados anonimizados.

La notebook no debe considerarse todavía un producto ni una herramienta de diagnóstico. Su objetivo es responder si la señal obtenida con MediaPipe tiene suficiente calidad para continuar. Cada experimento debe registrar versión de MediaPipe, modelo, parámetros, vídeo de entrada o semilla sintética y conclusiones.

El primer entregable experimental será `notebooks/01_pose_and_bike_fit_experiment.ipynb`. Debe poder ejecutarse sin vídeo para validar las matemáticas y debe dejar una sección claramente delimitada para activar el procesamiento de un vídeo real cuando las dependencias estén instaladas.

### Fase 1: esqueleto de producto

- Inicializar Next.js, FastAPI y PostgreSQL.
- Implementar autenticación mínima o sesión anónima controlada.
- Implementar creación de análisis, subida y estados.
- Configurar almacenamiento de objetos y jobs.

### Fase 2: pipeline biomecánico

- Integrar extracción de frames y MediaPipe Pose.
- Implementar control de calidad.
- Implementar ciclos de pedalada.
- Calcular las primeras métricas y guardar datos reproducibles.

### Fase 3: reglas e informe

- Implementar reglas versionadas.
- Añadir cálculo de confianza y evidencias.
- Construir informe visual sin LLM.
- Añadir LLM únicamente para redactar explicaciones sobre resultados ya decididos.

### Fase 4: validación

- Comparar resultados con mediciones manuales o instrumentadas.
- Medir repetibilidad con varios vídeos del mismo ciclista.
- Revisar falsos positivos y falsos negativos con expertos.
- Ajustar umbrales y límites de confianza.

### Fase 5: aprendizaje con datos

- Registrar ajustes aplicados y análisis de seguimiento con consentimiento.
- Crear proceso de revisión y etiquetado.
- Establecer partición por ciclista.
- Evaluar un modelo de recomendación solo contra el baseline de reglas.

## 16. Criterios de aceptación del MVP

- Un usuario puede subir un vídeo válido y obtener un estado de procesamiento visible.
- Un vídeo inválido devuelve un motivo comprensible y una instrucción para repetirlo.
- Un análisis completado contiene al menos las métricas disponibles, calidad de datos y número de ciclos.
- Cada diagnóstico muestra regla, evidencia, confianza y versión.
- Cada recomendación está asociada a un diagnóstico y expresa una acción y un rango.
- El informe muestra capturas con superposición de puntos o ángulos.
- El LLM no puede introducir valores que no existan en la salida del motor experto.
- El mismo vídeo, pipeline y ruleset producen resultados equivalentes.
- El usuario puede eliminar sus artefactos almacenados.
- Las pruebas cubren reglas límite, frames faltantes, baja visibilidad, cero ciclos válidos y reintentos.

## 17. Riesgos y decisiones abiertas

### Riesgos

- MediaPipe puede perder articulaciones por oclusión, ropa o baja iluminación.
- Un vídeo 2D no permite inferir todos los movimientos tridimensionales.
- La vista lateral limita la detección de simetría real.
- Los umbrales pueden variar por antropometría, bicicleta, cadencia y técnica.
- Una recomendación incorrecta puede provocar incomodidad o lesión.

### Decisiones que deben cerrarse antes de producción

- ¿Se analizará un solo lado o ambos mediante vídeos separados?
- ¿Qué dispositivo de almacenamiento y cola se utilizará?
- ¿Habrá cuenta de usuario en el MVP o enlaces temporales?
- ¿Qué precisión mínima exige cada métrica?
- ¿Qué especialista revisará y aprobará las reglas?
- ¿Cuánto tiempo se conservarán vídeos y capturas?
- ¿Qué jurisdicciones y requisitos de privacidad aplican?
- ¿Qué magnitud máxima de ajuste puede recomendar automáticamente el sistema?

## 18. Estrategia de pruebas

### Unitarias

- Cálculo de ángulos con geometrías conocidas.
- Detección de ciclos con señales sintéticas.
- Reglas por debajo, en y por encima de cada umbral.
- Cálculo de confianza con calidades límite.
- Validación de esquemas del informe.

### Integración

- Subida y transición de estados.
- Job completo con vídeo de prueba.
- Persistencia de métricas, diagnósticos y capturas.
- Reintentos e idempotencia.
- Fallback del LLM.

### Evaluación biomecánica

- Concordancia contra anotación humana.
- Repetibilidad entre vídeos del mismo ciclista.
- Sensibilidad a resolución, iluminación y oclusiones.
- Revisión experta de recomendaciones.

### Frontend

- Flujo móvil de subida.
- Estados de error y procesamiento.
- Informe legible en móvil y escritorio.
- Accesibilidad de controles, colores y textos.

## 19. Definición de terminado

Una funcionalidad está terminada cuando:

- Tiene contrato de datos y pruebas.
- Registra versiones relevantes.
- Maneja errores y datos insuficientes.
- Explica al usuario la evidencia y las limitaciones.
- Está cubierta por observabilidad básica.
- Ha sido revisada en el dispositivo y flujo objetivo.
- No convierte una inferencia de vídeo en una afirmación médica.
