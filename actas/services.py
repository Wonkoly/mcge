from datetime import datetime

from actas.models import Lector, Sinodal
from core.auditoria import registrar


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _parsear_fecha(valor):
    valor = _o_none(valor)
    return datetime.strptime(valor, "%Y-%m-%d").date() if valor else None


def agregar_lector(*, alumno_id: int, profesor_id: int, fecha=None, acta_id=None, usuario: str = "usuario") -> Lector:
    lector = Lector.objects.create(alumno_id=alumno_id, profesor_id=profesor_id, fecha=_parsear_fecha(fecha), acta_id=acta_id)
    registrar(usuario=usuario, entidad="Lector", entidad_id=lector.id, accion="crear", valor_nuevo=f"alumno_id={alumno_id} profesor_id={profesor_id}")
    return lector


def quitar_lector(lector: Lector, *, usuario: str = "usuario") -> None:
    registrar(usuario=usuario, entidad="Lector", entidad_id=lector.id, accion="eliminar")
    lector.delete()


def agregar_sinodal(
    *, alumno_id: int, profesor_id: int, cargo: str, fecha_examen=None,
    hora_examen: str | None = None, lugar_examen: str | None = None, acta_id=None, usuario: str = "usuario",
) -> Sinodal:
    sinodal = Sinodal.objects.create(
        alumno_id=alumno_id, profesor_id=profesor_id, cargo=cargo,
        fecha_examen=_parsear_fecha(fecha_examen), hora_examen=_o_none(hora_examen),
        lugar_examen=_o_none(lugar_examen), acta_id=acta_id,
    )
    registrar(usuario=usuario, entidad="Sinodal", entidad_id=sinodal.id, accion="crear", valor_nuevo=f"alumno_id={alumno_id} profesor_id={profesor_id} cargo={cargo}")
    return sinodal


def quitar_sinodal(sinodal: Sinodal, *, usuario: str = "usuario") -> None:
    registrar(usuario=usuario, entidad="Sinodal", entidad_id=sinodal.id, accion="eliminar")
    sinodal.delete()
