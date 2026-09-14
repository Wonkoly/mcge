"""Migración puntual: agrega los campos estructurados a PuntoActa (tipo,
alumno_id, profesor_id, rol, ciclo, direccion_id, comite_tutorial_id) y
crea la tabla punto_acta_miembro — para que un punto de Acta pueda
disparar el alta/cambio real de Dirección o Comité Tutorial en vez de ser
solo texto libre (ver app/services/acta_service.py).

No hay datos que perder: los puntos ya existentes quedan con
tipo="otro" (default), que es exactamente su comportamiento actual.

Correr una sola vez: python scripts/migrar_puntos_acta_estructurados.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.database.session import engine


def main():
    insp = inspect(engine)
    columnas = {c["name"] for c in insp.get_columns("punto_acta")}
    tablas = set(insp.get_table_names())

    with engine.begin() as con:
        if "tipo" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN tipo VARCHAR(30) DEFAULT 'otro'"))
            con.execute(text("UPDATE punto_acta SET tipo = 'otro' WHERE tipo IS NULL"))
            print("Columna 'tipo' agregada (puntos existentes marcados como 'otro').")
        if "alumno_id" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN alumno_id INTEGER REFERENCES alumno(id)"))
            print("Columna 'alumno_id' agregada.")
        if "profesor_id" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN profesor_id INTEGER REFERENCES profesor(id)"))
            print("Columna 'profesor_id' agregada.")
        if "rol" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN rol VARCHAR(12)"))
            print("Columna 'rol' agregada.")
        if "ciclo" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN ciclo VARCHAR(10)"))
            print("Columna 'ciclo' agregada.")
        if "direccion_id" not in columnas:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN direccion_id INTEGER REFERENCES direccion(id)"))
            print("Columna 'direccion_id' agregada.")
        if "comite_tutorial_id" not in columnas:
            con.execute(
                text("ALTER TABLE punto_acta ADD COLUMN comite_tutorial_id INTEGER REFERENCES comite_tutorial(id)")
            )
            print("Columna 'comite_tutorial_id' agregada.")

        if "punto_acta_miembro" not in tablas:
            con.execute(
                text(
                    """
                    CREATE TABLE punto_acta_miembro (
                        id INTEGER PRIMARY KEY,
                        punto_id INTEGER NOT NULL REFERENCES punto_acta(id),
                        profesor_id INTEGER NOT NULL REFERENCES profesor(id)
                    )
                    """
                )
            )
            print("Tabla 'punto_acta_miembro' creada.")

    print("Migración completa.")


if __name__ == "__main__":
    main()
