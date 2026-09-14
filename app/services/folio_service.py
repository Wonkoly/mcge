from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import FolioSecuencia

# Nombres legibles para la pantalla de Configuración — mismas claves que
# usa app/documents/generador.py al pedir folio.
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


def listar_folios(session: Session) -> list[FolioSecuencia]:
    """Todo el historial de contadores (tipo + año), para la pantalla de
    Configuración — incluye los tipos que ya tienen folios pedidos, más los
    tipos conocidos que todavía no se han usado este año (para poder
    fijarles un punto de partida antes del primer documento real)."""
    filas = {
        (f.tipo_documento, f.anio): f
        for f in session.query(FolioSecuencia).all()
    }
    anio_actual = date.today().year
    for tipo in TIPOS_DOCUMENTO:
        if (tipo, anio_actual) not in filas:
            filas[(tipo, anio_actual)] = FolioSecuencia(tipo_documento=tipo, anio=anio_actual, ultimo_folio=0)
    return sorted(filas.values(), key=lambda f: (-f.anio, f.tipo_documento))


def establecer_folio(session: Session, tipo_documento: str, anio: int, ultimo_folio: int) -> None:
    """Corrige a mano "en cuál nos quedamos" (ej. al migrar desde el
    control manual en papel/Excel a mitad de año) — el SIGUIENTE folio que
    pida `siguiente_folio()` será `ultimo_folio + 1`."""
    fila = session.get(FolioSecuencia, (tipo_documento, anio))
    if fila is None:
        fila = FolioSecuencia(tipo_documento=tipo_documento, anio=anio, ultimo_folio=ultimo_folio)
        session.add(fila)
    else:
        fila.ultimo_folio = ultimo_folio
