# simulador_liga
Simulador Monte Carlo de posiciones finales del todos contra todos del FPC (Liga colombiana), a partir de la tabla actual y los partidos restantes.

**Qué hace**
- Simula resultados aleatorios para los partidos pendientes.
- Calcula la probabilidad de que cada equipo termine en cada posición.
- Exporta los resultados a Excel y genera una gráfica apilada.

**Archivos del repo**
- `.gitattributes`: configuración de atributos de Git.
- `Data.xlsx`: datos auxiliares o fuente histórica.
- `Partidos.csv`: partidos restantes (separador `;`).
- `Resultado.png`: gráfica final generada por `Resultados.ipynb`.
- `Resultados.ipynb`: notebook que genera la imagen a partir de `Resultados.xlsx`.
- `Resultados.xlsx`: salida generada por `Simulacion.ipynb`.
- `Simulacion.ipynb`: notebook principal con la simulación Monte Carlo.
- `Tabla.csv`: tabla actual de posiciones (separador `;`).

**Requisitos**
- Python 3.13+ (el notebook indica `python 3.13.5`).
- Paquetes: `pandas`, `numpy`, `matplotlib`, `tqdm`.

**Cómo usar**
1. Abre `Simulacion.ipynb` en Jupyter o VS Code y ejecuta todas las celdas.
2. Se generará `Resultados.xlsx`.
3. Abre `Resultados.ipynb` y ejecuta las celdas para crear `Resultado.png`.

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
- La simulación usa resultados equiprobables (`local`, `empate`, `visitante`). Si necesitas ponderar por probabilidades reales, modifica la función `simular_temporada` en `Simulacion.ipynb`.
- La cantidad de simulaciones se controla con `num_simulaciones` (por defecto 100000).