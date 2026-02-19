"""Lee todos los JSON de resultados, extrae partido_url, estadio_url y arbitro_url
únicos y guarda partidos.json, estadios.json y arbitros.json en staging."""

import json
from pathlib import Path

CARPETA_RESULTADOS = (
    Path(__file__).resolve().parent.parent.parent / "data" / "b_staging" / "resultados"
)
CARPETA_ESTADIOS_ARBITROS_PARTIDOS = (
    Path(__file__).resolve().parent.parent.parent
    / "data"
    / "b_staging"
    / "estadios_arbitros_partidos"
)


def _id_desde_url(url):
    """Extrae el id del final de la URL (ej: .../r10180.html -> r10180)."""
    if not url:
        return ""
    nombre_archivo = url.rstrip("/").split("/")[-1]
    return (
        nombre_archivo.removesuffix(".html") if nombre_archivo.endswith(".html") else nombre_archivo
    )


def main():
    partidos_por_url = {}  # url -> id_partido (None si no existe en el JSON)
    estadios_por_url = {}  # url -> nombre
    arbitros_por_url = {}  # url -> nombre

    for path in sorted(CARPETA_RESULTADOS.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            partidos = json.load(f)
        for p in partidos:
            if p.get("partido_url"):
                url = p["partido_url"]
                # Mantener id_partido si ya había uno; si no, usar el actual (puede ser None)
                if url not in partidos_por_url or p.get("id_partido") is not None:
                    partidos_por_url[url] = p.get("id_partido")
            if p.get("estadio_url"):
                estadios_por_url.setdefault(p["estadio_url"], p.get("estadio") or "")
            if p.get("arbitro_url"):
                arbitros_por_url.setdefault(p["arbitro_url"], p.get("arbitro") or "")

    CARPETA_ESTADIOS_ARBITROS_PARTIDOS.mkdir(parents=True, exist_ok=True)

    partidos_data = [
        {"id": id_partido, "url": url}
        for url, id_partido in sorted(
            partidos_por_url.items(), key=lambda x: (x[0] or "", x[0] or "")
        )
    ]
    estadios_data = [
        {"id": _id_desde_url(url), "nombre": nombre, "url": url}
        for url, nombre in sorted(estadios_por_url.items(), key=lambda x: (x[0] or "", x[1]))
    ]
    arbitros_data = [
        {"id": _id_desde_url(url), "nombre": nombre, "url": url}
        for url, nombre in sorted(arbitros_por_url.items(), key=lambda x: (x[0] or "", x[1]))
    ]

    with open(
        CARPETA_ESTADIOS_ARBITROS_PARTIDOS / "partidos.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(partidos_data, f, ensure_ascii=False, indent=2)

    with open(
        CARPETA_ESTADIOS_ARBITROS_PARTIDOS / "estadios.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(estadios_data, f, ensure_ascii=False, indent=2)

    with open(
        CARPETA_ESTADIOS_ARBITROS_PARTIDOS / "arbitros.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(arbitros_data, f, ensure_ascii=False, indent=2)

    print(
        f"Guardados: {len(partidos_data)} partidos, "
        f"{len(estadios_data)} estadios, {len(arbitros_data)} árbitros"
    )


if __name__ == "__main__":
    main()
