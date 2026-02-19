"""Lee todos los HTML de estadios de b_staging y genera JSON en c_bronze."""

import json
from pathlib import Path

from bs4 import BeautifulSoup

CARPETA_ESTADIOS = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "b_staging"
    / "estadios_arbitros_partidos"
    / "estadios"
)
CARPETA_BRONZE_ESTADIOS = Path(__file__).resolve().parent.parent.parent / "data" / "c_bronze"

# Mapeo etiqueta HTML -> clave JSON. Orden de campos para el JSON final.
CAMPOS_ESTADIO = [
    "nombre_completo",
    "aforo",
    "inauguracion",
    "arquitecto",
    "dimensiones",
    "localidad",
]
ETIQUETA_A_CLAVE = {
    "Nombre completo": "nombre_completo",
    "Aforo": "aforo",
    "Inauguración": "inauguracion",
    "Arquitecto": "arquitecto",
    "Dimensiones": "dimensiones",
    "Localidad": "localidad",
}


def listar_html_estadios() -> list[Path]:
    """Devuelve la lista de archivos .html en la carpeta de estadios, ordenados."""
    if not CARPETA_ESTADIOS.exists():
        return []
    return sorted(f for f in CARPETA_ESTADIOS.iterdir() if f.suffix.lower() == ".html")


def extraer_url_canonica(html: str) -> str:
    """Extrae la URL del <link rel="canonical" href="..."> en el head."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", rel="canonical")
    return link.get("href", "") if link else ""


def extraer_datos_estadio(html: str) -> dict:
    """
    Extrae los campos del hero de la página de estadio.
    Estructura: div.float-left.mr-4.mb-3 > div (etiqueta) + div.font-weight-bold (valor)
    """
    soup = BeautifulSoup(html, "html.parser")
    datos = {}
    for bloque in soup.find_all("div", class_="float-left mr-4 mb-3"):
        divs = bloque.find_all("div", recursive=False)
        if len(divs) < 2:
            continue
        etiqueta = divs[0].get_text(strip=True)
        valor = divs[1].get_text(strip=True)
        clave = ETIQUETA_A_CLAVE.get(etiqueta)
        if clave:
            datos[clave] = valor
    return datos


def main():
    archivos = listar_html_estadios()
    total = len(archivos)
    print(f"Encontrados {total} archivos HTML en {CARPETA_ESTADIOS}")

    CARPETA_BRONZE_ESTADIOS.mkdir(parents=True, exist_ok=True)

    estadios = []
    for i, path in enumerate(archivos, 1):
        id_estadio = path.stem
        print(f"  Procesando {i}/{total}: {id_estadio}")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        datos = extraer_datos_estadio(html)
        url = extraer_url_canonica(html)
        # Mantener todos los campos; vacío si no está en el HTML
        objeto = {"id": id_estadio}
        for campo in CAMPOS_ESTADIO:
            objeto[campo] = datos.get(campo, "")
        objeto["url"] = url if url else ""
        estadios.append(objeto)

    out_path = CARPETA_BRONZE_ESTADIOS / "estadios.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(estadios, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {out_path} ({len(estadios)} estadios)")


if __name__ == "__main__":
    main()
