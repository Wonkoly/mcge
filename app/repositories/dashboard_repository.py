from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Alumno, Aspirante, Profesor, StatusAlumno


def estadisticas(session: Session) -> dict:
    total_alumnos = session.query(func.count(Alumno.id)).scalar()

    por_status = (
        session.query(StatusAlumno.nombre, func.count(Alumno.id))
        .join(Alumno, Alumno.status_codigo == StatusAlumno.codigo, isouter=True)
        .group_by(StatusAlumno.nombre)
        .all()
    )
    por_categoria = (
        session.query(StatusAlumno.categoria, func.count(Alumno.id))
        .join(Alumno, Alumno.status_codigo == StatusAlumno.codigo)
        .group_by(StatusAlumno.categoria)
        .all()
    )
    activos = next((c for cat, c in por_categoria if cat == "activo"), 0)

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
        "por_status": por_status,
        "total_profesores": total_profesores,
        "total_nucleo": total_nucleo,
        "aspirantes_pendientes": aspirantes_pendientes,
    }
