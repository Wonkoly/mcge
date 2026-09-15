from datetime import datetime

from django.db import IntegrityError
from django.db.models import Q

from alumnos.models import Alumno
from core.auditoria import registrar


class CodigoDuplicadoError(Exception):
    pass


CAMPOS_TEXTO = [
    "ciclo_ingreso", "status_id", "correo_personal", "correo_institucional",
    "telefono", "tesis_titulo", "observaciones", "maximo_ciclo", "dictamen", "cvu",
]
CAMPOS_NUMERICOS = ["creditos_acumulados", "creditos_faltantes", "promedio", "ciclos_cursados"]

# El formulario sigue mandando "status_codigo" (mismo nombre de campo que
# tenía Flask) — se traduce aquí al nombre del atributo FK en Django.
_ALIAS_CAMPO = {"status_codigo": "status_id"}


def _aplicar_campos(alumno: Alumno, campos: dict) -> None:
    campos = {_ALIAS_CAMPO.get(k, k): v for k, v in campos.items()}
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


def crear_alumno(*, usuario: str = "usuario", **campos) -> Alumno:
    codigo = (campos.get("codigo") or "").strip()
    nombre = (campos.get("nombre") or "").strip()
    if not codigo or not nombre:
        raise ValueError("Código y nombre son obligatorios")

    alumno = Alumno(codigo=codigo, nombre=nombre)
    _aplicar_campos(alumno, campos)
    try:
        alumno.save()
    except IntegrityError as exc:
        raise CodigoDuplicadoError(f"Ya existe un alumno con código {codigo!r}") from exc

    registrar(usuario=usuario, entidad="Alumno", entidad_id=alumno.id, accion="crear", valor_nuevo=f"{nombre} ({codigo})")
    return alumno


def actualizar_alumno(alumno: Alumno, *, usuario: str = "usuario", **campos) -> Alumno:
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
        alumno.save()
    except IntegrityError as exc:
        raise CodigoDuplicadoError(f"Ya existe un alumno con código {codigo!r}") from exc

    registrar(
        usuario=usuario, entidad="Alumno", entidad_id=alumno.id, accion="modificar",
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


# --- Módulo 2.1: filtrado combinable + ordenamiento ---

ORDENES_VALIDOS = {
    "nombre": "nombre",
    "-nombre": "-nombre",
    "ciclo_ingreso": "ciclo_ingreso",
    "-ciclo_ingreso": "-ciclo_ingreso",
    "creditos_acumulados": "creditos_acumulados",
    "-creditos_acumulados": "-creditos_acumulados",
    "promedio": "promedio",
    "-promedio": "-promedio",
}


def buscar_alumnos_filtrado(
    *,
    texto: str = "",
    ciclo_ingreso: list[str] | None = None,
    status_codigo: list[str] | None = None,
    categoria: list[str] | None = None,
    lies_id: list[str] | None = None,
    director_id: list[str] | None = None,
    dictamen: list[str] | None = None,
    creditos_min: str = "",
    creditos_max: str = "",
    orden: str = "nombre",
) -> list[Alumno]:
    """Todos los filtros son combinables entre sí (AND); dentro de un mismo
    campo, varios valores marcados se combinan con OR (autofiltro estilo
    Excel — Módulo 2.1/1.1) usando `IN`. `orden` controla columna y
    dirección (prefijo "-" = descendente). `categoria` es la del catálogo
    `StatusAlumno` (agrupa varios códigos, ej. "baja" cubre BV/DE/BA) — la
    usan los indicadores navegables del panel."""
    ciclo_ingreso = [v for v in (ciclo_ingreso or []) if v]
    status_codigo = [v for v in (status_codigo or []) if v]
    categoria = [v for v in (categoria or []) if v]
    lies_id = [int(v) for v in (lies_id or []) if v]
    director_id = [int(v) for v in (director_id or []) if v]
    dictamen = [v for v in (dictamen or []) if v]

    query = Alumno.objects.select_related("status", "lies")

    if texto:
        query = query.filter(Q(nombre__icontains=texto) | Q(codigo__icontains=texto))
    if ciclo_ingreso:
        query = query.filter(ciclo_ingreso__in=ciclo_ingreso)
    if status_codigo:
        query = query.filter(status_id__in=status_codigo)
    if categoria:
        query = query.filter(status__categoria__in=categoria)
    if lies_id:
        query = query.filter(lies_id__in=lies_id)
    if dictamen:
        query = query.filter(dictamen__in=dictamen)
    if creditos_min:
        query = query.filter(creditos_acumulados__gte=int(creditos_min))
    if creditos_max:
        query = query.filter(creditos_acumulados__lte=int(creditos_max))
    if director_id:
        query = query.filter(
            direcciones__profesor_id__in=director_id,
            direcciones__rol="Director",
            direcciones__fecha_fin__isnull=True,
        )

    return list(query.order_by(ORDENES_VALIDOS.get(orden, "nombre")).distinct())


def valores_distintos_ciclo_ingreso() -> list[str]:
    valores = [v for v in Alumno.objects.values_list("ciclo_ingreso", flat=True).distinct() if v]
    return sorted(valores, reverse=True)


def valores_distintos_dictamen() -> list[str]:
    return sorted(v for v in Alumno.objects.values_list("dictamen", flat=True).distinct() if v)
