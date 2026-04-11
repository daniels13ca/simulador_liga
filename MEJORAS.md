# Opciones de mejora del simulador

Este documento lista mejoras posibles para el algoritmo de simulacion, incluye un modelo de datos propuesto y opciones para obtener un rating tipo Elo por equipo.

## 1) Mejoras de modelo (prioridad sugerida)

1. **Probabilidades realistas por partido**
   - Introducir un sesgo de localia y/o rating de equipos para calcular probabilidades de local/empate/visita.
   - Beneficio: resultados mas realistas que la equiprobabilidad actual.

2. **Desempates segun reglamento**
   - Ordenar por Puntos, Diferencia de Goles, Goles a Favor, etc.
   - Beneficio: posiciones finales mas coherentes con la liga real.

3. **Simulacion de goles (Poisson)**
   - Generar goles por equipo y actualizar diferencia de goles en cada partido.
   - Beneficio: permite desempates completos y distribuciones mas realistas.

4. **Validacion de datos de entrada**
   - Verificar que los equipos de `Partidos.csv` existan en `Tabla.csv`.
   - Beneficio: evita errores silenciosos por nombres mal escritos.

5. **Reproducibilidad**
   - Permitir fijar `random.seed()` para resultados repetibles.

6. **Calibracion basica**
   - Ajustar probabilidades globales de local/empate/visita con historicos reales.

## 2) Modelo de datos propuesto

### 2.1 Equipos (`equipos.csv`)
Campos sugeridos:
- `Equipo` (str, PK)
- `Puntos` (int)
- `PJ` (int)
- `GF` (int)
- `GC` (int)
- `DG` (int, opcional si se calcula)
- `Rating` (float, opcional si no se usa Elo)
- `Forma` (float, opcional, ultimos 5 partidos)

### 2.2 Partidos (`partidos.csv`)
Campos sugeridos:
- `Equipo Local` (str)
- `Equipo Visitante` (str)
- `Jornada` (int, opcional)
- `Fecha` (date, opcional)
- `Neutral` (bool, opcional; 1 si no hay localia real)

### 2.3 Parametros del modelo (`model_params.csv`)
Campos sugeridos:
- `HomeAdvantage` (float)  
- `DrawBias` (float)
- `RatingScale` (float)
- `MinProb` (float)

### 2.4 Salidas
- `Resultados.xlsx` (tabla de probabilidades por posicion)
- `Resultado.png` (grafica apilada)

## 3) Opciones para obtener Elo (o ratings similares)

Puedes obtener un rating tipo Elo de dos maneras: **fuentes externas** o **calculo propio**.

### 3.1 Fuentes externas (listas ya calculadas)
Opciones comunes:
- **ClubElo**: ratings Elo para clubes de futbol.
- **World Football Elo Ratings**: ratings Elo publicos por clubes/selecciones.
- **FiveThirtyEight SPI** (no es Elo puro, pero es un rating utilizable).

Ventaja: rapido de usar.
Desventaja: puede no incluir todos los equipos o no estar actualizado al corte de la liga.

### 3.2 Calculo propio (recomendado si quieres control)
- Tomar historicos de resultados (oficiales o de un proveedor de datos).
- Calcular Elo por temporada o acumulado con un factor K fijo.
- Ajustar por localia y, si quieres, por diferencia de goles.

Ventaja: control total y transparencia.
Desventaja: requiere historicos limpios y mantenimiento.

## 4) Formula simple sugerida (si hay rating)

- `delta = (RatingLocal + HomeAdvantage) - RatingVisitante`
- `P_local = sigmoid(delta / RatingScale)`
- `P_empate = DrawBias`
- `P_visitante = 1 - P_local - P_empate`
- Aplicar `MinProb` y renormalizar.

## 5) Proximo paso recomendado

1. Crear `equipos.csv` con `Rating` (aunque sea aproximado).
2. Añadir `model_params.csv`.
3. Modificar la simulacion para usar probabilidades ponderadas.