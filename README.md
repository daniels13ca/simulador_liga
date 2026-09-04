# simulador_liga
Simulador Monte Carlo de posiciones finales del todos contra todos del FPC (Liga colombiana), a partir de la tabla actual y los partidos restantes.

**Qué hace**
- Simula resultados para los partidos pendientes, ponderados por un rating relativo de cada equipo (no equiprobable).
- Calcula la probabilidad de que cada equipo termine en cada posición.
- Exporta los resultados a Excel y genera una gráfica apilada.

**Cómo funciona el modelo**
- **Rating por equipo**: se deriva de `Tabla.csv` (puntos por partido jugado y diferencia de gol por partido jugado, normalizados). Al arranque de temporada, cuando hay pocos partidos jugados (`PJ` bajo), se mezcla con la posición final del torneo anterior (`Data.xlsx`) para reducir el ruido de una muestra chica; ese peso decae a medida que avanzan las fechas.
- **Probabilidad por partido**: a partir del rating de local y visitante, más una ventaja de localía, se calcula `P_local`/`P_empate`/`P_visitante` con una función sigmoide (parámetros en `model_params.csv`).
- **Desempate**: si dos equipos terminan con los mismos puntos simulados, desempata la diferencia de gol actual (no se simulan goles de los partidos restantes).
- **Reproducibilidad**: la corrida usa una semilla fija (`SEED` en `Simulacion.ipynb`) para que el resultado sea repetible; se puede poner en `None` para que varíe en cada ejecución.
- **Validación de datos**: al cargar los CSV se verifica que todo equipo de `Partidos.csv` exista en `Tabla.csv`, y falla con un mensaje claro si no.
- El modelo **no** simula goles partido a partido (Poisson) ni usa un Elo real: ambas cosas quedan bloqueadas hasta contar con un histórico de resultados o una fuente externa de ratings (no se necesitan hoy porque no hay más datos disponibles que los de este repo).

**Archivos del repo**
- `.gitattributes`: configuración de atributos de Git.
- `Data.xlsx`: tabla final y fixture de ejemplo del torneo anterior (Apertura 2026-I). Se usa como prior de arranque de temporada (ver arriba).
- `model_params.csv`: parámetros del modelo (`HomeAdvantage`, `DrawBias`, `RatingScale`, `MinProb`, `K_prior`), con una columna `Origen` que indica si cada valor es un supuesto o si se calibró con los datos actuales.
- `Partidos.csv`: partidos restantes (separador `;`).
- `Resultado.png`: gráfica final generada por `Resultados.ipynb`.
- `Resultados.ipynb`: notebook que genera la imagen a partir de `Resultados.xlsx`.
- `Resultados.xlsx`: salida generada por `Simulacion.ipynb`.
- `Simulacion.ipynb`: notebook principal con la simulación Monte Carlo.
- `Tabla.csv`: tabla actual de posiciones (separador `;`).

**Requisitos**
- Python 3.13+ (el notebook indica `python 3.13.5`).
- Paquetes: `pandas`, `numpy`, `matplotlib`, `tqdm`, `openpyxl`.

**Cómo usar**
1. Abre `Simulacion.ipynb` en Jupyter o VS Code y ejecuta todas las celdas.
2. Se generará `Resultados.xlsx`.
3. Abre `Resultados.ipynb` y ejecuta las celdas para crear `Resultado.png`.

**Formato de datos**
`Tabla.csv`:
- `Posicion actual` (int)
- `Equipo` (str)
- `Puntos` (int)
- `PJ` (int) — partidos jugados; se usa para normalizar el rating y para el peso del prior de `Data.xlsx`.
- `Diferencia de Goles` (int)

`Partidos.csv`:
- `Equipo Local` (str)
- `Equipo Visitante` (str)

`model_params.csv`:
- `Parametro` (str), `Valor` (float), `Origen` (str: si es un supuesto o si se calibró con los datos de `Tabla.csv`).

**Notas**
- `DrawBias` (probabilidad base de empate) se calibra exacto con los datos de la temporada en curso: `empates_totales = 3 x partidos_jugados_totales - puntos_totales_repartidos`. `HomeAdvantage` y `RatingScale` son supuestos de referencia (no hay datos de resultados por localía para calibrarlos).
- Si cambia la tabla o el fixture, basta con reejecutar `Simulacion.ipynb`; el `DrawBias` de `model_params.csv` no se recalcula solo, así que si quieres que siga siendo exacto hay que actualizarlo a mano con los nuevos totales de `Tabla.csv`.
- La cantidad de simulaciones se controla con `num_simulaciones` (por defecto 100000).
