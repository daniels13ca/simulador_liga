# simulador_liga
Simulador Monte Carlo de posiciones finales del todos contra todos de la Liga BetPlay Dimayor (Colombia), a partir de la tabla actual, los partidos restantes y el historial real de resultados desde 2025.

## Objetivo
Responder, con una probabilidad concreta y no una intuición, la pregunta *"¿qué chance tiene mi equipo de clasificar a los ocho?"*, dado el estado real del torneo en curso. El modelo termina ahí a propósito: la fase de todos-contra-todos de la Liga BetPlay solo define quién avanza a la fase final (top 8) — el título se juega después en esa otra fase (cuadrangulares o playoffs, según el semestre) y el descenso se calcula con una tabla acumulada de varios años (el "promedio"), no con esta tabla de un solo semestre. Ninguna de esas dos cosas es lo que este simulador calcula.

Para eso, en vez de asumir que cada partido pendiente es un volado de tres caras (local/empate/visitante equiprobables), el modelo usa la fuerza real de cada equipo — un **Elo** calculado sobre ~725 partidos oficiales jugados desde 2025 — para ponderar cada resultado posible, y un modelo de goles (**Poisson**) calibrado con los mismos datos para que la diferencia de gol de desempate también sea realista. Corre la temporada restante 100 000 veces con esas probabilidades y cuenta, para cada equipo, en qué posición terminó cada vez. El resultado es una tabla y un gráfico con la probabilidad real de cada equipo de terminar en cada puesto.

## Procedimiento de cálculo
El cálculo tiene tres etapas. Las primeras dos ocurren **una sola vez** por corrida (son las mismas para las 100 000 iteraciones); la tercera se repite 100 000 veces.

### Etapa 1 — Preparar el rating de cada equipo (una vez)
1. Cargar `Historial_partidos.csv` y ordenarlo por `Fecha` real (no por el orden en que están las filas en el archivo).
2. **Calcular el Elo** de cada equipo recorriendo ese historial en orden cronológico: todos arrancan en 1500 puntos y se actualizan partido a partido con la fórmula estándar de Elo. El Elo final (al día de hoy) es el que se usa para lo que sigue.
3. **Calcular ataque y defensa** de cada equipo: cuántos goles marca/recibe por partido, relativo al promedio de la liga, usando el mismo historial completo (no solo la temporada en curso).

### Etapa 2 — Calcular la probabilidad de cada partido pendiente (una vez)
Para cada partido de `Partidos.csv`, a partir del Elo de local y visitante más una ventaja de localía, una sigmoide da `P_local` / `P_empate` / `P_visitante`:
```
delta = (Elo_local + HomeAdvantage) - Elo_visitante
sig = sigmoide(delta / RatingScale)
P_empate = DrawBias
P_local = (1 - DrawBias) x sig
P_visitante = (1 - DrawBias) x (1 - sig)
```
`HomeAdvantage`, `RatingScale`, `DrawBias` y `K` (en `model_params.csv`) no son supuestos: se calibraron con una búsqueda en grilla que minimiza el error de predicción (log-loss) sobre los ~725 partidos reales del historial (log-loss ≈1.03 del modelo calibrado vs. ≈1.10 de un modelo equiprobable). `DrawBias` en particular es exacto: es la proporción real de empates observada en el historial.

### Etapa 3 — Simular una temporada (se repite 100 000 veces)
Cada iteración de Monte Carlo hace esto:
1. Cada equipo arranca con sus `Puntos` y `Diferencia de Goles` actuales de `Tabla.csv`.
2. Para cada partido pendiente (en el orden de `Partidos.csv`):
   - Se sortea el resultado (local/empate/visitante) con las probabilidades ya calculadas en la Etapa 2 para ese enfrentamiento puntual.
   - Se simula un marcador (goles local, goles visitante) con una distribución de Poisson, usando el ataque/defensa de la Etapa 1; el marcador se vuelve a sortear hasta que sea consistente con el resultado ya decidido (p. ej. si ya se decidió "empate", hasta que ambos equipos saquen el mismo número de goles).
   - Se suman los puntos de liga (3/1/0) y se actualiza la diferencia de gol de ambos equipos con los goles recién simulados.
3. Al terminar todos los partidos pendientes, se ordenan los 20 equipos por Puntos y, en caso de empate, por Diferencia de Goles (la proyectada con los goles simulados, no la actual), exactamente como especifica el reglamento. Esa posición final de esta iteración se registra.

