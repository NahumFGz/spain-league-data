"""
Copia cada JSON de clasificación por temporada a data/d_silver/clasificacion.
Origen: data/b_staging/clasificacion
Destino: data/d_silver/clasificacion
"""

import shutil
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    staging_dir = base_dir / "data" / "b_staging" / "clasificacion"
    output_dir = base_dir / "data" / "d_silver" / "clasificacion"

    if not staging_dir.exists():
        raise FileNotFoundError(f"No existe el directorio: {staging_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)

    json_files = list(staging_dir.glob("*.json"))
    for json_path in json_files:
        shutil.copy2(json_path, output_dir / json_path.name)

    print(f"Copiados {len(json_files)} archivos a {output_dir}")


if __name__ == "__main__":
    main()
