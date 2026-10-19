# Cómo analizar los resultados del laboratorio de bike fit

Esta guía explica cómo interpretar las métricas que produce
[notebooks/01_pose_and_bike_fit_experiment.ipynb](../notebooks/01_pose_and_bike_fit_experiment.ipynb)
y qué rangos de referencia de ajuste de bicicleta pueden usarse como umbrales
**exploratorios**. No es una herramienta clínica ni sustituye la valoración de un
profesional (fitter o fisioterapeuta).

## 1. Principio de partida: no existe una medida universal

Todas las fuentes consultadas coinciden en un punto clave: **no hay un único valor
"correcto"** de altura de sillín, retroceso o ángulo articular. Los rangos
publicados son puntos de partida que dependen de:

- Disciplina (carretera, contrarreloj/triatlón, gravel, MTB).
- Flexibilidad de la cadena posterior (isquiotibiales, glúteos).
- Proporciones individuales (longitud de fémur, tibia y pie).
- Estilo de pedaleo y posición del tobillo (talón arriba/abajo).
- Cadencia e intensidad del esfuerzo.
- Punto exacto del ciclo de pedalada en el que se mide.

Por eso, las reglas de la notebook deben expresar **diagnóstico + evidencia +
confianza**, y bajar la confianza cuando la calidad de la anotación es baja.

## 2. Cómo leer el ángulo de rodilla (`knee_angle`)

La función `angle_at` devuelve el **ángulo interno** de la articulación:

- Pierna extendida → cercano a `180°`.
- Pierna muy flexionada → valor bajo.

La literatura de bike fit habla normalmente de **flexión** (cuánto le falta a la
rodilla para estar recta), que es el complementario:

$$\text{flexión} \approx 180° - \text{ángulo interno}$$

### Rangos de referencia (extensión máxima, cerca del punto muerto inferior)

| Método / condición                         | Flexión de rodilla | Ángulo interno equivalente |
| ------------------------------------------ | ------------------ | -------------------------- |
| Método Holmes (medición **estática**)      | 25–35°             | ~145–155°                  |
| Dinámico, baja intensidad (BDC)            | 33–43°             | ~137–147°                  |
| Dinámico, alta intensidad (BDC)            | 30–40°             | ~140–150°                  |

Notas importantes:

- El ángulo **estático** y el **dinámico** no coinciden: 25–35° estático puede
  corresponder a 30–40° dinámico. La notebook mide sobre frames de vídeo, así que
  está más cerca del caso dinámico.
- El ángulo depende mucho de la **posición del tobillo**; hay que medirlo en un
  punto comparable del ciclo.
- Un ángulo interno **bajo** (mucha flexión) sugiere sillín potencialmente bajo;
  un ángulo **alto** (poca flexión) sugiere sillín potencialmente alto.

> El umbral actual de la notebook (`< 145` bajo, `> 155` alto) es coherente con el
> rango estático de Holmes, pero **solo tiene sentido si se evalúa en frames
> cercanos al punto muerto inferior**, no en cualquier frame del ciclo.

### Requisito de medición correcta

Antes de aplicar la regla de rodilla:

1. Identificar el frame de **máxima extensión** (mínimo de flexión) dentro de cada
   ciclo de pedalada, en lugar de usar todos los frames.
2. Confirmar que rodilla, cadera y tobillo del lado analizado son visibles
   (`occluded == False`, `outside == False`).
3. Reducir la confianza si el frame tiene movimiento rápido o baja visibilidad.

## 3. Altura de sillín

La altura de sillín no se mide directamente en la imagen, pero el ángulo de rodilla
en extensión máxima es su mejor proxy 2D. Fórmulas de referencia habituales
(solo como punto de partida, **no** como diagnóstico):

- **LeMond:** `altura = entrepierna × 0,883` (del eje de pedalier a la parte
  superior del sillín).
- **Hamley:** `altura = entrepierna × 1,09` (de la superficie del pedal al sillín;
  incluye longitud de biela).

Limitaciones documentadas: estas fórmulas fallan más de la mitad de las veces en
mantener la rodilla dentro del rango 25–35°, porque no consideran fémur, tibia,
pie ni biela. **Preferir siempre el criterio del ángulo de rodilla** sobre la
fórmula.

Señales de altura incorrecta observables en pose:

- Balanceo lateral de la pelvis → posible sillín **demasiado alto**.
- Punto muerto / pérdida de contacto abajo → posible sillín **demasiado alto**.
- Estilo muy de puntillas (talón abajo) → puede indicar sillín alto compensado.

## 4. Retroceso de sillín (fore-aft) y KOPS

`KOPS` (Knee Over Pedal Spindle): con la biela horizontal, una vertical desde la
tuberosidad tibial pasa por el eje del pedal.

- Es un **punto de partida**, no una regla física. No tiene que cumplirse
  exactamente.
