from collections import Counter

from sqlalchemy.orm import Session

from app.models import Alumno, Direccion, Profesor, StatusAlumno
from app.utils.fechas import PROGRAMA_SEMESTRES, ciclo_ya_paso, semestre_desde_ciclo

LIMITE_ALUMNOS_POR_PROFESOR = 4  # regla oficial, ver hoja `estudiante - profesor` del Excel
SEMESTRE_REZAGO_DIRECTOR = 5  # "después del 5to semestre" (Módulo 1.4) — no debería recibir alumnos nuevos


def _alumnos_activos_con_semestre(session: Session, ciclo_vigente: str) -> list[tuple[Alumno, int | None]]:
    activos = (
        session.query(Alumno)
        .join(StatusAlumno, StatusAlumno.codigo == Alumno.status_codigo)
        .filter(StatusAlumno.categoria == "activo")
        .all()
    )
    return [(a, semestre_desde_ciclo(a.ciclo_ingreso, ciclo_vigente)) for a in activos]


def distribucion_semestres(session: Session, ciclo_vigente: str) -> dict:
    """Cuántos alumnos activos hay en cada semestre (1..N), agrupando los
    que ya rebasaron el programa en "excedido" y los sin ciclo de ingreso
    reconocible en "sin_dato" — Módulo 1.3."""
    contador: Counter = Counter()
    for _, semestre in _alumnos_activos_con_semestre(session, ciclo_vigente):
        if semestre is None or semestre < 1:
            contador["sin_dato"] += 1
        elif semestre > PROGRAMA_SEMESTRES:
            contador["excedido"] += 1
        else:
            contador[semestre] += 1
    return contador


def alertas(session: Session, ciclo_vigente: str) -> dict:
    """Casos a cuidar del Módulo 1.4, calculados de la fecha/ciclo — nada
    capturado a mano. Cada lista es de registros reales (alumno o
    profesor), listos para enlazar a su expediente."""
    activos_semestre = _alumnos_activos_con_semestre(session, ciclo_vigente)

    en_ultimo_semestre = sorted(
        (a for a, s in activos_semestre if s == PROGRAMA_SEMESTRES), key=lambda a: a.nombre
    )
    excedieron = sorted(
        (a for a, s in activos_semestre if s is not None and s > PROGRAMA_SEMESTRES), key=lambda a: a.nombre
    )
    creditos_faltantes_avanzado = sorted(
        (
            a
            for a, s in activos_semestre
            if s is not None and s >= PROGRAMA_SEMESTRES and (a.creditos_faltantes or 0) > 0
        ),
        key=lambda a: a.nombre,
    )
    max_ciclo_rebasado = sorted(
        (a for a, _ in activos_semestre if a.maximo_ciclo and ciclo_ya_paso(a.maximo_ciclo, ciclo_vigente)),
        key=lambda a: a.nombre,
    )

    direcciones_vigentes = session.query(Direccion).filter(Direccion.fecha_fin.is_(None)).all()

    conteo_por_profesor = Counter(d.profesor_id for d in direcciones_vigentes)
    profesores_exceso = sorted(
        (
            (session.get(Profesor, profesor_id), total)
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