### Después de las 100 000 iteraciones
La probabilidad de que un equipo termine en una posición dada es simplemente `(veces que terminó ahí) / 100 000`. Esa tabla se exporta a `Resultados.xlsx`, y de ahí se genera el gráfico `Resultado.png`.

## Cómo correr el proyecto
1. Instala las dependencias: `pip install pandas numpy matplotlib tqdm openpyxl` (o usa el entorno conda del repo).
2. Si hay partidos nuevos jugados desde la última corrida, actualiza los datos primero — ver la siguiente sección, **es el paso que más importa**.
3. Abre `Simulacion.ipynb` (Jupyter o VS Code) y ejecuta todas las celdas ("Run All"). Esto lee `Tabla.csv`, `Partidos.csv`, `Historial_partidos.csv` y `model_params.csv`, corre las 100 000 simulaciones (Etapas 1-3 de arriba), y genera `Resultados.xlsx`.
4. Abre `Resultados.ipynb` y ejecuta todas las celdas. Lee `Resultados.xlsx` y genera `Resultado.png`.

También se pueden ejecutar sin abrir Jupyter, desde la terminal:
```
jupyter nbconvert --to notebook --execute --inplace Simulacion.ipynb
jupyter nbconvert --to notebook --execute --inplace Resultados.ipynb
```

## Cómo actualizar resultados de partidos nuevos (paso a paso)
El simulador solo es tan bueno como el estado de sus datos: si `Partidos.csv`/`Tabla.csv`/`Historial_partidos.csv` no reflejan lo que ya se jugó, el resultado va a estar mal sin ningún aviso. Cada vez que se juega una fecha hay que actualizar **los tres archivos antes de volver a correr la simulación**. Usa el script `actualizar_resultados.py`; hacerlo a mano es fácil de arruinar (olvidar un archivo, invertir los goles, desordenar el historial).

### Paso 0 — Anotar qué se jugó
Para cada partido terminado necesitás: equipo local, equipo visitante, goles de cada uno. Nada más — la fecha, el torneo y la jornada el script los toma solos de `Partidos.csv`.

### Paso 1 — Elegir cómo cargarlo
- **Un solo partido**, desde la terminal, parado en la carpeta del repo:
  ```
  python3 actualizar_resultados.py --local "Millonarios" --visita "Deportivo Cali" --gl 2 --gv 1
  ```
- **Varios partidos de la misma fecha** (lo normal — se juegan ~10 partidos por jornada): crea un archivo de texto, por ejemplo `nuevos_resultados.csv`, con separador `;` y esta forma exacta (respetando mayúsculas/tildes de los nombres de equipo):
  ```
  Equipo Local;Equipo Visitante;Goles Local;Goles Visitante
  Millonarios;Deportivo Cali;2;1
  Jaguares;Fortaleza;0;0
  Santa Fe;Deportes Tolima;1;3
  ```
  y corré:
  ```
  python3 actualizar_resultados.py --csv nuevos_resultados.csv
  ```

### Paso 2 — Leer la salida y confirmar que aplicó bien
Con el ejemplo de arriba (un solo partido), la salida real es:
```
OK: Millonarios 2-1 Deportivo Cali (2026-09-10, 2026-II, fecha 5)

Actualizados: Partidos.csv, Tabla.csv, Historial_partidos.csv.
Ahora corre Simulacion.ipynb y Resultados.ipynb para regenerar los resultados.
```
La línea `OK: ...` confirma equipos, marcador, fecha real tomada de `Partidos.csv`, torneo y jornada — revisá que diga lo que esperabas antes de seguir. Si algo no cuadra (por ejemplo la fecha), todavía podés corregir los tres archivos a mano (Paso 5) porque ya quedaron escritos en disco.

Qué hizo exactamente, por cada partido:
1. Lo buscó en `Partidos.csv` por (Equipo Local, Equipo Visitante) exacto y lo sacó de ahí — ya no está pendiente. De esa misma fila tomó la `Fecha` real (y la `Jornada`), salvo que hayas pasado `--fecha`/`--jornada` explícitos.
2. Agregó la fila `{Fecha, Torneo, Jornada, Equipo Local, Equipo Visitante, Goles Local, Goles Visitante}` a `Historial_partidos.csv` y **reordenó todo el archivo por `Fecha`** (no lo dejó al final: hay partidos aplazados que se juegan fuera del orden de su jornada nominal — le pasa a casi 1 de cada 3 partidos de este torneo — y el Elo depende de procesarlos en el orden real en que ocurrieron).
3. En `Tabla.csv`, a ambos equipos les subió `PJ` (+1), `GF`/`GC` (+goles reales), recalculó `Diferencia de Goles`, sumó `Puntos` (3 al ganador, 1 y 1 si fue empate), y renumeró `Posicion actual` de toda la tabla.

