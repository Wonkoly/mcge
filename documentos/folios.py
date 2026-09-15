"""Puerto de app/services/folio_service.py. Incremento ATÓMICO en una sola
sentencia SQL (INSERT ... ON CONFLICT ... RETURNING) — necesario porque dos
PCs pueden pedir folio del mismo tipo casi al mismo instante y NUNCA deben
recibir el mismo número. Se usa SQL crudo sobre la tabla folio_secuencia
(clave compuesta tipo_documento+anio, sin modelo Django porque no hace
falta ORM para este único acceso atómico)."""

from datetime import date

from django.db import connection, transaction

# Nombres legibles — mismas claves que folio_service.py en Flask.
TIPOS_DOCUMENTO = {
    "oficio_direccion": "Oficio de asignación de Director/Codirector",
    "constancia_direccion": "Constancia de Director/Codirector",
    "oficio_comite_tutorial": "Oficio de comité tutorial",
    "constancia_lector": "Constancia de Lector",
    "constancia_jurado": "Constancia de Sinodal/Jurado",
    "oficio_invitacion_jurado": "Oficio de invitación a Sinodal/Jurado",
    "constancia_evaluador_aspirantes": "Constancia de evaluador de aspirantes",
    "oficio_asentamiento_creditos": "Oficio de asentamiento de créditos",
    "oficio_permiso_municipio": "Oficio de permiso a municipio",
}

FORMATOS = {
    "oficio": "CUCPV/MCG/{folio:03d}/{anio}",
    "constancia": "MCG/{folio:03d}/{anio}",
}


@transaction.atomic
def siguiente_folio(tipo_documento: str, anio: int | None = None) -> int:
    anio = anio or date.today().year
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO folio_secuencia (tipo_documento, anio, ultimo_folio)
            VALUES (%s, %s, 1)
            ON CONFLICT(tipo_documento, anio) DO UPDATE SET ultimo_folio = ultimo_folio + 1
            RETURNING ultimo_folio
            """,
            [tipo_documento, anio],
        )
        return cursor.fetchone()[0]


def siguiente_folio_formateado(tipo_documento: str, categoria: str = "oficio") -> str:
    anio = date.today().year
    folio = siguiente_folio(tipo_documento, anio)
    formato = FORMATOS.get(categoria, FORMATOS["oficio"])
    return formato.format(folio=folio, anio=anio)


def folio_sugerido(tipo_documento: str, anio: int | None = None) -> int:
    """El SIGUIENTE número, sin consumirlo — para precargar el prompt del
    botón "Generar oficio". No escribe nada; el número real que se use lo
    fija `usar_folio()` cuando el usuario confirma (o corrige) el número."""
    anio = anio or date.today().year
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT ultimo_folio FROM folio_secuencia WHERE tipo_documento = %s AND anio = %s",
            [tipo_documento, anio],
        )
        fila = cursor.fetchone()
    return (fila[0] if fila else 0) + 1


@transaction.atomic
def usar_folio(tipo_documento: str, numero: int, anio: int | None = None) -> int:
    """Fija el folio que el usuario escribió/confirmó en el prompt del
    botón — deja `ultimo_folio` en al menos ese valor (nunca lo baja, por si
    dos personas generan oficios casi al mismo tiempo y una escribe un
    número menor al que ya se usó)."""
    anio = anio or date.today().year
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO folio_secuencia (tipo_documento, anio, ultimo_folio)
            VALUES (%s, %s, %s)
            ON CONFLICT(tipo_documento, anio) DO UPDATE SET
                ultimo_folio = MAX(folio_secuencia.ultimo_folio, excluded.ultimo_folio)
            """,
            [tipo_documento, anio, numero],
        )
    return numero
