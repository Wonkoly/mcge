from sqlalchemy.orm import Session

from app.models import Acta


def listar_actas(session: Session) -> list[Acta]:
    return session.query(Acta).order_by(Acta.fecha.desc().nullslast(), Acta.id.desc()).all()


def obtener_acta(session: Session, acta_id: int) -> Acta | None:
    return session.get(Acta, acta_id)
