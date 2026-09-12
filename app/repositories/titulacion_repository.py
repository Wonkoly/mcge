from sqlalchemy.orm import Session

from app.models import Lector, Sinodal


def lectores_de_alumno(session: Session, alumno_id: int) -> list[Lector]:
    return session.query(Lector).filter(Lector.alumno_id == alumno_id).order_by(Lector.fecha.desc().nullslast()).all()


def sinodales_de_alumno(session: Session, alumno_id: int) -> list[Sinodal]:
    return (
        session.query(Sinodal)
        .filter(Sinodal.alumno_id == alumno_id)
        .order_by(Sinodal.fecha_examen.desc().nullslast())
        .all()
    )
