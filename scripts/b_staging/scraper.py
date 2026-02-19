"""Descarga el HTML de cada arbitro, partido y estadio a partir de los JSON de staging.
Lee arbitros.json, partidos.json y estadios.json, hace GET a cada url y guarda
el HTML en carpetas arbitros/, partidos/ y estadios/ con nombre {id}.html."""

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock

import requests
from tqdm import tqdm

NUM_WORKERS = 10
DELAY_SEC = 0.1  # pausa entre peticiones por worker (0 = sin pausa)

# Script en scripts/b_staging/scraper.py -> parent=scripts/b_staging, parent.parent=raíz repo
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
BASE = PROJECT_ROOT / "data" / "b_staging" / "estadios_arbitros_partidos"

ARBITROS_JSON = BASE / "arbitros.json"
PARTIDOS_JSON = BASE / "partidos.json"
ESTADIOS_JSON = BASE / "estadios.json"

DIR_ARBITROS = BASE / "arbitros"
DIR_PARTIDOS = BASE / "partidos"
DIR_ESTADIOS = BASE / "estadios"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
TIMEOUT = 30


def _descargar_uno(args):
    """Descarga una URL y guarda el HTML en out_file. Retorna (id_str, exito, error_msg)."""
    url, id_str, out_file = args
    if DELAY_SEC > 0:
        time.sleep(DELAY_SEC)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        out_file.write_text(resp.text, encoding="utf-8")
        return (id_str, True, None)
    except requests.RequestException as e:
        return (id_str, False, str(e))


def descargar_lista(archivo_json, dir_salida, nombre_lista):
    """Carga un JSON de lista, descarga cada url en paralelo y guarda {id}.html en dir_salida."""
    if not archivo_json.exists():
        print(f"No se encuentra {archivo_json}")
        return 0, 0

    dir_salida.mkdir(parents=True, exist_ok=True)

    with open(archivo_json, encoding="utf-8") as f:
        items = json.load(f)

    total = len(items)
    # Solo items que faltan por descargar (recomprobamos exists por si hay concurrencia)
    pendientes = []
    ya_existentes = 0
    for item in items:
        url = item.get("url")
        id_val = item.get("id")
        if url is None or id_val is None:
            continue
        id_str = str(id_val)
        out_file = dir_salida / f"{id_str}.html"
        if out_file.exists():
            ya_existentes += 1
        else:
            pendientes.append((url, id_str, out_file))

    if not pendientes:
        print(f"  {nombre_lista}: todos ya existían ({ya_existentes}/{total})", flush=True)
        return ya_existentes, total

    lock = Lock()
    errores = []

    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(_descargar_uno, p): p for p in pendientes}
        with tqdm(
            total=len(pendientes),
            desc=nombre_lista,
            unit="url",
            leave=True,
        ) as pbar:
            for fut in as_completed(futures):
                id_str, exito, err = fut.result()
                with lock:
                    if not exito:
                        errores.append((id_str, err))
                        tqdm.write(f"  {nombre_lista} id={id_str}: ERROR {err}")
                pbar.update(1)

    ok = ya_existentes + len(pendientes) - len(errores)
    print(
        f"  {nombre_lista}: Hecho {ok}/{total}" + (f" ({len(errores)} errores)" if errores else ""),
        flush=True,
    )
    return ok, total


def main():
    # Conteo de elementos en cada JSON
    conteos = []
    for nombre, path in [
        ("arbitros", ARBITROS_JSON),
        ("partidos", PARTIDOS_JSON),
        ("estadios", ESTADIOS_JSON),
    ]:
        n = len(json.loads(path.read_text(encoding="utf-8"))) if path.exists() else 0
        conteos.append((nombre, n))
    print("Conteo en JSON: ", end="")
    print(", ".join(f"{nombre}={n}" for nombre, n in conteos), end=".\n\n")

    print("Estadios:")
    ok_e, total_e = descargar_lista(ESTADIOS_JSON, DIR_ESTADIOS, "estadios")
    print(f"  Hecho: {ok_e}/{total_e}\n")

    print("Arbitros:")
    ok_a, total_a = descargar_lista(ARBITROS_JSON, DIR_ARBITROS, "arbitros")
    print(f"  Hecho: {ok_a}/{total_a}\n")

    print("Partidos:")
    ok_p, total_p = descargar_lista(PARTIDOS_JSON, DIR_PARTIDOS, "partidos")
    print(f"  Hecho: {ok_p}/{total_p}\n")

    print(
        f"Resumen: arbitros {ok_a}/{total_a}, partidos {ok_p}/{total_p}, estadios {ok_e}/{total_e}."
    )


if __name__ == "__main__":
    main()
