from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Acta, PuntoActa
from app.services.auditoria_service import registrar


class NumeroDuplicadoError(Exception):
    pass


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _parsear_fecha(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def _reemplazar_puntos(acta: Acta, puntos: list[dict]) -> None:
    acta.puntos.clear()
    for i, punto in enumerate(puntos, start=1):
        titulo = _o_none(punto.get("titulo"))
        if not titulo:
            continue
        acta.puntos.append(PuntoActa(orden=i, titulo=titulo, resolutivo=_o_none(punto.get("resolutivo"))))


def crear_acta(session: Session, *, usuario: str = "usuario", puntos: list[dict], **campos) -> Acta:
    numero = (campos.get("numero") or "").strip()
    if not numero:
        raise ValueError("El número de acta es obligatorio")

    fecha = _parsear_fecha(campos.get("fecha"))
    anio = fecha.year if fecha else datetime.now().year

    acta = Acta(
        numero=numero,
        fecha=fecha,
        anio=anio,
        resumen=_o_none(campos.get("resumen")),
        hora_inicio=_o_none(campos.get("hora_inicio")),
        hora_fin=_o_none(campos.get("hora_fin")),
        lugar=_o_none(campos.get("lugar")) or "Puerto Vallarta, Jalisco",
        sede=_o_none(campos.get("sede")),
        asistentes=_o_none(campos.get("asistentes")),
    )
    _reemplazar_puntos(acta, puntos)
    session.add(acta)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    registrar(session, usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="crear", valor_nuevo=numero)
    return acta


def actualizar_acta(session: Session, acta: Acta, *, usuario: str = "usuario", puntos: list[dict], **campos) -> Acta:
    numero = (campos.get("numero") or "").strip()
    if not numero:
        raise ValueError("El número de acta es obligatorio")

    fecha = _parsear_fecha(campos.get("fecha"))
    acta.numero = numero
    acta.fecha = fecha
    acta.anio = fecha.year if fecha else acta.anio
    acta.resumen = _o_none(campos.get("resumen"))
    acta.hora_inicio = _o_none(campos.get("hora_inicio"))
    acta.hora_fin = _o_none(campos.get("hora_fin"))
    acta.lugar = _o_none(campos.get("lugar")) or "Puerto Vallarta, Jalisco"
    acta.sede = _o_none(campos.get("sede"))
    acta.asistentes = _o_none(campos.get("asistentes"))
    _reemplazar_puntos(acta, puntos)

    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    registrar(session, usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="modificar", valor_nuevo="datos actualizados")
    return acta
