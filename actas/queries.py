"""Consultas de solo lectura sobre el dominio de Actas (Direccion,
ComiteTutorial, Lector, Sinodal), usadas desde Alumnos/Profesores/Panel.
El alta/baja de estos registros vía Acta completa se porta en su propia
fase (acta_service.py); agregar/quitar Lector y Sinodal directo sí se
porta (ver actas/services.py) porque el expediente del alumno ya lo hacía
así en Flask."""

from django.db.models import Case, F, IntegerField, Value, When

from actas.models import ComiteMiembro, ComiteTutorial, Direccion, Lector, Sinodal

_VIGENTE_PRIMERO = Case(When(fecha_fin__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField())


def direcciones_vigentes(alumno_id: int) -> list[Direccion]:
    return list(Direccion.objects.filter(alumno_id=alumno_id, fecha_fin__isnull=True).select_related("profesor", "acta"))


def contar_dirigidos_activos(profesor_id: int) -> int:
    """Alumnos ACTIVOS con dirección/codirección vigente de este profesor.
    Regla oficial (≤4 estudiantes por profesor) — se muestra como aviso, no
    como bloqueo duro (ver actas/direccion_service.py). Un alumno ya
    titulado/graduado sigue con fecha_fin=NULL (nadie la cierra al
    terminar) pero no debe contar para este límite."""
    return Direccion.objects.filter(
        profesor_id=profesor_id, fecha_fin__isnull=True, alumno__status__categoria="activo"
    ).count()


def historial_direcciones(alumno_id: int) -> list[Direccion]:
    return list(
        Direccion.objects.filter(alumno_id=alumno_id)
        .select_related("profesor", "acta")
        .order_by(F("fecha_inicio").desc(nulls_last=True))
    )


def direcciones_de_profesor(profesor_id: int) -> list[Direccion]:
    return list(
        Direccion.objects.filter(profesor_id=profesor_id)
        .select_related("alumno", "alumno__status", "acta")
        .annotate(_vigente_primero=_VIGENTE_PRIMERO)
        .order_by("-_vigente_primero", F("fecha_inicio").desc(nulls_last=True))
    )


def comite_vigente(alumno_id: int) -> ComiteTutorial | None:
    return (
        ComiteTutorial.objects.filter(alumno_id=alumno_id, fecha_fin__isnull=True)
        .select_related("acta")
        .prefetch_related("miembros__profesor")
        .first()
    )


def historial_comites(alumno_id: int) -> list[ComiteTutorial]:
    return list(
        ComiteTutorial.objects.filter(alumno_id=alumno_id)
        .select_related("acta")
        .prefetch_related("miembros__profesor")
        .order_by(F("fecha_inicio").desc(nulls_last=True))
    )


def membresias_de_profesor(profesor_id: int) -> list[ComiteMiembro]:
    return list(
        ComiteMiembro.objects.filter(profesor_id=profesor_id)
        .select_related("comite", "comite__alumno", "comite__alumno__status")
        .annotate(_vigente_primero=Case(When(comite__fecha_fin__isnull=True, then=Value(1)), default=Value(0), output_field=IntegerField()))
        .order_by("-_vigente_primero", F("comite__fecha_inicio").desc(nulls_last=True))
    )


def lectores_de_alumno(alumno_id: int) -> list[Lector]:
    return list(
        Lector.objects.filter(alumno_id=alumno_id).select_related("profesor").order_by(F("fecha").desc(nulls_last=True))
    )


def sinodales_de_alumno(alumno_id: int) -> list[Sinodal]:
    return list(
        Sinodal.objects.filter(alumno_id=alumno_id)
        .select_related("profesor")
        .order_by(F("fecha_examen").desc(nulls_last=True))
    )
