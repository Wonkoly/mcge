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
    tratamiento: str = "",
    sni: str = "",
    dedicacion: str = "",
    lies_id: str = "",
    nucleo: str = "",  # "si" | "no" | ""
    orden: str = "nombre",
):
    """Devuelve lista de tuplas (Profesor, num_alumnos_vigentes). Todos los
    filtros son combinables entre sí (se aplican con AND). `orden` controla
    tanto la columna como la dirección (prefijo "-" = descendente)."""
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
        query = query.filter(Profesor.tratamiento == tratamiento)
    if sni:
        query = query.filter(Profesor.sni == sni)
    if dedicacion:
        query = query.filter(Profesor.dedicacion.ilike(f"%{dedicacion}%"))
    if lies_id:
        query = query.filter(Profesor.lies_id == int(lies_id))
    if nucleo == "si":
        query = query.filter(Profesor.nucleo_academico.is_(True))
    elif nucleo == "no":
        query = query.filter(Profesor.nucleo_academico.is_(False))

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
