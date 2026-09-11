from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Alumno
from app.services.auditoria_service import registrar


class CodigoDuplicadoError(Exception):
    pass


def crear_alumno(session: Session, *, usuario: str = "usuario", **campos) -> Alumno:
    codigo = (campos.get("codigo") or "").strip()
    nombre = (campos.get("nombre") or "").strip()
    if not codigo or not nombre:
        raise ValueError("Código y nombre son obligatorios")

    fecha_nacimiento = _parsear_fecha(campos.get("fecha_nacimiento"))

    alumno = Alumno(
        codigo=codigo,
        nombre=nombre,
        ciclo_ingreso=_o_none(campos.get("ciclo_ingreso")),
        status_codigo=_o_none(campos.get("status_codigo")),
        correo_personal=_o_none(campos.get("correo_personal")),
        correo_institucional=_o_none(campos.get("correo_institucional")),
        telefono=_o_none(campos.get("telefono")),
        fecha_nacimiento=fecha_nacimiento,
        lies_id=_a_entero(campos.get("lies_id")),
        tesis_titulo=_o_none(campos.get("tesis_titulo")),
        observaciones=_o_none(campos.get("observaciones")),
    )
    session.add(alumno)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise CodigoDuplicadoError(f"Ya existe un alumno con código {codigo!r}") from exc

    registrar(
        session,
        usuario=usuario,
        entidad="Alumno",
        entidad_id=alumno.id,
        accion="crear",
        valor_nuevo=f"{nombre} ({codigo})",
    )
    return alumno


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _a_entero(valor):
    valor = _o_none(valor)
    return int(valor) if valor else None


def _parsear_fecha(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()