### Paso 3 — Verificar los archivos (opcional pero recomendado)
```
grep "Millonarios;\|Deportivo Cali;" Tabla.csv
tail -3 Historial_partidos.csv
grep -c "Millonarios;Deportivo Cali" Partidos.csv   # debe dar 0
```

### Paso 4 — Volver a correr la simulación
Seguí con el paso 3 de "Cómo correr el proyecto" (ejecutar `Simulacion.ipynb` y `Resultados.ipynb`) para que el Elo, el ataque/defensa y el resultado final reflejen lo que acabas de cargar.

### Casos especiales
- **Nombre de equipo mal escrito o inexistente**: el script no adivina ni actualiza nada a medias. Se detiene con:
  ```
  No encontre 'Millonarios FC' vs 'Deportivo Cali' en Partidos.csv. Revisa que los nombres coincidan exactamente (mayusculas/tildes incluidas).
  ```
  Corregí el nombre (copialo tal cual aparece en `Partidos.csv` o `Tabla.csv`) y volvé a correr el comando.
- **El partido no está en `Partidos.csv`** (por ejemplo, arrancó una fecha que el fixture cargado no incluía todavía): agregalo ahí a mano primero, con su `Fecha` programada y `Jornada`, en el mismo formato que las filas existentes. Después sí lo puede tomar el script.
- **Partido aplazado que se juega fuera de su jornada nominal**: no hay que hacer nada especial — el script reordena `Historial_partidos.csv` por `Fecha` real automáticamente, así que el Elo lo procesa en el momento correcto sin importar en qué orden lo hayas cargado.
- **Cargaste un resultado equivocado por error**: el script no tiene "deshacer". Corregí a mano: en `Historial_partidos.csv` borrá o corregí esa fila; en `Tabla.csv` revertí los puntos/goles de ambos equipos (o volvé a calcular la fila entera sumando manualmente todos sus partidos jugados); si el partido debe volver a quedar pendiente, agregalo de nuevo en `Partidos.csv`.
- **Ya se jugaron todos los partidos de `Partidos.csv`** (el torneo pasó a otra fase, p. ej. cuadrangulares o playoffs): este simulador de todos-contra-todos deja de aplicar tal cual — ver la nota al final del README.

### Paso 5 (alternativa) — Editar los CSV a mano, sin el script
Si preferís no usar el script: agregá la fila en `Historial_partidos.csv` en su lugar cronológico real por `Fecha` (o al final; el notebook la reordena de todos modos al cargarla, pero es más prolijo dejarla bien ubicada), sumá los goles/puntos correspondientes en `Tabla.csv`, y borrá la fila del partido en `Partidos.csv`. Lo único que **no** podés dejar mal es la columna `Fecha` de `Historial_partidos.csv` (el Elo se calcula recorriéndolo en ese orden) ni `Puntos`/`Diferencia de Goles` de `Tabla.csv` (son las únicas columnas de esa tabla que la simulación realmente usa para arrancar cada temporada simulada — `PJ`, `GF`, `GC` y `Posicion actual` son solo para referencia humana, aunque igual conviene mantenerlas al día).

### Solo partidos de liga
`Historial_partidos.csv` tiene *únicamente* partidos oficiales de la Liga BetPlay: la fase de todos-contra-todos **y también** cuadrangulares semifinales, cuartos de final, semifinales y finales (según el formato de cada semestre) — nunca Copa Colombia, Copa Libertadores/Sudamericana ni amistosos, porque mezclar esas competencias distorsionaría el Elo y el ataque/defensa con partidos de un nivel de rival totalmente distinto. La columna `Jornada` identifica la fase de cada partido (`1`-`20` para todos-contra-todos; `"Cuadrangular A - Fecha 3"`, `"Cuartos de final (serie 2, ida)"`, `"Final vuelta"`, etc. para las fases finales — son solo etiquetas descriptivas, no se usan en ningún cálculo). Si en algún momento se recarga el historial desde otra fuente: la fase de todos-contra-todos debe tener exactamente 10 partidos por fecha (20 equipos, todos contra todos una vez) y las fases finales deben coincidir con los campeones oficiales — así se verificó el historial actual, cruzando los marcadores contra los campeones reales de cada semestre (Santa Fe en Apertura 2025, Junior en Finalización 2025 y en Apertura 2026).

