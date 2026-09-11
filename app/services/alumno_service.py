from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Alumno
from app.services.auditoria_service import registrar


class CodigoDuplicadoError(Exception):
    pass


CAMPOS_TEXTO = [
    "ciclo_ingreso", "status_codigo", "correo_personal", "correo_institucional",
    "telefono", "tesis_titulo", "observaciones", "maximo_ciclo", "dictamen", "cvu",
]
CAMPOS_NUMERICOS = ["creditos_acumulados", "creditos_faltantes", "promedio", "ciclos_cursados"]


def _aplicar_campos(alumno: Alumno, campos: dict) -> None:
    for campo in CAMPOS_TEXTO:
        if campo in campos:
            setattr(alumno, campo, _o_none(campos.get(campo)))
    for campo in CAMPOS_NUMERICOS:
        if campo in campos:
            setattr(alumno, campo, _a_numero(campos.get(campo)))
    if "fecha_nacimiento" in campos:
        alumno.fecha_nacimiento = _parsear_fecha(campos.get("fecha_nacimiento"))
    if "lies_id" in campos:
        alumno.lies_id = _a_entero(campos.get("lies_id"))


def crear_alumno(session: Session, *, usuario: str = "usuario", **campos) -> Alumno:
    codigo = (campos.get("codigo") or "").strip()
    nombre = (campos.get("nombre") or "").strip()
    if not codigo or not nombre:
        raise ValueError("Código y nombre son obligatorios")

    alumno = Alumno(codigo=codigo, nombre=nombre)
    _aplicar_campos(alumno, campos)
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


def actualizar_alumno(session: Session, alumno: Alumno, *, usuario: str = "usuario", **campos) -> Alumno:
    codigo = (campos.get("codigo") or "").strip()
    nombre = (campos.get("nombre") or "").strip()
    if not codigo or not nombre:
        raise ValueError("Código y nombre son obligatorios")

    cambios = []
    if alumno.codigo != codigo:
        cambios.append(f"código: {alumno.codigo!r} → {codigo!r}")
    if alumno.nombre != nombre:
        cambios.append(f"nombre: {alumno.nombre!r} → {nombre!r}")

    alumno.codigo = codigo
    alumno.nombre = nombre
    _aplicar_campos(alumno, campos)

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
        accion="modificar",
        valor_nuevo="; ".join(cambios) if cambios else "datos actualizados",
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


def _a_numero(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    try:
        return float(valor) if "." in valor else int(valor)
    except ValueError:
        return None


def _parsear_fecha(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()
