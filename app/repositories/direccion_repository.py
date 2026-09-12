from sqlalchemy.orm import Session

from app.models import Direccion


def direcciones_vigentes(session: Session, alumno_id: int) -> list[Direccion]:
    return (
        session.query(Direccion)
        .filter(Direccion.alumno_id == alumno_id, Direccion.fecha_fin.is_(None))
        .all()
    )


def historial_direcciones(session: Session, alumno_id: int) -> list[Direccion]:
    return (
        session.query(Direccion)
        .filter(Direccion.alumno_id == alumno_id)
        .order_by(Direccion.fecha_inicio.desc().nullslast())
        .all()
    )


def direcciones_de_profesor(session: Session, profesor_id: int) -> list[Direccion]:
    """Todas las direcciones/codirecciones (vigentes e históricas) donde
    este profesor participa — para la pantalla 'Observar' de Profesor."""
    return (
        session.query(Direccion)
        .filter(Direccion.profesor_id == profesor_id)
        .order_by(Direccion.fecha_fin.is_(None).desc(), Direccion.fecha_inicio.desc().nullslast())
        .all()
    )
