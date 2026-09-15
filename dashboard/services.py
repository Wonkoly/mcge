"""Puerto de app/services/dashboard_service.py y
app/repositories/dashboard_repository.py: indicadores del panel (Módulo
1.1/1.3) y alertas de casos a cuidar (Módulo 1.4), calculados por la app a
partir de fecha/ciclo — nada capturado a mano."""

from collections import Counter

from django.db.models import Count

from actas.models import Direccion
from alumnos.models import Alumno
from aspirantes.models import Aspirante
from core.fechas import PROGRAMA_SEMESTRES, ciclo_ya_paso, semestre_desde_ciclo
from core.models import StatusAlumno
from profesores.models import Profesor

LIMITE_ALUMNOS_POR_PROFESOR = 4  # regla oficial, hoja `estudiante - profesor` del Excel
SEMESTRE_REZAGO_DIRECTOR = 5  # "después del 5to semestre" — no debería recibir alumnos nuevos


def estadisticas() -> dict:
    total_alumnos = Alumno.objects.count()

    por_status = [
        (status, status.alumnos.count())
        for status in StatusAlumno.objects.order_by("codigo")
    ]
    conteo_categoria = Counter()
    for alumno in Alumno.objects.select_related("status"):
        if alumno.status:
            conteo_categoria[alumno.status.categoria] += 1
    activos = conteo_categoria.get("activo", 0)

    total_profesores = Profesor.objects.count()
    total_nucleo = Profesor.objects.filter(nucleo_academico=True).count()

    aspirantes_pendientes = Aspirante.objects.exclude(estado__in=["Inscrito", "No aceptado"]).count()

    return {
        "total_alumnos": total_alumnos,
        "activos": activos,
        "proceso_titulacion": conteo_categoria.get("proceso_titulacion", 0),
        "graduados": conteo_categoria.get("graduado", 0),
        "titulados": conteo_categoria.get("titulado", 0),
        "bajas": conteo_categoria.get("baja", 0),
        "por_status": por_status,
        "total_profesores": total_profesores,
        "total_nucleo": total_nucleo,
        "aspirantes_pendientes": aspirantes_pendientes,
    }


def alumnos_activos_por_ciclo() -> list[tuple[str, int]]:
    """Desglose de alumnos ACTIVOS por ciclo de ingreso, más reciente
    primero — cada renglón es navegable desde el panel (Módulo 1.1)."""
    filas = (
        Alumno.objects.filter(status__categoria="activo", ciclo_ingreso__isnull=False)
        .exclude(ciclo_ingreso="")
        .values("ciclo_ingreso")
        .annotate(total=Count("id"))
        .values_list("ciclo_ingreso", "total")
    )
    return sorted(filas, key=lambda par: par[0], reverse=True)


def _alumnos_activos_con_semestre(ciclo_vigente: str) -> list[tuple[Alumno, int | None]]:
    activos = Alumno.objects.filter(status__categoria="activo")
    return [(a, semestre_desde_ciclo(a.ciclo_ingreso, ciclo_vigente)) for a in activos]


def distribucion_semestres(ciclo_vigente: str) -> dict:
    """Cuántos alumnos activos hay en cada semestre (1..N), agrupando los
    que ya rebasaron el programa en "excedido" y los sin ciclo de ingreso
    reconocible en "sin_dato" — Módulo 1.3."""
    contador: Counter = Counter()
    for _, semestre in _alumnos_activos_con_semestre(ciclo_vigente):
        if semestre is None or semestre < 1:
            contador["sin_dato"] += 1
        elif semestre > PROGRAMA_SEMESTRES:
            contador["excedido"] += 1
        else:
            contador[semestre] += 1
    return contador


def alertas(ciclo_vigente: str) -> dict:
    """Casos a cuidar del Módulo 1.4, calculados de la fecha/ciclo — nada
    capturado a mano. Cada lista es de registros reales (alumno o
    profesor), listos para enlazar a su expediente."""
    activos_semestre = _alumnos_activos_con_semestre(ciclo_vigente)

    en_ultimo_semestre = sorted((a for a, s in activos_semestre if s == PROGRAMA_SEMESTRES), key=lambda a: a.nombre)
    excedieron = sorted(
        (a for a, s in activos_semestre if s is not None and s > PROGRAMA_SEMESTRES), key=lambda a: a.nombre
    )
    creditos_faltantes_avanzado = sorted(
        (
            a for a, s in activos_semestre
            if s is not None and s >= PROGRAMA_SEMESTRES and (a.creditos_faltantes or 0) > 0
        ),
        key=lambda a: a.nombre,
    )
    max_ciclo_rebasado = sorted(
        (a for a, _ in activos_semestre if a.maximo_ciclo and ciclo_ya_paso(a.maximo_ciclo, ciclo_vigente)),
        key=lambda a: a.nombre,
    )

    direcciones_vigentes = list(Direccion.objects.filter(fecha_fin__isnull=True).select_related("profesor"))

    conteo_por_profesor = Counter(d.profesor_id for d in direcciones_vigentes)
    profesores_por_id = {d.profesor_id: d.profesor for d in direcciones_vigentes}
    profesores_exceso = sorted(
        (
            (profesores_por_id[profesor_id], total)
            for profesor_id, total in conteo_por_profesor.items()
            if total > LIMITE_ALUMNOS_POR_PROFESOR
        ),
        key=lambda par: -par[1],
    )

    semestre_por_alumno_id = {a.id: s for a, s in activos_semestre}
    directores_rezago: dict[int, Profesor] = {}
    for d in direcciones_vigentes:
        if d.rol != "Director":
            continue
        semestre = semestre_por_alumno_id.get(d.alumno_id)
        if semestre is not None and semestre > SEMESTRE_REZAGO_DIRECTOR:
            directores_rezago.setdefault(d.profesor_id, d.profesor)

    return {
        "en_ultimo_semestre": en_ultimo_semestre,
        "excedieron": excedieron,
        "creditos_faltantes_avanzado": creditos_faltantes_avanzado,
        "max_ciclo_rebasado": max_ciclo_rebasado,
        "profesores_exceso": profesores_exceso,
        "directores_alumno_rezagado": sorted(directores_rezago.values(), key=lambda p: p.nombre),
    }
