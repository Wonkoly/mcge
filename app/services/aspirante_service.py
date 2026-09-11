from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models import Alumno, Aspirante
from app.services.auditoria_service import registrar


def crear_aspirante(session: Session, *, usuario: str = "usuario", **campos) -> Aspirante:
    nombre = (campos.get("nombre") or "").strip()
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    aspirante = Aspirante(
        nombre=nombre,
        licenciatura=_o_none(campos.get("licenciatura")),
        universidad=_o_none(campos.get("universidad")),
        promedio=_a_float(campos.get("promedio")),
        correo=_o_none(campos.get("correo")),
        telefono=_o_none(campos.get("telefono")),
        ciclo=_o_none(campos.get("ciclo")),
        fecha_registro=date.today(),
        estado=_o_none(campos.get("estado")) or "Registrado",
        observaciones=_o_none(campos.get("observaciones")),
    )
    session.add(aspirante)
    session.flush()
    registrar(session, usuario=usuario, entidad="Aspirante", entidad_id=aspirante.id, accion="crear", valor_nuevo=nombre)
    return aspirante


def cambiar_estado(session: Session, aspirante: Aspirante, nuevo_estado: str, *, usuario: str = "usuario") -> None:
    anterior = aspirante.estado
    aspirante.estado = nuevo_estado
    registrar(
        session,
        usuario=usuario,
        entidad="Aspirante",
        entidad_id=aspirante.id,
        accion="modificar",
        campo="estado",
        valor_anterior=anterior,
        valor_nuevo=nuevo_estado,
    )


def aceptar_aspirante(session: Session, aspirante: Aspirante, *, codigo_alumno: str, usuario: str = "usuario") -> Alumno:
    """Convierte un Aspirante aceptado en Alumno sin recapturar datos (nombre,
    correo, teléfono ya capturados se copian). Requiere el código de alumno
    asignado por control escolar, que no se conoce hasta la inscripción."""
    if aspirante.alumno_id:
        raise ValueError("Este aspirante ya fue convertido a alumno")

    codigo_alumno = (codigo_alumno or "").strip()
    if not codigo_alumno:
        raise ValueError("Se necesita el código de alumno para convertirlo")

    alumno = Alumno(
        codigo=codigo_alumno,
        nombre=aspirante.nombre,
        ciclo_ingreso=aspirante.ciclo,
        status_codigo="AC",
        correo_personal=aspirante.correo,
        telefono=aspirante.telefono,
    )
    session.add(alumno)
    session.flush()

    aspirante.alumno_id = alumno.id
    cambiar_estado(session, aspirante, "Inscrito", usuario=usuario)

    registrar(
        session,
        usuario=usuario,
        entidad="Alumno",
        entidad_id=alumno.id,
        accion="crear",
        valor_nuevo=f"{alumno.nombre} ({codigo_alumno}) — convertido desde aspirante {aspirante.id}",
    )
    return alumno


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _a_float(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    try:
        return float(valor)
    except ValueError:
        return None
