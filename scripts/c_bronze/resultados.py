"""Lee todos los HTML de partidos de b_staging y genera un JSON por partido en c_bronze."""

import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

CARPETA_PARTIDOS = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "b_staging"
    / "estadios_arbitros_partidos"
    / "partidos"
)
CARPETA_BRONZE_PARTIDOS = (
    Path(__file__).resolve().parent.parent.parent / "data" / "c_bronze" / "partidos"
)
BASE_URL_BDFUTBOL = "https://www.bdfutbol.com/es"


def href_a_url_absoluta(href: str) -> str:
    """Convierte href relativo (ej. ../e/e87.html) a URL absoluta bdfutbol."""
    if not href or not href.strip():
        return ""
    href = href.strip()
    if href.startswith("../"):
        return f"{BASE_URL_BDFUTBOL}/{href[3:]}"
    if href.startswith("/"):
        return f"https://www.bdfutbol.com{href}"
    return href


def id_desde_url_equipo(url: str) -> str:
    """Extrae el id del equipo desde la URL: último segmento del path sin .html (ej. e87, e7)."""
    if not url or not url.strip():
        return ""
    path = urlparse(url.strip()).path.rstrip("/")
    if not path:
        return ""
    nombre_archivo = path.split("/")[-1]
    if nombre_archivo.lower().endswith(".html"):
        return nombre_archivo[: -5]
    return nombre_archivo


def listar_html_partidos() -> list[Path]:
    """Devuelve la lista de archivos .html en la carpeta de partidos, ordenados."""
    if not CARPETA_PARTIDOS.exists():
        return []
    return sorted(
        f for f in CARPETA_PARTIDOS.iterdir() if f.suffix.lower() == ".html"
    )


def extraer_id_y_url_canonica(html: str) -> tuple[str, str]:
    """Extrae id (query id=) y URL del <link rel="canonical" href="...">."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", rel="canonical")
    if not link:
        return "", ""
    url = link.get("href", "")
    if not url:
        return "", ""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    id_partido = params.get("id", [""])[0]
    return id_partido, url


def extraer_resultado_partido(html: str) -> dict:
    """
    Extrae equipo_local, equipo_visitante, resultado_local, resultado_visitante
    del bloque .d-none.d-md-block que contiene la fila con .resultat-partit y .partit-equip.
    """
    soup = BeautifulSoup(html, "html.parser")
    out = {
        "equipo_local": "",
        "equipo_visitante": "",
        "url_equipo_local": "",
        "url_equipo_visitante": "",
        "id_equipo_local": "",
        "id_equipo_visitante": "",
        "resultado_local": None,
        "resultado_visitante": None,
    }
    # Bloque desktop: una fila con partit-equip, resultat-partit, resultat-partit, partit-equip
    bloque = soup.find("div", class_="d-none d-md-block")
    if not bloque:
        return out
    row = bloque.find("div", class_="row", recursive=True)
    if not row:
        return out
    equipos = row.find_all("div", class_=lambda c: c and "partit-equip" in c)
    resultados = row.find_all("div", class_=lambda c: c and "resultat-partit" in c)
    if len(equipos) >= 2:
        a_local = equipos[0].find("a")
        a_visitante = equipos[1].find("a")
        if a_local:
            out["equipo_local"] = a_local.get_text(strip=True)
            out["url_equipo_local"] = href_a_url_absoluta(a_local.get("href", ""))
            out["id_equipo_local"] = id_desde_url_equipo(out["url_equipo_local"])
        if a_visitante:
            out["equipo_visitante"] = a_visitante.get_text(strip=True)
            out["url_equipo_visitante"] = href_a_url_absoluta(a_visitante.get("href", ""))
            out["id_equipo_visitante"] = id_desde_url_equipo(out["url_equipo_visitante"])
    if len(resultados) >= 2:
        try:
            out["resultado_local"] = int(resultados[0].get_text(strip=True))
        except (ValueError, TypeError):
            pass
        try:
            out["resultado_visitante"] = int(resultados[1].get_text(strip=True))
        except (ValueError, TypeError):
            pass
    return out


def procesar_html_partido(html: str) -> dict:
    """Construye el objeto JSON del partido: id_partido, url_partido y campos de resultado."""
    id_partido, url_partido = extraer_id_y_url_canonica(html)
    datos = extraer_resultado_partido(html)
    return {
        "id_partido": id_partido,
        "url_partido": url_partido,
        "equipo_local": datos["equipo_local"],
        "equipo_visitante": datos["equipo_visitante"],
        "url_equipo_local": datos["url_equipo_local"],
        "url_equipo_visitante": datos["url_equipo_visitante"],
        "id_equipo_local": datos["id_equipo_local"],
        "id_equipo_visitante": datos["id_equipo_visitante"],
        "resultado_local": datos["resultado_local"],
        "resultado_visitante": datos["resultado_visitante"],
    }


def main():
    archivos = listar_html_partidos()
    total = len(archivos)
    print(f"Encontrados {total} archivos HTML en {CARPETA_PARTIDOS}")

    CARPETA_BRONZE_PARTIDOS.mkdir(parents=True, exist_ok=True)

    for i, path in enumerate(archivos, 1):
        nombre_base = path.stem
        print(f"  Procesando {i}/{total}: {nombre_base}", end="\r")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        objeto = procesar_html_partido(html)
        out_path = CARPETA_BRONZE_PARTIDOS / f"{nombre_base}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(objeto, f, ensure_ascii=False, indent=2)

    print(f"Guardados {total} JSON en {CARPETA_BRONZE_PARTIDOS}")


if __name__ == "__main__":
    main()
