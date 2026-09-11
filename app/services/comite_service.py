from datetime import date

from sqlalchemy.orm import Session

from app.models import ComiteMiembro, ComiteTutorial
from app.repositories.comite_repository import comite_vigente
from app.services.auditoria_service import registrar


def asignar_comite_tutorial(
    session: Session,
    *,
    alumno_id: int,
    profesor_ids: list[int],
    ciclo: str | None = None,
    acta_id: int | None = None,
    usuario: str = "usuario",
) -> ComiteTutorial:
    """Cierra el comité tutorial vigente del alumno (si existe) y crea uno
    nuevo con los miembros dados. Confirmado en actas: 2-3 profesores por
    alumno, sin cargo diferenciado — por eso `profesor_ids` es una lista
    plana, no hay campo de rol."""
    if not profesor_ids:
        raise ValueError("Un comité tutorial necesita al menos un profesor")

    hoy = date.today()
    anterior = comite_vigente(session, alumno_id)
    if anterior is not None:
        anterior.fecha_fin = hoy
        registrar(
            session,
            usuario=usuario,
            entidad="ComiteTutorial",
            entidad_id=anterior.id,
            accion="modificar",
            campo="fecha_fin",
            valor_nuevo=str(hoy),
        )

    nuevo = ComiteTutorial(alumno_id=alumno_id, ciclo=ciclo, fecha_inicio=hoy, acta_id=acta_id)
    session.add(nuevo)
    session.flush()
    for pid in profesor_ids:
        session.add(ComiteMiembro(comite_id=nuevo.id, profesor_id=pid))

    registrar(
        session,
        usuario=usuario,
        entidad="ComiteTutorial",
        entidad_id=nuevo.id,
        accion="crear",
        valor_nuevo=f"alumno_id={alumno_id} miembros={profesor_ids}",
    )
    return nuevo
