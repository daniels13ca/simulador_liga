"""Actualiza Partidos.csv, Tabla.csv y Historial_partidos.csv con resultados
de partidos ya jugados, para no tener que editar los tres archivos a mano
cada vez que se juega una fecha.

Uso (un partido):
    python3 actualizar_resultados.py --local "Millonarios" --visita "Once Caldas" --gl 2 --gv 1

Uso (varios partidos de una fecha, desde un CSV con separador ';'):
    python3 actualizar_resultados.py --csv nuevos_resultados.csv

El CSV de entrada debe tener columnas: Equipo Local;Equipo Visitante;Goles Local;Goles Visitante
(y opcionalmente Fecha en formato YYYY-MM-DD; Torneo; Jornada -- si se omiten,
se toman de la fila correspondiente en Partidos.csv, o de --fecha/--torneo/--jornada).

Que hace, por cada partido:
1. Lo quita de Partidos.csv (ya no esta pendiente). De ahi se toma tambien la
   Fecha real del partido, si no se pasa una explicita.
2. Lo agrega a Historial_partidos.csv y reordena todo el archivo por Fecha
   (para que quede en su lugar cronologico real, no al final -- importante
   porque hay partidos aplazados que se juegan fuera del orden de su fecha
   nominal).
3. Actualiza Puntos/PJ/GF/GC/Diferencia de Goles de ambos equipos en Tabla.csv
   y renumera 'Posicion actual'.

No corre la simulacion: despues de actualizar los datos, ejecuta
Simulacion.ipynb y Resultados.ipynb (ver README.md, seccion "Como correr el
proyecto").
"""
import argparse
import csv

TABLA_PATH = 'Tabla.csv'
PARTIDOS_PATH = 'Partidos.csv'
HISTORIAL_PATH = 'Historial_partidos.csv'


def leer_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f, delimiter=';'))


def escribir_csv(path, filas, columnas):
    with open(path, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=columnas, delimiter=';', lineterminator='\r\n')
        w.writeheader()
        w.writerows(filas)


def aplicar_resultado(partidos, tabla, historial, local, visita, gl, gv, fecha, torneo, jornada):
    # 1) Sacar el partido de Partidos.csv (de ahi sale tambien la fecha/jornada
    #    real si no se pasaron explicitas)
    idx = next((i for i, p in enumerate(partidos)
                if p['Equipo Local'] == local and p['Equipo Visitante'] == visita), None)
    if idx is None:
        raise SystemExit(
            f"No encontre '{local}' vs '{visita}' en {PARTIDOS_PATH}. "
            "Revisa que los nombres coincidan exactamente (mayusculas/tildes incluidas)."
        )
    fila_partido = partidos.pop(idx)
    fecha = fecha or fila_partido.get('Fecha') or ''
    jornada = jornada or (int(fila_partido['Jornada']) if fila_partido.get('Jornada') else None)
    if not fecha:
        raise SystemExit(f"No hay Fecha para '{local}' vs '{visita}' en Partidos.csv; pasa --fecha YYYY-MM-DD.")

    # 2) Agregarlo al historial (se reordena por fecha despues, en main())
    historial.append({
        'Fecha': fecha, 'Torneo': torneo, 'Jornada': jornada,
        'Equipo Local': local, 'Equipo Visitante': visita,
        'Goles Local': gl, 'Goles Visitante': gv,
    })

    # 3) Actualizar Tabla.csv
    fila_local = next(r for r in tabla if r['Equipo'] == local)
    fila_visita = next(r for r in tabla if r['Equipo'] == visita)
    for fila, gf, gc in [(fila_local, gl, gv), (fila_visita, gv, gl)]:
        fila['PJ'] = int(fila['PJ']) + 1
        fila['GF'] = int(fila['GF']) + gf
        fila['GC'] = int(fila['GC']) + gc
        fila['Diferencia de Goles'] = int(fila['GF']) - int(fila['GC'])
    if gl > gv:
        fila_local['Puntos'] = int(fila_local['Puntos']) + 3
    elif gl < gv:
        fila_visita['Puntos'] = int(fila_visita['Puntos']) + 3
    else:
        fila_local['Puntos'] = int(fila_local['Puntos']) + 1
        fila_visita['Puntos'] = int(fila_visita['Puntos']) + 1

    return fecha, torneo, jornada


