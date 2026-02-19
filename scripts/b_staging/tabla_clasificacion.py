"""Extrae la tabla de clasificación de cada HTML y la guarda como JSON en data/staging."""

import json
import re
from pathlib import Path

from bs4 import BeautifulSoup

CARPETA_CLASIFICACION = (
    Path(__file__).resolve().parent.parent.parent / "data" / "a_raw" / "clasificacion"
)
CARPETA_STAGING = (
    Path(__file__).resolve().parent.parent.parent / "data" / "b_staging" / "clasificacion"
)


def listar_archivos_clasificacion() -> list[Path]:
    """Devuelve la lista de archivos HTML en la carpeta de clasificación."""
    if not CARPETA_CLASIFICACION.exists():
        return []
    return sorted(
        (f for f in CARPETA_CLASIFICACION.iterdir() if f.suffix.lower() == ".html"),
        key=lambda p: p.name,
    )


def _parse_int(text: str) -> int:
    """Convierte texto a entero; devuelve 0 si está vacío o no es número."""
    s = (text or "").strip()
    return int(s) if s.isdigit() else 0


def extraer_tabla_clasificacion(html_path: Path) -> list[dict] | None:
    """
    Lee un HTML de clasificación, localiza la tabla #classific y devuelve
    una lista de diccionarios con los datos de cada equipo.
    """
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    table = soup.find("table", id="classific")
    if not table:
        return None

    filas_datos = table.find_all("tr", attrs={"data-ideq": True})
    resultado = []

    for row in filas_datos:
        celdas = row.find_all("td")
        if len(celdas) < 13:
            continue

        # Posición: segunda celda, puede ser "1", "10", etc. (a veces con img)
        pos_text = celdas[1].get_text(strip=True)
        pos_match = re.search(r"\d+", pos_text)
        posicion = int(pos_match.group()) if pos_match else 0

        # Equipo: cuarta celda, enlace
        enlace = celdas[3].find("a")
        equipo = enlace.get_text(strip=True) if enlace else celdas[3].get_text(strip=True)
        equipo = re.sub(r"\s+", " ", equipo).strip()

        # IDEQ: atributo data-ideq
        ideq = row.get("data-ideq", "")

        resultado.append(
            {
                "posicion": posicion,
                "ideq": ideq,
                "equipo": equipo,
                "pts": _parse_int(celdas[4].get_text(strip=True)),
                "pj": _parse_int(celdas[5].get_text(strip=True)),
                "pg": _parse_int(celdas[6].get_text(strip=True)),
                "pe": _parse_int(celdas[7].get_text(strip=True)),
                "pp": _parse_int(celdas[8].get_text(strip=True)),
                "gf": _parse_int(celdas[9].get_text(strip=True)),
                "gc": _parse_int(celdas[10].get_text(strip=True)),
                "ta": _parse_int(celdas[11].get_text(strip=True)),
                "tr": _parse_int(celdas[12].get_text(strip=True)),
            }
        )

    return resultado


def html_a_json(html_path: Path, salida_dir: Path) -> Path | None:
    """
    Procesa un HTML de clasificación y guarda el JSON en salida_dir
    con el mismo nombre cambiando .html por .json. Devuelve la ruta del JSON o None.
    """
    datos = extraer_tabla_clasificacion(html_path)
    if datos is None:
        return None

    nombre_json = html_path.stem + ".json"
    json_path = salida_dir / nombre_json

    salida_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return json_path


if __name__ == "__main__":
    archivos = listar_archivos_clasificacion()
    CARPETA_STAGING.mkdir(parents=True, exist_ok=True)

    procesados = 0
    errores = []

    for html_path in archivos:
        resultado = html_a_json(html_path, CARPETA_STAGING)
        if resultado:
            procesados += 1
            print(f"  {html_path.name} -> {resultado.name}")
        else:
            errores.append(html_path.name)

    print(f"\nProcesados: {procesados}/{len(archivos)}")
    if errores:
        print(f"No se encontró tabla en: {', '.join(errores)}")
