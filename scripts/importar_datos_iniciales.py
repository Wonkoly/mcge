"""Punto de entrada para poblar data/maestria.db desde cero: crea el
esquema, siembra catálogos + núcleo académico, e importa el Excel actual.

Uso: python scripts/importar_datos_iniciales.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.session import SessionLocal, init_db
from app.importers.excel_importer import ImportadorExcel
from app.importers.seed_data import seed_lies, seed_nucleo_academico, seed_status

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "Docs" / "Alumnos Resumen Academico 2026 B.xlsx"


def main():
    print("1/3 — Creando esquema (data/maestria.db)...")
    init_db()

    session = SessionLocal()
    try:
        print("2/3 — Sembrando catálogos (Status, LIES) y núcleo académico...")
        seed_status(session)
        seed_lies(session)
        seed_nucleo_academico(session)
        session.commit()

        print(f"3/3 — Importando alumnos desde {EXCEL_PATH.name}...")
        importador = ImportadorExcel(session)
        resultado = importador.importar(EXCEL_PATH)
        session.commit()

        print()
        print(f"Alumnos creados:        {resultado.alumnos_creados}")
        print(f"Alumnos actualizados:   {resultado.alumnos_actualizados}")
        print(f"Profesores nuevos:      {resultado.profesores_creados} (fuera del núcleo académico de 25)")
        print(f"Direcciones creadas:    {resultado.direcciones_creadas}")
        if resultado.advertencias:
            print(f"\nAdvertencias ({len(resultado.advertencias)}):")
            for a in resultado.advertencias:
                print(f"  - {a}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
