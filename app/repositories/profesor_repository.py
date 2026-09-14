from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Direccion, Profesor


def listar_profesores(session: Session, solo_activos: bool = True, texto: str = "") -> list[Profesor]:
    query = session.query(Profesor)
    if solo_activos:
        query = query.filter(Profesor.activo.is_(True))
    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Profesor.nombre.ilike(patron), Profesor.linea_investigacion.ilike(patron)))
    return query.order_by(Profesor.nombre).all()


def obtener_profesor(session: Session, profesor_id: int) -> Profesor | None:
    return session.get(Profesor, profesor_id)


def contar_dirigidos_activos(session: Session, profesor_id: int) -> int:
    """Alumnos con dirección/codirección VIGENTE de este profesor. Usado
    para la regla oficial (≤4 estudiantes por profesor, hoja `estudiante -
    profesor` del Excel) — se muestra como aviso, no como bloqueo duro."""
    return (
        session.query(Direccion)
        .filter(Direccion.profesor_id == profesor_id, Direccion.fecha_fin.is_(None))
        .count()
    )


# --- Módulo 3.1: filtrado combinable + ordenamiento + "número de alumnos a cargo" ---

ORDENES_VALIDOS = {
    "nombre": (Profesor.nombre, False),
    "-nombre": (Profesor.nombre, True),
    "num_alumnos": (None, False),
    "-num_alumnos": (None, True),
}


def buscar_profesores_filtrado(
    session: Session,
    *,
    texto: str = "",
    tratamiento: list[str] | None = None,
    sni: list[str] | None = None,
    dedicacion: list[str] | None = None,
    lies_id: list[str] | None = None,
    nucleo: list[str] | None = None,  # valores "si" | "no"
    orden: str = "nombre",
):
    """Devuelve lista de tuplas (Profesor, num_alumnos_vigentes). Todos los
    campos son combinables entre sí (AND); dentro de un mismo campo, varios
    valores marcados se combinan con OR (autofiltro estilo Excel) usando
    `IN`. `orden` controla columna y dirección (prefijo "-" = descendente)."""
    tratamiento = [v for v in (tratamiento or []) if v]
    sni = [v for v in (sni or []) if v]
    dedicacion = [v for v in (dedicacion or []) if v]
    lies_id = [int(v) for v in (lies_id or []) if v]
    nucleo = [v for v in (nucleo or []) if v]

    conteo = (
        session.query(Direccion.profesor_id, func.count(Direccion.id).label("num_alumnos"))
        .filter(Direccion.fecha_fin.is_(None))
        .group_by(Direccion.profesor_id)
        .subquery()
    )

    query = session.query(Profesor, func.coalesce(conteo.c.num_alumnos, 0)).outerjoin(
        conteo, conteo.c.profesor_id == Profesor.id
    )

    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Profesor.nombre.ilike(patron), Profesor.linea_investigacion.ilike(patron)))
    if tratamiento:
        query = query.filter(Profesor.tratamiento.in_(tratamiento))
    if sni:
        query = query.filter(Profesor.sni.in_(sni))
    if dedicacion:
        query = query.filter(Profesor.dedicacion.in_(dedicacion))
    if lies_id:
        query = query.filter(Profesor.lies_id.in_(lies_id))
    if nucleo:
        query = query.filter(Profesor.nucleo_academico.in_([v == "si" for v in nucleo]))

    columna, descendente = ORDENES_VALIDOS.get(orden, ORDENES_VALIDOS["nombre"])
    if orden.lstrip("-") == "num_alumnos":
        columna_orden = func.coalesce(conteo.c.num_alumnos, 0)
    else:
        columna_orden = Profesor.nombre
    query = query.order_by(columna_orden.desc() if descendente else columna_orden.asc())

    return query.all()


def valores_distintos_sni(session: Session) -> list[str]:
    return [v for (v,) in session.query(Profesor.sni).distinct() if v]


def valores_distintos_dedicacion(session: Session) -> list[str]:
    return [v for (v,) in session.query(Profesor.dedicacion).distinct() if v]
