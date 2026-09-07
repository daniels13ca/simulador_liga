# simulador_liga
Simulador Monte Carlo de posiciones finales del todos contra todos de la Liga BetPlay Dimayor (Colombia), a partir de la tabla actual, los partidos restantes y el historial real de resultados desde 2025.

## Qué hace
Para cada partido que falta por jugarse, simula un resultado (con marcador incluido) ponderado por la fuerza real de cada equipo, repite eso 100 000 veces para toda la temporada, y con eso calcula la probabilidad de que cada equipo termine en cada posición final de la tabla. Exporta la tabla de probabilidades a Excel y genera una gráfica de barras apiladas con el top 8 (los que clasifican a cuadrangulares).

## Cómo correr el proyecto
1. Instala las dependencias: `pip install pandas numpy matplotlib tqdm openpyxl` (o usa el entorno conda del repo).
2. Si hay partidos nuevos jugados desde la última corrida, actualiza los datos primero — ver la siguiente sección, **es el paso que más importa**.
3. Abre `Simulacion.ipynb` (Jupyter o VS Code) y ejecuta todas las celdas ("Run All"). Esto lee `Tabla.csv`, `Partidos.csv`, `Historial_partidos.csv` y `model_params.csv`, corre las 100 000 simulaciones, y genera `Resultados.xlsx`.
4. Abre `Resultados.ipynb` y ejecuta todas las celdas. Lee `Resultados.xlsx` y genera `Resultado.png`.

También se pueden ejecutar sin abrir Jupyter, desde la terminal:
```
jupyter nbconvert --to notebook --execute --inplace Simulacion.ipynb
jupyter nbconvert --to notebook --execute --inplace Resultados.ipynb
```

## Cómo agregar resultados de partidos nuevos (importante)
El simulador solo es tan bueno como el estado de sus datos. Cada vez que se juegan partidos de la fecha en curso, hay que actualizar **tres archivos antes de volver a correr la simulación**: `Partidos.csv` (sacar el partido de pendientes), `Tabla.csv` (sumar puntos/goles) y `Historial_partidos.csv` (agregar el resultado real, es la base del Elo y del modelo de goles). Hacerlo a mano es fácil de arruinar (olvidar un archivo, invertir goles, desordenar el historial), así que hay un script que lo hace por vos: **`actualizar_resultados.py`**.

**Un solo partido:**
```
python3 actualizar_resultados.py --local "Millonarios" --visita "Once Caldas" --gl 2 --gv 1
```

**Una fecha completa** (varios partidos de una vez, más cómodo): crea un CSV como `nuevos_resultados.csv` con separador `;`:
```
Equipo Local;Equipo Visitante;Goles Local;Goles Visitante
Millonarios;Once Caldas;2;1
Junior;Deportivo Pasto;0;0
América de Cali;Fortaleza;3;1
```
y corre:
```
python3 actualizar_resultados.py --csv nuevos_resultados.csv
```

Los nombres de equipo deben escribirse **exactamente** igual que en `Partidos.csv`/`Tabla.csv` (mayúsculas y tildes incluidas), porque así se buscan las filas a actualizar. El script:
1. Busca cada partido en `Partidos.csv` por (Equipo Local, Equipo Visitante) y lo elimina — si no lo encuentra, se detiene con un error en vez de dejar los datos a medio actualizar.
2. Agrega el resultado real al final de `Historial_partidos.csv` (torneo/jornada se infieren del último valor visto ahí si no los pasás con `--torneo`/`--jornada`; no afectan el cálculo, solo son documentación).
3. Sube `PJ`, `GF`, `GC`, `Diferencia de Goles` y `Puntos` de ambos equipos en `Tabla.csv`, y renumera `Posicion actual`.

Después de correrlo, seguí con el paso 3 de "Cómo correr el proyecto" (ejecutar los dos notebooks) para que la simulación refleje los nuevos resultados.

Si preferís editar los CSV a mano: agregá la fila al final de `Historial_partidos.csv`, sumá los goles/puntos correspondientes en `Tabla.csv`, y borrá la fila de `Partidos.csv`. Lo único que **no** podés dejar desactualizado es `Historial_partidos.csv` en desorden cronológico (el Elo se calcula recorriéndolo de arriba a abajo) ni `Puntos`/`Diferencia de Goles` de `Tabla.csv` (son las únicas columnas de esa tabla que la simulación realmente usa para arrancar cada temporada simulada — `PJ`, `GF`, `GC` y `Posicion actual` son solo para referencia humana).

