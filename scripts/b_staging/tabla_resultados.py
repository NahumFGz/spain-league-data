"""Extrae la tabla de resultados de cada HTML y la guarda como JSON en data/staging."""

import json
import re
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

CARPETA_RESULTADOS = Path(__file__).resolve().parent.parent.parent / "data" / "a_raw" / "resultados"
CARPETA_STAGING = (
    Path(__file__).resolve().parent.parent.parent / "data" / "b_staging" / "resultados"
)

# Base URL de BDFutbol para completar enlaces relativos (p. ej. árbitros)
BDFUTBOL_BASE_URL = "https://www.bdfutbol.com/es"


def listar_archivos_resultados() -> list[Path]:
    """Devuelve la lista de archivos HTML en la carpeta de resultados."""
    if not CARPETA_RESULTADOS.exists():
        return []
    return sorted(
        (f for f in CARPETA_RESULTADOS.iterdir() if f.suffix.lower() == ".html"),
        key=lambda p: p.name,
    )


def _parse_int(text: str) -> int:
    """Convierte texto a entero; devuelve 0 si está vacío o no es número."""
    s = (text or "").strip()
    return int(s) if s.isdigit() else 0


def _texto_celda(celda) -> str:
    """Extrae y normaliza el texto de una celda (espacios colapsados)."""
    return re.sub(r"\s+", " ", (celda.get_text(strip=True) or "")).strip()


def _id_partido_desde_url(href: str) -> int | None:
    """Extrae el parámetro id de la URL del partido (p. ej. ?id=28200)."""
    if not href or not href.strip():
        return None
    parsed = urlparse(href.strip())
    qs = parse_qs(parsed.query)
    id_val = qs.get("id", [None])[0]
    return int(id_val) if id_val and str(id_val).isdigit() else None


def _url_absoluta_bdfutbol(href: str) -> str:
    """Convierte un href relativo de BDFutbol (p. ej. ../r/r600379.html) a URL absoluta."""
    if not href or not href.strip():
        return ""
    href = href.strip()
    # Quitar prefijos ./ y ../
    while href.startswith("./"):
        href = href[2:]
    while href.startswith("../"):
        href = href[3:]
    if not href:
        return ""
    # La base es https://www.bdfutbol.com/es , el href queda como r/r600379.html
    base = BDFUTBOL_BASE_URL.rstrip("/")
    path = href.lstrip("/")
    return f"{base}/{path}"


def _nombre_equipo(celda) -> str:
    """Extrae el nombre del equipo desde una celda (local o visitante)."""
    enlaces = celda.find_all("a", href=True)
    # En local suele ser el primero; en visitante el primero puede ser el escudo (img)
    candidato = ""
    for a in enlaces:
        if a.find("img"):
            continue
        t = _texto_celda(a)
        if len(t) > len(candidato):
            candidato = t
    return candidato or _texto_celda(celda)


def extraer_tabla_resultados(html_path: Path) -> list[dict] | None:
    """
    Lee un HTML de resultados, localiza la tabla taula_estil-16 y devuelve
    una lista de diccionarios con los datos de cada partido por jornada.
    """
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="replace"), "html.parser")
    table = soup.find("table", class_=lambda c: c and "taula_estil-16" in c)
    if not table:
        return None

    resultado = []
    for row in table.find_all("tr", class_=lambda c: c and "jornadai" in c):
        celdas = row.find_all("td")
        if len(celdas) < 6:
            continue

        jornada = row.get("data-jornada")
        if not jornada:
            continue
        jornada = _parse_int(jornada)

        # Fecha: primera celda (enlace con fecha DD/MM/YYYY que lleva a la ficha del partido)
        fecha_el = celdas[0].find("a") or celdas[0]
        fecha = _texto_celda(fecha_el)
        href_partido = fecha_el.get("href", "").strip() if fecha_el.name == "a" else ""
        id_partido = _id_partido_desde_url(href_partido)
        partido_url = _url_absoluta_bdfutbol(href_partido) or None if href_partido else None

        # Local y visitante: celdas 1 y 3 (primer enlace con nombre de equipo)
        local = _nombre_equipo(celdas[1])
        visitante = _nombre_equipo(celdas[3])

        # Resultado: celda 2, dos divs con class resultat-gols (local, visitante)
        divs_goles = celdas[2].find_all("div", class_=lambda c: c and "resultat-gols" in c)
        goles_local = _parse_int(divs_goles[0].get_text(strip=True)) if len(divs_goles) > 0 else 0
        goles_visitante = (
            _parse_int(divs_goles[1].get_text(strip=True)) if len(divs_goles) > 1 else 0
        )

        # Estadio y árbitro: celdas 4 y 5 (árbitro puede tener enlace con url)
        estadio_el = celdas[4].find("a") or celdas[4]
        arbitro_el = celdas[5].find("a") or celdas[5]
        estadio = _texto_celda(estadio_el)
        arbitro = _texto_celda(arbitro_el)
        href_estadio = estadio_el.get("href", "").strip() if estadio_el.name == "a" else ""
        estadio_url = _url_absoluta_bdfutbol(href_estadio) or None if href_estadio else None
        href_arbitro = arbitro_el.get("href", "").strip() if arbitro_el.name == "a" else ""
        arbitro_url = _url_absoluta_bdfutbol(href_arbitro) or None if href_arbitro else None

        resultado.append(
            {
                "id_partido": id_partido,
                "jornada": jornada,
                "fecha": fecha,
                "partido_url": partido_url,
                "local": local,
                "visitante": visitante,
                "goles_local": goles_local,
                "goles_visitante": goles_visitante,
                "estadio": estadio,
                "estadio_url": estadio_url,
                "arbitro": arbitro,
                "arbitro_url": arbitro_url or None,
            }
        )

    return resultado if resultado else None


def html_a_json(html_path: Path, salida_dir: Path) -> Path | None:
    """
    Procesa un HTML de resultados y guarda el JSON en salida_dir
    con el mismo nombre cambiando .html por .json. Devuelve la ruta del JSON o None.
    """
    datos = extraer_tabla_resultados(html_path)
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
    archivos = listar_archivos_resultados()
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
