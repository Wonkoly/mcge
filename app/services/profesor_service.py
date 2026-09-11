from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Profesor
from app.services.auditoria_service import registrar
from app.utils.nombres import limpiar_nombre


class NombreDuplicadoError(Exception):
    pass


def crear_profesor(session: Session, *, usuario: str = "usuario", **campos) -> Profesor:
    nombre = limpiar_nombre((campos.get("nombre") or "").strip())
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    profesor = Profesor(
        nombre=nombre,
        grado=_o_none(campos.get("grado")),
        correo=_o_none(campos.get("correo")),
        telefono=_o_none(campos.get("telefono")),
        cvu=_o_none(campos.get("cvu")),
        nucleo_academico=bool(campos.get("nucleo_academico")),
    )
    session.add(profesor)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NombreDuplicadoError(f"Ya existe un profesor con el nombre {nombre!r}") from exc

    registrar(session, usuario=usuario, entidad="Profesor", entidad_id=profesor.id, accion="crear", valor_nuevo=nombre)
    return profesor


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None
