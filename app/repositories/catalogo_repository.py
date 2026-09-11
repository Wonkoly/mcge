from sqlalchemy.orm import Session

from app.models import Lies, StatusAlumno


def listar_status(session: Session) -> list[StatusAlumno]:
    return session.query(StatusAlumno).order_by(StatusAlumno.codigo).all()


def listar_lies(session: Session) -> list[Lies]:
    return session.query(Lies).order_by(Lies.nombre).all()