Si empieza una fecha completamente nueva del torneo y no está en `Partidos.csv` (por ejemplo, el fixture solo traía hasta cierta fecha), hay que agregar esos partidos a `Partidos.csv` a mano antes de poder cargarles resultado.

## Descripción algorítmica de la simulación
Cada una de las 100 000 iteraciones de Monte Carlo simula una temporada completa así:

1. **Punto de partida**: cada equipo arranca con sus `Puntos` y `Diferencia de Goles` actuales de `Tabla.csv`.
2. **Para cada partido pendiente** (en el orden de `Partidos.csv`):
   a. Se sortea el resultado (local/empate/visitante) con las probabilidades ya calculadas para ese partido (ver "Elo y probabilidades" abajo) — no es 33/33/33, son probabilidades específicas de ese enfrentamiento.
   b. Se simula un marcador (goles local, goles visitante) con un modelo de Poisson (ver "Modelo de goles" abajo), forzado a ser consistente con el resultado ya sorteado.
   c. Se suman los puntos de liga (3/1/0) y se actualiza la diferencia de gol de ambos equipos con los goles recién simulados.
3. **Al terminar todos los partidos pendientes**: se ordena a los 20 equipos por Puntos y, en caso de empate, por Diferencia de Goles (proyectada, no la actual), exactamente como especifica el reglamento. Esa posición final de esta iteración se registra.

Después de las 100 000 iteraciones, la probabilidad de cada equipo de terminar en cada posición es simplemente `(veces que terminó ahí) / 100000`.

### Elo y probabilidades
En vez de un rating inventado, cada equipo tiene un **Elo real** calculado recorriendo `Historial_partidos.csv` (~660 partidos reales de Apertura 2025 a la fecha actual) en orden cronológico: arranca en 1500 y se actualiza partido a partido con la fórmula estándar de Elo, `nuevo = viejo + K x (resultado_real - resultado_esperado)`. El "resultado esperado" de cada partido sale de la misma fórmula que decide las probabilidades de la simulación (autoconsistente):
```
delta = (Elo_local + HomeAdvantage) - Elo_visitante
sig = sigmoide(delta / RatingScale)
P_empate = DrawBias
P_local = (1 - DrawBias) x sig
P_visitante = (1 - DrawBias) x (1 - sig)
```
`HomeAdvantage`, `RatingScale`, `DrawBias` y `K` (en `model_params.csv`) no son supuestos: se calibraron con una búsqueda en grilla que minimiza el error de predicción (log-loss) sobre los ~660 partidos reales del historial. `DrawBias` en particular es exacto: es la proporción real de empates observada.

### Modelo de goles (Poisson)
Cada equipo tiene una fuerza de **ataque** y **defensa** relativa al promedio de la liga, calculada con todos los goles a favor/en contra de `Historial_partidos.csv` (no solo la temporada en curso, para no depender de una muestra chica). El número esperado de goles de cada equipo en un partido es:
```
goles_esperados_local    = promedio_goles_local    x ataque_local    x defensa_visitante
goles_esperados_visitante = promedio_goles_visitante x ataque_visitante x defensa_local
```
y el marcador se sortea de una distribución de Poisson con esas medias. Como el resultado (local/empate/visitante) ya se decidió con el Elo en el paso anterior, se vuelve a sortear el marcador hasta que sea consistente con ese resultado (por ejemplo, si ya se decidió "empate", se sortea hasta que ambos equipos saquen el mismo número de goles); si tarda demasiado en converger, se fuerza un marcador mínimo consistente en vez de trabarse.

## Explicación del código
`Simulacion.ipynb`, celda por celda:

1. **Imports**: `pandas`/`numpy` para tablas, `tqdm` para la barra de progreso, `math`/`random` para el modelo.
2. **`poisson_rv`, `simular_goles`, `simular_temporada`**: el núcleo de una temporada simulada (ver descripción algorítmica arriba). `simular_temporada` recibe las probabilidades ya calculadas y los factores de ataque/defensa, y devuelve la posición final de cada equipo para esa única iteración.
3. **`validar_datos`, `calcular_elo`, `calcular_ataque_defensa`, `probabilidades_partido`, `calcular_probabilidades_partidos`**: preparan todo lo que `simular_temporada` necesita, una sola vez por corrida completa (no en cada una de las 100 000 iteraciones, sería carísimo):
   - `validar_datos` corta la ejecución temprano si un equipo de `Partidos.csv` no existe en `Tabla.csv` (evita un `KeyError` confuso a mitad de la simulación).
   - `calcular_elo` recorre `Historial_partidos.csv` y devuelve el Elo final de cada equipo.
   - `calcular_ataque_defensa` recorre el mismo historial y devuelve la fuerza ofensiva/defensiva de cada equipo más los promedios de gol de la liga.
   - `probabilidades_partido` convierte una diferencia de Elo en `(P_local, P_empate, P_visitante)`.
   - `calcular_probabilidades_partidos` aplica lo anterior a cada partido de `Partidos.csv`, una sola vez.
