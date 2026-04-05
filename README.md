# simulador_liga
Simulador Monte Carlo de posiciones finales del “todos contra todos” del FPC (Liga colombiana), a partir de la tabla actual y los partidos restantes.

**Qué hace**
- Simula resultados aleatorios para los partidos pendientes.
- Calcula la probabilidad de que cada equipo termine en cada posición.
- Exporta los resultados a Excel y genera una gráfica apilada en el notebook.

**Estructura del repo**
- `Simulacion.ipynb`: notebook principal con la simulación.
- `Tabla.csv`: tabla actual de posiciones (separador `;`).
- `Partidos.csv`: partidos restantes (separador `;`).
- `Resultados.xlsx`: salida generada por el notebook.
- `Resultados Ordenados.xlsx`: salida adicional/ordenada (generada manualmente).
- `Data.xlsx`: datos auxiliares o fuente histórica.

**Requisitos**
- Python 3.13+ (el notebook indica `python 3.13.5`).
- Paquetes: `pandas`, `numpy`, `matplotlib`, `tqdm`.

**Cómo usar**
1. Abre `Simulacion.ipynb` en Jupyter o VS Code.
2. Asegúrate de tener `Tabla.csv` y `Partidos.csv` en la raíz del repo.
3. Ejecuta las celdas en orden.
4. Se generará `Resultados.xlsx` y la gráfica de probabilidades.

**Formato de datos**
`Tabla.csv`:
- `Posicion actual` (int)
- `Equipo` (str)
- `Puntos` (int)
- `Diferencia de Goles` (int)

`Partidos.csv`:
- `Equipo Local` (str)
- `Equipo Visitante` (str)

**Notas**
- La simulación usa resultados equiprobables (`local`, `empate`, `visitante`). Si necesitas ponderar por probabilidades reales, hay que modificar la función `simular_temporada` en `Simulacion.ipynb`.
- La cantidad de simulaciones se controla con `num_simulaciones` (por defecto 100000).
