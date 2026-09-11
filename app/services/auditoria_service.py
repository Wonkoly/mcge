from sqlalchemy.orm import Session

from app.models import HistorialCambio


def registrar(
    session: Session,
    *,
    usuario: str,
    entidad: str,
    entidad_id: int,
    accion: str,
    campo: str | None = None,
    valor_anterior: str | None = None,
    valor_nuevo: str | None = None,
) -> None:
    session.add(
        HistorialCambio(
            usuario=usuario,
            entidad=entidad,
            entidad_id=entidad_id,
            accion=accion,
            campo=campo,
            valor_anterior=valor_anterior,
            valor_nuevo=valor_nuevo,
        )
    )
