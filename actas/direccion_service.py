"""Puerto de app/services/direccion_service.py."""

from datetime import date

from actas.models import Direccion
from actas.queries import contar_dirigidos_activos, direcciones_vigentes
from core.auditoria import registrar

LIMITE_ALUMNOS_POR_PROFESOR = 4  # regla oficial, hoja `estudiante - profesor`


def asignar_direccion(
    *, alumno_id: int, profesor_id: int, rol: str, acta_id: int | None = None, usuario: str = "usuario",
) -> tuple[Direccion, str | None]:
    """Cierra la dirección/codirección vigente del mismo rol (si existe) y
    crea una nueva. Devuelve (registro_creado, aviso_o_None) — el aviso es
    informativo (ej. regla de ≤4 alumnos por profesor), NO bloquea la
    asignación: la regla real de las actas se aplica con criterio humano
    (ej. hay excepciones documentadas), así que se avisa en vez de impedir."""
    if rol not in ("Director", "Codirector"):
        raise ValueError(f"Rol inválido: {rol!r}")

    hoy = date.today()
    for vigente in direcciones_vigentes(alumno_id):
        if vigente.rol == rol:
            vigente.fecha_fin = hoy
            vigente.save(update_fields=["fecha_fin", "actualizado_en"])
            registrar(
                usuario=usuario, entidad="Direccion", entidad_id=vigente.id,
                accion="modificar", campo="fecha_fin", valor_nuevo=str(hoy),
            )

    nueva = Direccion.objects.create(alumno_id=alumno_id, profesor_id=profesor_id, rol=rol, fecha_inicio=hoy, acta_id=acta_id)
    registrar(
        usuario=usuario, entidad="Direccion", entidad_id=nueva.id, accion="crear",
        valor_nuevo=f"{rol} profesor_id={profesor_id} alumno_id={alumno_id}",
    )

    aviso = None
    dirigidos = contar_dirigidos_activos(profesor_id)
    if dirigidos > LIMITE_ALUMNOS_POR_PROFESOR:
        aviso = (
            f"Este profesor ya dirige/codirige a {dirigidos} alumnos vigentes "
            f"(regla oficial: máximo {LIMITE_ALUMNOS_POR_PROFESOR})."
        )
    return nueva, aviso
