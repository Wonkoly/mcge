"""Migración puntual: crea las tablas del taller de plantillas
(plantilla_base, tipo_documento_personalizado) y agrega
tipo_documento_id/datos_json a punto_acta — sin pérdida de datos, las
actas/puntos ya existentes quedan con ambas columnas en NULL (no aplica
a ellos, son de tipo "direccion"/"comite_tutorial"/"otro").

Correr una sola vez: python scripts/migrar_tipos_documento_personalizados.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text

from app.database.session import engine


def main():
    insp = inspect(engine)
    tablas = set(insp.get_table_names())
    columnas_punto = {c["name"] for c in insp.get_columns("punto_acta")}

    with engine.begin() as con:
        if "plantilla_base" not in tablas:
            con.execute(
                text(
                    """
                    CREATE TABLE plantilla_base (
                        categoria VARCHAR(20) PRIMARY KEY,
                        archivo VARCHAR(255)
                    )
                    """
                )
            )
            print("Tabla 'plantilla_base' creada.")

        if "tipo_documento_personalizado" not in tablas:
            con.execute(
                text(
                    """
                    CREATE TABLE tipo_documento_personalizado (
                        id INTEGER PRIMARY KEY,
                        clave VARCHAR(60) UNIQUE NOT NULL,
                        etiqueta VARCHAR(150) NOT NULL,
                        descripcion VARCHAR(500),
                        categoria VARCHAR(20) NOT NULL,
                        cuerpo_texto TEXT,
                        plantilla_archivo VARCHAR(255),
                        estado VARCHAR(20) DEFAULT 'borrador',
                        creado_en DATETIME,
                        actualizado_en DATETIME
                    )
                    """
                )
            )
            print("Tabla 'tipo_documento_personalizado' creada.")

        if "tipo_documento_id" not in columnas_punto:
            con.execute(
                text(
                    "ALTER TABLE punto_acta ADD COLUMN tipo_documento_id INTEGER "
                    "REFERENCES tipo_documento_personalizado(id)"
                )
            )
            print("Columna 'tipo_documento_id' agregada a punto_acta.")

        if "datos_json" not in columnas_punto:
            con.execute(text("ALTER TABLE punto_acta ADD COLUMN datos_json VARCHAR(4000)"))
            print("Columna 'datos_json' agregada a punto_acta.")

    print("Migración completa.")


if __name__ == "__main__":
    main()
