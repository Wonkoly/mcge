"""Migración puntual: agrega tratamiento/centro_universitario a Profesor
sin perder los datos ya importados, y rellena tratamiento a partir del
texto libre de `grado` con la misma heurística que ya se usaba en
app/documents/generador.py (ahora reemplazada por este campo explícito).

Correr una sola vez: python scripts/migrar_tratamiento_profesor.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.database.session import SessionLocal, engine


def _tratamiento_desde_grado(grado: str | None) -> str | None:
    if not grado:
        return None
    g = grado.lower()
    femenino = "doctora" in g or "maestra" in g
    if "doctor" in g:
        return "Doctora" if femenino else "Doctor"
    if "maestro" in g or "maestra" in g or "m.c" in g or "m. en c" in g:
        return "Maestra" if femenino else "Maestro"
    return None


def main():
    insp = inspect(engine)
    columnas = {c["name"] for c in insp.get_columns("profesor")}

    with engine.begin() as con:
        if "tratamiento" not in columnas:
            con.execute(text("ALTER TABLE profesor ADD COLUMN tratamiento VARCHAR(10)"))
            print("Columna 'tratamiento' agregada.")
        if "centro_universitario" not in columnas:
            con.execute(text("ALTER TABLE profesor ADD COLUMN centro_universitario VARCHAR(150)"))
            print("Columna 'centro_universitario' agregada.")

    session = SessionLocal()
    try:
        from app.models import Profesor

        actualizados = 0
        for p in session.query(Profesor).all():
            cambiado = False
            if not p.tratamiento:
                t = _tratamiento_desde_grado(p.grado)
                if t:
                    p.tratamiento = t
                    cambiado = True
            if not p.centro_universitario:
                p.centro_universitario = "Centro Universitario de la Costa"
                cambiado = True
            if cambiado:
                actualizados += 1
        session.commit()
        print(f"Profesores actualizados: {actualizados}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
