from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Alumno, Direccion, StatusAlumno


def buscar_alumnos(session: Session, texto: str = "") -> list[Alumno]:
    query = session.query(Alumno)
    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Alumno.nombre.ilike(patron), Alumno.codigo.ilike(patron)))
    return query.order_by(Alumno.nombre).all()


def obtener_alumno(session: Session, alumno_id: int) -> Alumno | None:
    return session.get(Alumno, alumno_id)


# --- Módulo 2.1: filtrado combinable + ordenamiento ---

ORDENES_VALIDOS = {
    "nombre": (Alumno.nombre, False),
    "-nombre": (Alumno.nombre, True),
    "ciclo_ingreso": (Alumno.ciclo_ingreso, False),
    "-ciclo_ingreso": (Alumno.ciclo_ingreso, True),
    "creditos_acumulados": (Alumno.creditos_acumulados, False),
    "-creditos_acumulados": (Alumno.creditos_acumulados, True),
    "promedio": (Alumno.promedio, False),
    "-promedio": (Alumno.promedio, True),
}


def buscar_alumnos_filtrado(
    session: Session,
    *,
    texto: str = "",
    ciclo_ingreso: str = "",
    status_codigo: str = "",
    categoria: str = "",
    lies_id: str = "",
    director_id: str = "",
    dictamen: str = "",
    creditos_min: str = "",
    creditos_max: str = "",
    orden: str = "nombre",
) -> list[Alumno]:
    """Todos los filtros son combinables entre sí (se aplican con AND).
    `orden` controla tanto la columna como la dirección (prefijo "-" =
    descendente). `categoria` es la del catálogo `StatusAlumno` (agrupa
    varios códigos, ej. "baja" cubre BV/DE/BA) — la usan los indicadores
    navegables del panel (Módulo 1.1)."""
    query = session.query(Alumno)

    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Alumno.nombre.ilike(patron), Alumno.codigo.ilike(patron)))
    if ciclo_ingreso:
        query = query.filter(Alumno.ciclo_ingreso == ciclo_ingreso)
    if status_codigo:
        query = query.filter(Alumno.status_codigo == status_codigo)
    if categoria:
        query = query.join(StatusAlumno, StatusAlumno.codigo == Alumno.status_codigo).filter(
            StatusAlumno.categoria == categoria
        )
    if lies_id:
        query = query.filter(Alumno.lies_id == int(lies_id))
    if dictamen:
        query = query.filter(Alumno.dictamen == dictamen)
    if creditos_min:
        query = query.filter(Alumno.creditos_acumulados >= int(creditos_min))
    if creditos_max:
        query = query.filter(Alumno.creditos_acumulados <= int(creditos_max))
    if director_id:
        query = query.join(Direccion, Direccion.alumno_id == Alumno.id).filter(
            Direccion.profesor_id == int(director_id),
            Direccion.rol == "Director",
            Direccion.fecha_fin.is_(None),
        )

    columna, descendente = ORDENES_VALIDOS.get(orden, ORDENES_VALIDOS["nombre"])
    query = query.order_by(columna.desc() if descendente else columna.asc())

    return query.all()


def valores_distintos_ciclo_ingreso(session: Session) -> list[str]:
    valores = [v for (v,) in session.query(Alumno.ciclo_ingreso).distinct() if v]
    return sorted(valores, reverse=True)


def valores_distintos_dictamen(session: Session) -> list[str]:
    return sorted(v for (v,) in session.query(Alumno.dictamen).distinct() if v)
