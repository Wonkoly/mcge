from sqlalchemy.orm import Session

from app.models import ComiteMiembro, ComiteTutorial


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


def membresias_de_profesor(session: Session, profesor_id: int) -> list[ComiteMiembro]:
    """Todos los comités tutoriales (vigentes e históricos) donde este
    profesor participa como miembro — para la pantalla 'Observar' de
    Profesor."""
    return (
        session.query(ComiteMiembro)
        .join(ComiteTutorial)
        .filter(ComiteMiembro.profesor_id == profesor_id)
        .order_by(ComiteTutorial.fecha_fin.is_(None).desc(), ComiteTutorial.fecha_inicio.desc().nullslast())
        .all()
    )
