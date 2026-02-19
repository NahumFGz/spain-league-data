"""Lee todos los HTML de árbitros de b_staging y genera JSON en c_bronze."""

import json
from pathlib import Path

from bs4 import BeautifulSoup

CARPETA_ARBITROS = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "b_staging"
    / "estadios_arbitros_partidos"
    / "arbitros"
)
CARPETA_BRONZE = Path(__file__).resolve().parent.parent.parent / "data" / "c_bronze"

# Mapeo etiqueta HTML -> clave JSON. Orden de campos para el JSON final.
CAMPOS_ARBITRO = [
    "nombre_completo",
    "fecha_nacimiento",
    "fecha_fallecimiento",
    "lugar_nacimiento",
    "pais_nacimiento",
]
ETIQUETA_A_CLAVE = {
    "Nombre completo": "nombre_completo",
    "Fecha de nacimiento": "fecha_nacimiento",
    "Fecha de fallecimiento": "fecha_fallecimiento",
    "Lugar de nacimiento": "lugar_nacimiento",
    "País de nacimiento": "pais_nacimiento",
}


def listar_html_arbitros() -> list[Path]:
    """Devuelve la lista de archivos .html en la carpeta de árbitros, ordenados."""
    if not CARPETA_ARBITROS.exists():
        return []
    return sorted(f for f in CARPETA_ARBITROS.iterdir() if f.suffix.lower() == ".html")


def extraer_url_canonica(html: str) -> str:
    """Extrae la URL del <link rel="canonical" href="..."> en el head."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.find("link", rel="canonical")
    return link.get("href", "") if link else ""


def extraer_datos_arbitro(html: str) -> dict:
    """
    Extrae los campos del hero de la página de árbitro.
    Estructura: div.float-left.mr-4.mb-0.mb-md-3 > div (etiqueta) + div.font-weight-bold (valor)
    """
    soup = BeautifulSoup(html, "html.parser")
    datos = {}
    for bloque in soup.find_all("div", class_="float-left mr-4 mb-0 mb-md-3"):
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
    archivos = listar_html_arbitros()
    total = len(archivos)
    print(f"Encontrados {total} archivos HTML en {CARPETA_ARBITROS}")

    CARPETA_BRONZE.mkdir(parents=True, exist_ok=True)

    arbitros = []
    for i, path in enumerate(archivos, 1):
        id_arbitro = path.stem
        print(f"  Procesando {i}/{total}: {id_arbitro}")
        with open(path, encoding="utf-8") as f:
            html = f.read()
        datos = extraer_datos_arbitro(html)
        url = extraer_url_canonica(html)
        objeto = {"id": id_arbitro}
        for campo in CAMPOS_ARBITRO:
            objeto[campo] = datos.get(campo, "")
        objeto["url"] = url if url else ""
        arbitros.append(objeto)

    out_path = CARPETA_BRONZE / "arbitros.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(arbitros, f, ensure_ascii=False, indent=2)
    print(f"Guardado: {out_path} ({len(arbitros)} árbitros)")


if __name__ == "__main__":
    main()
