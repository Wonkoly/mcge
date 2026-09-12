from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

# Formato del folio final por tipo — separado del conteo, porque el
# número visible en cada oficio/constancia real no siempre sigue el mismo
# patrón (ver 'MaestriaGeofisica - Actas, Oficios y Constancias' en el
# vault: los prefijos varían entre "CUCPV/MCG/NNN/AAAA" y "MCG/NNN/AAAA").
FORMATOS = {
    "oficio": "CUCPV/MCG/{folio:03d}/{anio}",
    "constancia": "MCG/{folio:03d}/{anio}",
}


def siguiente_folio(session: Session, tipo_documento: str, anio: int | None = None) -> int:
    """Incremento ATÓMICO en una sola sentencia SQL (INSERT ... ON
    CONFLICT ... RETURNING) — necesario porque dos PCs pueden pedir folio
    del mismo tipo casi al mismo instante (ver Fase 0 / arquitectura de
    dos equipos) y NUNCA deben recibir el mismo número. Hace commit de
    inmediato para que el folio quede reservado aunque el resto de la
    operación (guardar el DocumentoEmitido, etc.) falle después."""
    anio = anio or date.today().year
    resultado = session.execute(
        text(
            """
            INSERT INTO folio_secuencia (tipo_documento, anio, ultimo_folio)
            VALUES (:tipo, :anio, 1)
            ON CONFLICT(tipo_documento, anio) DO UPDATE SET ultimo_folio = ultimo_folio + 1
            RETURNING ultimo_folio
            """
        ),
        {"tipo": tipo_documento, "anio": anio},
    )
    folio = resultado.scalar_one()
    session.commit()
    return folio


def siguiente_folio_formateado(session: Session, tipo_documento: str, categoria: str = "oficio") -> str:
    """`categoria` selecciona el formato ("oficio" -> CUCPV/MCG/NNN/AAAA,
    "constancia" -> MCG/NNN/AAAA). `tipo_documento` es la clave interna de
    conteo (ej. "oficio_lector", "constancia_jurado") — cada tipo lleva su
    propia numeración, no una sola secuencia compartida."""
    anio = date.today().year
    folio = siguiente_folio(session, tipo_documento, anio)
    formato = FORMATOS.get(categoria, FORMATOS["oficio"])
    return formato.format(folio=folio, anio=anio)