## Diccionario de archivos
Cada tabla lista las columnas tal como están en el CSV, en orden.

### `Tabla.csv` — tabla de posiciones actual
| Columna | Tipo | Ejemplo | ¿La usa la simulación? | Descripción |
|---|---|---|---|---|
| `Posicion actual` | int | `1` | No | Puesto en la tabla real, 1 a 20. Solo referencia; se renumera sola al correr `actualizar_resultados.py`. |
| `Equipo` | str | `América de Cali` | Sí | Nombre del equipo. Debe escribirse igual en los 4 archivos de datos (es la clave que los conecta). |
| `Puntos` | int | `20` | **Sí** | Puntos reales acumulados en la temporada actual. Punto de partida de cada temporada simulada. |
| `PJ` | int | `8` | No | Partidos jugados en la temporada actual. Solo referencia (el ataque/defensa/Elo se calculan de `Historial_partidos.csv`, no de esta columna). |
| `GF` | int | `20` | No | Goles a favor en la temporada actual. Solo referencia. |
| `GC` | int | `4` | No | Goles en contra en la temporada actual. Solo referencia. |
| `Diferencia de Goles` | int | `16` | **Sí** | `GF - GC`. Punto de partida del desempate de cada temporada simulada (Puntos, luego esta columna). |

### `Partidos.csv` — partidos que faltan por jugar
| Columna | Tipo | Ejemplo | ¿La usa la simulación? | Descripción |
|---|---|---|---|---|
| `Fecha` | date `YYYY-MM-DD` | `2026-09-10` | No | Fecha programada del partido. Solo informativa (y es lo que usa `actualizar_resultados.py` para completar `Historial_partidos.csv` cuando cargás el resultado). |
| `Jornada` | int | `5` | No | Número de fecha del todos-contra-todos. Solo informativa. |
| `Equipo Local` | str | `Millonarios` | **Sí** | Debe coincidir exactamente con el nombre en `Tabla.csv`. |
| `Equipo Visitante` | str | `Deportivo Cali` | **Sí** | Idem. |

### `Historial_partidos.csv` — resultados reales desde Apertura 2025
Ordenado por `Fecha` real (de más viejo a más nuevo) — es el orden en que se recorre para calcular el Elo, así que importa.

| Columna | Tipo | Ejemplo | ¿La usa la simulación? | Descripción |
|---|---|---|---|---|
| `Fecha` | date `YYYY-MM-DD` | `2026-09-10` | **Sí** | Fecha real en que se jugó. Define el orden en que se procesa el historial para el Elo. |
| `Torneo` | str | `2026-II` | No | `2025-I`, `2025-II`, `2026-I` o `2026-II`. Solo informativa. |
| `Jornada` | int o str | `5` / `"Final vuelta"` | No | Número de fecha (todos-contra-todos) o etiqueta de fase final. Solo informativa. |
| `Equipo Local` | str | `Millonarios` | **Sí** | — |
| `Equipo Visitante` | str | `Deportivo Cali` | **Sí** | — |
| `Goles Local` | int | `2` | **Sí** | Goles reales del local. Alimenta el Elo (quién ganó) y el ataque/defensa (cuántos goles). |
| `Goles Visitante` | int | `1` | **Sí** | Idem, del visitante. |

### `model_params.csv` — parámetros del modelo
| Columna | Tipo | Ejemplo | Descripción |
|---|---|---|---|
| `Parametro` | str | `HomeAdvantage` | Nombre del parámetro: `HomeAdvantage`, `RatingScale`, `DrawBias`, `MinProb` o `K_elo`. |
| `Valor` | float | `130` | Su valor numérico actual. |
| `Origen` | str | `Calibrado con...` | Cómo se obtuvo ese valor — todos están calibrados contra `Historial_partidos.csv`, salvo `MinProb` que es un supuesto (piso de probabilidad). |

