#!/usr/bin/env python3
"""
Descarga el HTML de las páginas de clasificación por temporada.
Lee scripts/temporadas.json y guarda cada HTML en data/raw/clasificacion/{temporada}.html
"""

import json
import sys
from pathlib import Path

import requests

SCRIPT_DIR = Path(__file__).resolve().parent  # scripts/raw/
PROJECT_ROOT = SCRIPT_DIR.parent.parent  # raíz del repo
TEMPORADAS_JSON = SCRIPT_DIR.parent / "temporadas.json"  # scripts/temporadas.json
OUTPUT_DIR = PROJECT_ROOT / "data" / "a_raw" / "clasificacion"

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}


def main():
    if not TEMPORADAS_JSON.exists():
        print(f"No se encuentra {TEMPORADAS_JSON}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(TEMPORADAS_JSON, encoding="utf-8") as f:
        temporadas = json.load(f)

    total = len(temporadas)
    ok = 0
    for i, item in enumerate(temporadas, 1):
        temporada = item.get("temporada")
        url = item.get("url_clasificacion")
        if not url:
            print(f"  [{i}/{total}] {temporada}: sin url_clasificacion, omitido")
            continue

        out_file = OUTPUT_DIR / f"{temporada}.html"
        if out_file.exists():
            print(f"  [{i}/{total}] {temporada}: ya existe, omitido")
            ok += 1
            continue

        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            out_file.write_text(resp.text, encoding="utf-8")
            print(f"  [{i}/{total}] {temporada}: guardado")
            ok += 1
        except requests.RequestException as e:
            print(f"  [{i}/{total}] {temporada}: ERROR {e}")

    print(f"\nHecho: {ok}/{total} temporadas.")


if __name__ == "__main__":
    main()
