from collections import Counter, defaultdict

from django.db import IntegrityError
from django.db.models import Case, Count, IntegerField, Q, Value, When

from actas.models import Direccion
from core.auditoria import registrar
from core.nombres import limpiar_nombre
from profesores.models import CENTRO_UNIVERSITARIO_DEFAULT, Profesor, TRATAMIENTOS

_ETIQUETA_ROL = {
    "Director": {"femenino": "directora", "masculino": "director", "neutro": "director(a)"},
    "Codirector": {"femenino": "codirectora", "masculino": "codirector", "neutro": "codirector(a)"},
}


class NombreDuplicadoError(Exception):
    pass


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
        codigo = d.alumno.status_id or "—"
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


def _validar_tratamiento(valor):
    valor = _o_none(valor)
    if valor and valor not in TRATAMIENTOS:
        raise ValueError(f"Tratamiento inválido: {valor!r}")
    return valor


def crear_profesor(*, usuario: str = "usuario", **campos) -> Profesor:
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
    try:
        profesor.save()
    except IntegrityError as exc:
        raise NombreDuplicadoError(f"Ya existe un profesor con el nombre {nombre!r}") from exc

    registrar(usuario=usuario, entidad="Profesor", entidad_id=profesor.id, accion="crear", valor_nuevo=nombre)
    return profesor


def actualizar_profesor(profesor: Profesor, *, usuario: str = "usuario", **campos) -> Profesor:
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
        profesor.save()
    except IntegrityError as exc:
        raise NombreDuplicadoError(f"Ya existe un profesor con el nombre {nombre!r}") from exc

    registrar(usuario=usuario, entidad="Profesor", entidad_id=profesor.id, accion="modificar", valor_nuevo="datos actualizados")
    return profesor


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


# --- Módulo 3.1: filtrado combinable + ordenamiento + "número de alumnos a cargo" ---

_VIGENTE = Q(direcciones__fecha_fin__isnull=True)


def buscar_profesores_filtrado(
    *,
    texto: str = "",
    tratamiento: list[str] | None = None,
    sni: list[str] | None = None,
    dedicacion: list[str] | None = None,
    lies_id: list[str] | None = None,
    nucleo: list[str] | None = None,  # valores "si" | "no"
    orden: str = "nombre",
):
    """Devuelve lista de tuplas (Profesor, num_alumnos_vigentes). Todos los
    campos son combinables entre sí (AND); dentro de un mismo campo, varios
    valores marcados se combinan con OR (autofiltro estilo Excel) usando
    `IN`. `orden` controla columna y dirección (prefijo "-" = descendente)."""
    tratamiento = [v for v in (tratamiento or []) if v]
    sni = [v for v in (sni or []) if v]
    dedicacion = [v for v in (dedicacion or []) if v]
    lies_id = [int(v) for v in (lies_id or []) if v]
    nucleo = [v for v in (nucleo or []) if v]

    query = Profesor.objects.annotate(
        num_alumnos=Count("direcciones", filter=_VIGENTE, distinct=True)
    )

    if texto:
        query = query.filter(Q(nombre__icontains=texto) | Q(linea_investigacion__icontains=texto))
    if tratamiento:
        query = query.filter(tratamiento__in=tratamiento)
    if sni:
        query = query.filter(sni__in=sni)
    if dedicacion:
        query = query.filter(dedicacion__in=dedicacion)
    if lies_id:
        query = query.filter(lies_id__in=lies_id)
    if nucleo:
        query = query.filter(nucleo_academico__in=[v == "si" for v in nucleo])

    campo_orden = "num_alumnos" if orden.lstrip("-") == "num_alumnos" else "nombre"
    if orden.startswith("-"):
        campo_orden = f"-{campo_orden}"
    query = query.order_by(campo_orden)

    return [(p, p.num_alumnos) for p in query]


def valores_distintos_sni() -> list[str]:
    return sorted(v for v in Profesor.objects.exclude(sni="").values_list("sni", flat=True).distinct() if v)


def valores_distintos_dedicacion() -> list[str]:
    return sorted(v for v in Profesor.objects.exclude(dedicacion="").values_list("dedicacion", flat=True).distinct() if v)