4. **`simular_montecarlo`**: corre `simular_temporada` 100 000 veces (con una semilla fija para que sea reproducible) y arma la tabla final de probabilidades por posición.
5. **Celda principal**: carga los 4 archivos de datos, llama a las funciones anteriores en orden, corre la simulación y exporta `Resultados.xlsx`.
6. **Celda de gráfico**: se queda con las posiciones 1 a 8 y arma un gráfico de barras apiladas por equipo.

`Resultados.ipynb` solo lee `Resultados.xlsx` y dibuja la versión final (`Resultado.png`) con estilo de tabla debajo del gráfico.

`actualizar_resultados.py` es el script de mantenimiento descrito en la sección anterior — no corre la simulación, solo mantiene los datos de entrada al día.

## Archivos del repo
- `.gitattributes`: configuración de atributos de Git.
- `Historial_partidos.csv`: resultados reales (goles local/visitante) de Apertura 2025, Finalización 2025, Apertura 2026 y Finalización 2026 hasta la fecha, en orden cronológico. Base del Elo y del modelo de goles.
- `model_params.csv`: parámetros del modelo (`HomeAdvantage`, `RatingScale`, `DrawBias`, `MinProb`, `K_elo`), con una columna `Origen` que indica cómo se calibró cada uno.
- `Partidos.csv`: partidos pendientes por jugar (separador `;`).
- `Tabla.csv`: tabla de posiciones actual (separador `;`).
- `actualizar_resultados.py`: script para cargar resultados nuevos (ver arriba).
- `Simulacion.ipynb`: notebook principal, corre la simulación Monte Carlo y genera `Resultados.xlsx`.
- `Resultados.ipynb`: notebook que genera `Resultado.png` a partir de `Resultados.xlsx`.
- `Resultados.xlsx`: salida generada por `Simulacion.ipynb`.
- `Resultado.png`: gráfica final generada por `Resultados.ipynb`.

## Formato de datos
`Tabla.csv` — solo `Puntos` y `Diferencia de Goles` los usa la simulación; el resto es referencia:
- `Posicion actual` (int), `Equipo` (str), `Puntos` (int), `PJ` (int), `GF` (int), `GC` (int), `Diferencia de Goles` (int)

`Partidos.csv`:
- `Equipo Local` (str), `Equipo Visitante` (str)

`Historial_partidos.csv` (en orden cronológico, de más viejo a más nuevo):
- `Torneo` (str, p.ej. `2025-I`, `2025-II`, `2026-I`, `2026-II`), `Jornada` (int, solo informativo)
- `Equipo Local` (str), `Equipo Visitante` (str), `Goles Local` (int), `Goles Visitante` (int)

`model_params.csv`:
- `Parametro` (str), `Valor` (float), `Origen` (str: cómo se calibró)

## Requisitos
- Python 3.13+ (el notebook indica `python 3.13.5`).
- Paquetes: `pandas`, `numpy`, `matplotlib`, `tqdm`, `openpyxl`.

## Notas
- `HomeAdvantage`, `RatingScale`, `K_elo` y `DrawBias` se calibraron minimizando el log-loss de predicción sobre `Historial_partidos.csv` (≈1.03 del modelo calibrado vs. ≈1.10 de un modelo equiprobable). No quedan parámetros puramente asumidos.
- La semilla de la simulación (`SEED` en `Simulacion.ipynb`) está fija en 42 para que la corrida sea reproducible; poné `None` ahí si querés que el resultado varíe en cada ejecución.
- La cantidad de simulaciones se controla con `num_simulaciones` en `Simulacion.ipynb` (por defecto 100000).
- Si el torneo termina o cambia de fase (por ejemplo, a cuadrangulares), este simulador de todos-contra-todos deja de aplicar tal cual — habría que adaptar `Partidos.csv`/`Tabla.csv` al nuevo formato de esa fase.