## Archivos del repo
- `.gitattributes`: configuración de atributos de Git.
- `Historial_partidos.csv`: ver diccionario arriba. Base del Elo y del modelo de goles.
- `model_params.csv`: ver diccionario arriba.
- `Partidos.csv`: ver diccionario arriba.
- `Tabla.csv`: ver diccionario arriba.
- `actualizar_resultados.py`: script para cargar resultados nuevos (ver "Cómo actualizar resultados de partidos nuevos").
- `Simulacion.ipynb`: notebook principal, corre la simulación Monte Carlo y genera `Resultados.xlsx`.
- `Resultados.ipynb`: notebook que genera `Resultado.png` a partir de `Resultados.xlsx`.
- `Resultados.xlsx`: salida generada por `Simulacion.ipynb`, con dos hojas: `Posiciones` (probabilidad % de cada equipo de terminar en cada una de las 20 posiciones) y `Clasificacion Top 8` (la métrica que realmente responde el objetivo del modelo: probabilidad % de cada equipo de terminar entre los ocho primeros, ya sumada — no hace falta sumarla a mano leyendo el gráfico).
- `Resultado.png`: gráfica final generada por `Resultados.ipynb`.

## Explicación del código
`Simulacion.ipynb`, celda por celda (implementa el "Procedimiento de cálculo" de arriba):

1. **Imports**: `pandas`/`numpy` para tablas, `tqdm` para la barra de progreso, `math`/`random` para el modelo.
2. **`poisson_rv`, `simular_goles`, `simular_temporada`**: el núcleo de una temporada simulada (Etapa 3). `simular_temporada` recibe las probabilidades y los factores de ataque/defensa ya calculados, y devuelve la posición final de cada equipo para esa única iteración.
3. **`validar_datos`, `calcular_elo`, `calcular_ataque_defensa`, `probabilidades_partido`, `calcular_probabilidades_partidos`**: implementan las Etapas 1 y 2 — se ejecutan una sola vez por corrida completa (no en cada una de las 100 000 iteraciones, sería carísimo):
   - `validar_datos` corta la ejecución temprano si un equipo de `Partidos.csv` no existe en `Tabla.csv` (evita un `KeyError` confuso a mitad de la simulación).
   - `calcular_elo` recorre `Historial_partidos.csv` (ya ordenado por `Fecha` real) y devuelve el Elo final de cada equipo.
   - `calcular_ataque_defensa` recorre el mismo historial y devuelve la fuerza ofensiva/defensiva de cada equipo más los promedios de gol de la liga.
   - `probabilidades_partido` convierte una diferencia de Elo en `(P_local, P_empate, P_visitante)`.
   - `calcular_probabilidades_partidos` aplica lo anterior a cada partido de `Partidos.csv`, una sola vez.
4. **`simular_montecarlo`**: corre `simular_temporada` 100 000 veces (con una semilla fija para que sea reproducible) y arma la tabla final de probabilidades por posición (Etapa 3 x 100 000 + agregación final).
5. **Celda principal**: carga los 4 archivos de datos, llama a las funciones anteriores en orden, corre la simulación, calcula `Clasificacion Top 8` (la suma de las posiciones 1 a 8 de cada equipo — la métrica del objetivo del modelo) y exporta ambas a `Resultados.xlsx` en hojas separadas.
6. **Celda de gráfico**: se queda con las posiciones 1 a 8 y arma un gráfico de barras apiladas por equipo (vista rápida dentro del notebook; el gráfico final con estilo lo genera `Resultados.ipynb`).

`Resultados.ipynb` solo lee `Resultados.xlsx` y dibuja la versión final (`Resultado.png`) con estilo de tabla debajo del gráfico.

`actualizar_resultados.py` es el script de mantenimiento descrito arriba — no corre la simulación, solo mantiene los datos de entrada al día.

## Requisitos
- Python 3.13+ (el notebook indica `python 3.13.5`).
- Paquetes: `pandas`, `numpy`, `matplotlib`, `tqdm`, `openpyxl`.

## Notas
- La semilla de la simulación (`SEED` en `Simulacion.ipynb`) está fija en 42 para que la corrida sea reproducible; poné `None` ahí si querés que el resultado varíe en cada ejecución.
- La cantidad de simulaciones se controla con `num_simulaciones` en `Simulacion.ipynb` (por defecto 100000).
- Si el torneo termina la fase de todos-contra-todos y pasa a otra fase (cuadrangulares o playoffs), este simulador deja de aplicar tal cual — habría que adaptar `Partidos.csv`/`Tabla.csv` al formato de esa fase (aunque sus resultados sí deberían seguir sumándose a `Historial_partidos.csv` para que el Elo del torneo siguiente arranque bien informado).
