from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models import Alumno


def buscar_alumnos(session: Session, texto: str = "") -> list[Alumno]:
    query = session.query(Alumno)
    if texto:
        patron = f"%{texto}%"
        query = query.filter(or_(Alumno.nombre.ilike(patron), Alumno.codigo.ilike(patron)))
    return query.order_by(Alumno.nombre).all()


def obtener_alumno(session: Session, alumno_id: int) -> Alumno | None:
    return session.get(Alumno, alumno_id)
