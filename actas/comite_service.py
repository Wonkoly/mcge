"""Puerto de app/services/comite_service.py."""

from datetime import date

from actas.models import ComiteMiembro, ComiteTutorial
from actas.queries import comite_vigente
from core.auditoria import registrar


def asignar_comite_tutorial(
    *, alumno_id: int, profesor_ids: list[int], ciclo: str | None = None, acta_id: int | None = None, usuario: str = "usuario",
) -> ComiteTutorial:
    """Cierra el comité tutorial vigente del alumno (si existe) y crea uno
    nuevo con los miembros dados. Confirmado en actas: 2-3 profesores por
    alumno, sin cargo diferenciado — por eso `profesor_ids` es una lista
    plana, no hay campo de rol."""
    if not profesor_ids:
        raise ValueError("Un comité tutorial necesita al menos un profesor")

    hoy = date.today()
    anterior = comite_vigente(alumno_id)
    if anterior is not None:
        anterior.fecha_fin = hoy
        anterior.save(update_fields=["fecha_fin", "actualizado_en"])
        registrar(
            usuario=usuario, entidad="ComiteTutorial", entidad_id=anterior.id,
            accion="modificar", campo="fecha_fin", valor_nuevo=str(hoy),
        )

    nuevo = ComiteTutorial.objects.create(alumno_id=alumno_id, ciclo=ciclo, fecha_inicio=hoy, acta_id=acta_id)
    ComiteMiembro.objects.bulk_create([ComiteMiembro(comite=nuevo, profesor_id=pid) for pid in profesor_ids])

    registrar(
        usuario=usuario, entidad="ComiteTutorial", entidad_id=nuevo.id, accion="crear",
        valor_nuevo=f"alumno_id={alumno_id} miembros={profesor_ids}",
    )
    return nuevo
