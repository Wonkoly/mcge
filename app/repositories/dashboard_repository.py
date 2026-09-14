from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Alumno, Aspirante, Profesor, StatusAlumno


def estadisticas(session: Session) -> dict:
    total_alumnos = session.query(func.count(Alumno.id)).scalar()

    por_status = (
        session.query(StatusAlumno, func.count(Alumno.id))
        .join(Alumno, Alumno.status_codigo == StatusAlumno.codigo, isouter=True)
        .group_by(StatusAlumno.codigo)
        .all()
    )
    por_categoria = (
        session.query(StatusAlumno.categoria, func.count(Alumno.id))
        .join(Alumno, Alumno.status_codigo == StatusAlumno.codigo)
        .group_by(StatusAlumno.categoria)
        .all()
    )
    conteo_categoria = dict(por_categoria)
    activos = conteo_categoria.get("activo", 0)

    total_profesores = session.query(func.count(Profesor.id)).scalar()
    total_nucleo = session.query(func.count(Profesor.id)).filter(Profesor.nucleo_academico.is_(True)).scalar()

    aspirantes_pendientes = (
        session.query(func.count(Aspirante.id))
        .filter(Aspirante.estado.notin_(["Inscrito", "No aceptado"]))
        .scalar()
    )

    return {
        "total_alumnos": total_alumnos,
        "activos": activos,
        "proceso_titulacion": conteo_categoria.get("proceso_titulacion", 0),
        "graduados": conteo_categoria.get("graduado", 0),
        "titulados": conteo_categoria.get("titulado", 0),
        "bajas": conteo_categoria.get("baja", 0),
        "por_status": por_status,
        "total_profesores": total_profesores,
        "total_nucleo": total_nucleo,
        "aspirantes_pendientes": aspirantes_pendientes,
    }


def alumnos_activos_por_ciclo(session: Session) -> list[tuple[str, int]]:
    """Desglose de alumnos ACTIVOS por ciclo de ingreso, más reciente
    primero — cada renglón es navegable desde el panel (Módulo 1.1)."""
    filas = (
        session.query(Alumno.ciclo_ingreso, func.count(Alumno.id))
        .join(StatusAlumno, StatusAlumno.codigo == Alumno.status_codigo)
        .filter(StatusAlumno.categoria == "activo", Alumno.ciclo_ingreso.isnot(None))
        .group_by(Alumno.ciclo_ingreso)
        .all()
    )
    return sorted(filas, key=lambda par: par[0], reverse=True)
