from sqlalchemy.orm import Session

from app.models import ComiteTutorial


def comite_vigente(session: Session, alumno_id: int) -> ComiteTutorial | None:
    return (
        session.query(ComiteTutorial)
        .filter(ComiteTutorial.alumno_id == alumno_id, ComiteTutorial.fecha_fin.is_(None))
        .one_or_none()
    )


def historial_comites(session: Session, alumno_id: int) -> list[ComiteTutorial]:
    return (
        session.query(ComiteTutorial)
        .filter(ComiteTutorial.alumno_id == alumno_id)
        .order_by(ComiteTutorial.fecha_inicio.desc().nullslast())
        .all()
    )