- En bicis de contrarreloj/triatlón la rodilla suele quedar **por delante** del eje
  del pedal de forma intencionada (sillín adelantado, cadera más abierta).
- Lo que realmente importa es el **equilibrio**: poco peso sobre las manos, pelvis
  estable y buen reparto de carga muscular.

Efecto acoplado a tener en cuenta: mover el sillín hacia delante/atrás cambia la
altura efectiva (≈ 3 mm de altura por cada 10 mm de fore-aft). Altura y retroceso
deben analizarse **juntos**.

## 5. Ángulo de cadera (`hip_angle`)

- Depende fuertemente de disciplina y flexibilidad.
- Referencia para contrarreloj/triatlón (ángulo mínimo de cadera sostenible):
  ~50° para un triatleta de flexibilidad media, ~45° para eventos cortos, ~40° solo
  en riders muy flexibles.
- **No** conviene usar un umbral universal de cadera para carretera; trátalo como
  descriptor, no como regla, en esta fase.

Recordatorio: la medición asume columna recta (hombro–cadera–rodilla), lo que rara
vez es exacto, así que el ángulo real suele ser algo mayor que el medido.

## 6. Oscilación de pelvis (`pelvis_y_spread`)

La métrica actual es la diferencia vertical en píxeles entre ambas caderas.
Problema: **un umbral fijo en píxeles (p. ej. `18`) no es transferible** entre
vídeos con distinta resolución, encuadre o distancia de cámara.

Recomendación: **normalizar** antes de comparar, dividiendo por una referencia
anatómica del propio frame, por ejemplo:

- Altura de la imagen.
- Longitud del fémur (distancia cadera–rodilla) en píxeles.
- Distancia entre caderas o entre hombros.

Así `pelvis_y_spread_normalizado` se vuelve comparable entre vídeos y el umbral
tiene un significado estable.

## 7. Consistencia entre lados y estabilidad temporal

Además de los valores absolutos, estas señales indican fiabilidad:

- **Diferencia izquierda/derecha** (`knee_side_difference_mean`): cuando ambos lados
  son visibles, deberían ser razonablemente parecidos. Una diferencia grande puede
  ser asimetría real **o** error de anotación/detección.
- **Desviación estándar por vídeo** (`knee_left_std`, `knee_right_std`): una
  variación muy alta entre frames consecutivos sugiere señal inestable (anotación o
  detección), no biomecánica real.
- **Saltos entre frames consecutivos**: los ángulos deberían evolucionar de forma
  suave a lo largo del ciclo de pedalada.

## 8. Checklist de análisis recomendado

1. **Calidad de datos primero:** verificar visibilidad de landmarks
   (`visible_landmark_ratio`, flags `occluded`/`outside`) antes de creer una cifra.
2. **Elegir el frame correcto:** medir la rodilla en la extensión máxima del ciclo,
   no en frames arbitrarios.
3. **Aplicar rangos como exploratorios:** rodilla ~`140–150°` de ángulo interno
   como zona plausible; fuera de ahí, marcar hipótesis (sillín alto/bajo) con
   confianza moderada.
4. **Normalizar métricas en píxeles** (oscilación de pelvis) por una referencia
   anatómica.
5. **Cruzar con estabilidad:** confianza alta solo si la métrica es estable en el
   tiempo y consistente entre lados.
6. **Reportar evidencia + confianza**, nunca un veredicto absoluto.

## 9. Criterio de decisión del experimento

El núcleo técnico se considera válido si:

- Los landmarks anotados caen sobre el ciclista en las imágenes asociadas.
- Los ángulos no presentan saltos inexplicables entre frames consecutivos.
- La variación de rodilla y pelvis permite distinguir fases de la pedalada.
- Los resultados son consistentes entre lados cuando ambos son visibles.

**Siguiente paso:** comparar estas métricas de referencia (anotación manual) con la
salida de MediaPipe Pose sobre las mismas imágenes, para medir el error del detector
antes de endurecer las reglas.

## Fuentes consultadas

- Cycling Weekly — Altura de sillín (métodos LeMond, Hamley, Holmes; estático vs
  dinámico): <https://www.cyclingweekly.com/fitness/bike-fit/set-saddle-height-how-to-25379>
- Cycling Weekly — Retroceso de sillín, KOPS y balance:
  <https://www.cyclingweekly.com/fitness/bike-fit/just-how-important-is-saddle-setback-plus-how-to-tell-if-yours-is-too-far-forwards-or-backwards>
- BikeDynamics — Saddle fore-aft y KOPS como "happy accident":
  <https://bikedynamics.co.uk/saddleforeaft.htm>
- BikeDynamics — Posición de contrarreloj y ángulo mínimo de cadera:
  <https://bikedynamics.co.uk/FitGuideTT.htm>

> Aviso: los rangos numéricos anteriores son orientativos y provienen de guías
> divulgativas y de fitters. Deben validarse contra literatura científica revisada
> antes de convertirlos en reglas de producto.
