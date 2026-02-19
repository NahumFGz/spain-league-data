"""
Unifica datos de resultados por jornada añadiendo estadio_detalle, arbitro_detalle y partido_detalle
desde los JSON de bronze (estadios, arbitros, partidos).
"""
import json
from pathlib import Path

# Rutas base
BASE = Path(__file__).resolve().parents[2]
STAGING_RESULTADOS = BASE / "data" / "b_staging" / "resultados"
BRONZE_ESTADIOS = BASE / "data" / "c_bronze" / "estadios.json"
BRONZE_ARBITROS = BASE / "data" / "c_bronze" / "arbitros.json"
BRONZE_PARTIDOS_DIR = BASE / "data" / "c_bronze" / "partidos"
OUTPUT_DIR = BASE / "data" / "d_silver" / "resultados_jornada"


def cargar_indice_por_id(ruta_json: Path) -> dict:
    """Carga un JSON array y devuelve un diccionario id -> objeto."""
    with open(ruta_json, encoding="utf-8") as f:
        datos = json.load(f)
    return {str(item["id"]): item for item in datos}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    todos = sorted(STAGING_RESULTADOS.glob("*.json"))
    ya_guardados = {p.name for p in OUTPUT_DIR.glob("*.json")}
    pendientes = [p for p in todos if p.name not in ya_guardados]
    total = len(todos)
    procesados_antes = len(ya_guardados)

    print(f"Resultados: {total} temporadas en origen.")
    print(f"En destino ya hay: {procesados_antes} archivos.")
    print(f"Pendientes de unificar: {len(pendientes)}.")
    if not pendientes:
        print("Nada que procesar. Todos los JSON ya están unificados.")
        return

    estadios = cargar_indice_por_id(BRONZE_ESTADIOS)
    arbitros = cargar_indice_por_id(BRONZE_ARBITROS)

    for path_resultado in pendientes:
        with open(path_resultado, encoding="utf-8") as f:
            partidos = json.load(f)

        for p in partidos:
            # Estadio: id puede ser int o string (ej. "6b")
            id_estadio = p.get("id_estadio")
            if id_estadio is not None:
                key_estadio = str(id_estadio).strip()
                p["estadio_detalle"] = estadios.get(key_estadio)

            # Árbitro
            id_arbitro = p.get("id_arbitro")
            if id_arbitro is not None:
                key_arbitro = str(id_arbitro).strip()
                p["arbitro_detalle"] = arbitros.get(key_arbitro)

            # Partido: archivo partidos/{id_partido}.json
            id_partido = p.get("id_partido")
            if id_partido is not None:
                path_partido = BRONZE_PARTIDOS_DIR / f"{id_partido}.json"
                if path_partido.exists():
                    with open(path_partido, encoding="utf-8") as fp:
                        p["partido_detalle"] = json.load(fp)
                else:
                    p["partido_detalle"] = None

        out_path = OUTPUT_DIR / path_resultado.name
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(partidos, f, ensure_ascii=False, indent=2)

        print(f"Guardado: {out_path.name} ({len(partidos)} partidos)")


if __name__ == "__main__":
    main()
