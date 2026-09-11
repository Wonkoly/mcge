from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Aspirante


def buscar_aspirantes(session: Session, texto: str = "") -> list[Aspirante]:
    query = session.query(Aspirante)
    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Aspirante.nombre.ilike(patron), Aspirante.universidad.ilike(patron)))
    return query.order_by(Aspirante.fecha_registro.desc().nullslast(), Aspirante.nombre).all()


def obtener_aspirante(session: Session, aspirante_id: int) -> Aspirante | None:
    return session.get(Aspirante, aspirante_id)
