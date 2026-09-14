from collections import Counter, defaultdict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Direccion, Profesor
from app.models.profesor import TRATAMIENTOS
from app.services.auditoria_service import registrar
from app.utils.nombres import limpiar_nombre

CENTRO_UNIVERSITARIO_DEFAULT = "Centro Universitario de la Costa"

_ETIQUETA_ROL = {
    "Director": {"femenino": "directora", "masculino": "director", "neutro": "director(a)"},
    "Codirector": {"femenino": "codirectora", "masculino": "codirector", "neutro": "codirector(a)"},
}


def _genero_profesor(profesor: Profesor) -> str:
    if profesor.tratamiento in ("Doctora", "Maestra"):
        return "femenino"
    if profesor.tratamiento in ("Doctor", "Maestro"):
        return "masculino"
    return "neutro"


def resumen_direcciones(profesor: Profesor, direcciones: list[Direccion]) -> list[str]:
    """Contadores "N status como rol" para las direcciones VIGENTES del
    profesor (ej. "2 PT, 2 AC como directora, 1 AC como codirectora"),
    calculados por la app en vez de capturarse a mano — ver Módulo 3.4."""
    genero = _genero_profesor(profesor)
    por_rol: dict[str, Counter] = defaultdict(Counter)
    for d in direcciones:
        if not d.vigente:
            continue
        codigo = d.alumno.status_codigo or "—"
        por_rol[d.rol][codigo] += 1

    resumen = []
    for rol in ("Director", "Codirector"):
        contador = por_rol.get(rol)
        if not contador:
            continue
        partes = ", ".join(f"{n} {codigo}" for codigo, n in contador.items())
        etiqueta = _ETIQUETA_ROL[rol][genero]
        resumen.append(f"{partes} como {etiqueta}")
    return resumen


class NombreDuplicadoError(Exception):
    pass


def _validar_tratamiento(valor):
    valor = _o_none(valor)
    if valor and valor not in TRATAMIENTOS:
        raise ValueError(f"Tratamiento inválido: {valor!r}")
    return valor


def crear_profesor(session: Session, *, usuario: str = "usuario", **campos) -> Profesor:
    nombre = limpiar_nombre((campos.get("nombre") or "").strip())
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    profesor = Profesor(
        nombre=nombre,
        tratamiento=_validar_tratamiento(campos.get("tratamiento")),
        grado=_o_none(campos.get("grado")),
        centro_universitario=_o_none(campos.get("centro_universitario")) or CENTRO_UNIVERSITARIO_DEFAULT,
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


def actualizar_profesor(session: Session, profesor: Profesor, *, usuario: str = "usuario", **campos) -> Profesor:
    nombre = limpiar_nombre((campos.get("nombre") or "").strip())
    if not nombre:
        raise ValueError("El nombre es obligatorio")

    profesor.nombre = nombre
    profesor.tratamiento = _validar_tratamiento(campos.get("tratamiento"))
    profesor.grado = _o_none(campos.get("grado"))
    profesor.centro_universitario = _o_none(campos.get("centro_universitario")) or CENTRO_UNIVERSITARIO_DEFAULT
    profesor.correo = _o_none(campos.get("correo"))
    profesor.telefono = _o_none(campos.get("telefono"))
    profesor.cvu = _o_none(campos.get("cvu"))
    profesor.linea_investigacion = _o_none(campos.get("linea_investigacion"))
    profesor.nucleo_academico = bool(campos.get("nucleo_academico"))
    profesor.activo = bool(campos.get("activo", True))

    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NombreDuplicadoError(f"Ya existe un profesor con el nombre {nombre!r}") from exc

    registrar(session, usuario=usuario, entidad="Profesor", entidad_id=profesor.id, accion="modificar", valor_nuevo="datos actualizados")
    return profesor


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None