def renumerar_tabla(tabla):
    tabla.sort(key=lambda r: (-int(r['Puntos']), -int(r['Diferencia de Goles']), -int(r['GF'])))
    for i, fila in enumerate(tabla, start=1):
        fila['Posicion actual'] = i


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--csv', help='CSV con varios partidos (Equipo Local;Equipo Visitante;Goles Local;Goles Visitante[;Fecha;Torneo;Jornada])')
    ap.add_argument('--local', help='Equipo local (un solo partido)')
    ap.add_argument('--visita', help='Equipo visitante (un solo partido)')
    ap.add_argument('--gl', type=int, help='Goles del local')
    ap.add_argument('--gv', type=int, help='Goles del visitante')
    ap.add_argument('--fecha', help='Fecha real del partido, YYYY-MM-DD (por defecto: la que ya tenia en Partidos.csv)')
    ap.add_argument('--torneo', help='Torneo (por defecto: el ultimo que aparece en Historial_partidos.csv)')
    ap.add_argument('--jornada', type=int, help='Jornada (por defecto: la que ya tenia en Partidos.csv)')
    args = ap.parse_args()

    partidos = leer_csv(PARTIDOS_PATH)
    tabla = leer_csv(TABLA_PATH)
    historial = leer_csv(HISTORIAL_PATH)

    torneo_default = args.torneo or historial[-1]['Torneo']

    partidos_a_aplicar = []
    if args.csv:
        for fila in leer_csv(args.csv):
            partidos_a_aplicar.append((
                fila['Equipo Local'], fila['Equipo Visitante'],
                int(fila['Goles Local']), int(fila['Goles Visitante']),
                fila.get('Fecha') or None,
                fila.get('Torneo') or torneo_default,
                int(fila['Jornada']) if fila.get('Jornada') else None,
            ))
    elif args.local and args.visita and args.gl is not None and args.gv is not None:
        partidos_a_aplicar.append((args.local, args.visita, args.gl, args.gv, args.fecha, torneo_default, args.jornada))
    else:
        ap.error('Pasa --csv archivo.csv, o --local --visita --gl --gv para un solo partido.')

    for local, visita, gl, gv, fecha, torneo, jornada in partidos_a_aplicar:
        fecha, torneo, jornada = aplicar_resultado(partidos, tabla, historial, local, visita, gl, gv, fecha, torneo, jornada)
        print(f"OK: {local} {gl}-{gv} {visita} ({fecha}, {torneo}, fecha {jornada})")

    renumerar_tabla(tabla)
    # Reordenar el historial por fecha real (no por orden de llegada): hay
    # partidos aplazados que se juegan fuera del orden de su jornada nominal,
    # y el Elo depende de procesar los partidos en el orden en que realmente
    # ocurrieron.
    historial.sort(key=lambda h: h['Fecha'])

    escribir_csv(PARTIDOS_PATH, partidos, ['Fecha', 'Jornada', 'Equipo Local', 'Equipo Visitante'])
    escribir_csv(TABLA_PATH, tabla, ['Posicion actual', 'Equipo', 'Puntos', 'PJ', 'GF', 'GC', 'Diferencia de Goles'])
    escribir_csv(HISTORIAL_PATH, historial, ['Fecha', 'Torneo', 'Jornada', 'Equipo Local', 'Equipo Visitante', 'Goles Local', 'Goles Visitante'])

    print(f"\nActualizados: {PARTIDOS_PATH}, {TABLA_PATH}, {HISTORIAL_PATH}.")
    print("Ahora corre Simulacion.ipynb y Resultados.ipynb para regenerar los resultados.")


if __name__ == '__main__':
    main()
