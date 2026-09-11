from sqlalchemy.orm import Session

from app.models import Direccion, Profesor


def listar_profesores(session: Session, solo_activos: bool = True) -> list[Profesor]:
    query = session.query(Profesor)
    if solo_activos:
        query = query.filter(Profesor.activo.is_(True))
    return query.order_by(Profesor.nombre).all()


def contar_dirigidos_activos(session: Session, profesor_id: int) -> int:
    """Alumnos con dirección/codirección VIGENTE de este profesor. Usado
    para la regla oficial (≤4 estudiantes por profesor, hoja `estudiante -
    profesor` del Excel) — se muestra como aviso, no como bloqueo duro."""
    return (
        session.query(Direccion)
        .filter(Direccion.profesor_id == profesor_id, Direccion.fecha_fin.is_(None))
        .count()
    )
