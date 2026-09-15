import re
from datetime import date

PROGRAMA_SEMESTRES = 4

_PATRON_CICLO = re.compile(r"(\d{4})\s*([AB])", re.IGNORECASE)


def indice_ciclo(ciclo: str) -> int | None:
    """Convierte '2024 A'/'2024B'/etc. en un índice comparable (año*2 + 0|1)
    para poder restar dos ciclos y obtener cuántos semestres pasaron, o
    comparar cuál de dos ciclos es más reciente."""
    coincidencia = _PATRON_CICLO.search(ciclo or "")
    if not coincidencia:
        return None
    anio, letra = coincidencia.groups()
    return int(anio) * 2 + (0 if letra.upper() == "A" else 1)


def semestre_desde_ciclo(ciclo_ingreso: str | None, ciclo_vigente: str) -> int | None:
    """Semestre actual del alumno (1, 2, 3, 4...) contando el ciclo de ingreso
    como el semestre 1. Devuelve None si `ciclo_ingreso` no tiene un formato
    reconocible (dato histórico sin capturar). El programa dura
    PROGRAMA_SEMESTRES semestres — un valor mayor indica que ya los rebasó."""
    indice_ingreso = indice_ciclo(ciclo_ingreso or "")
    indice_vigente = indice_ciclo(ciclo_vigente)
    if indice_ingreso is None or indice_vigente is None:
        return None
    return indice_vigente - indice_ingreso + 1


def ciclo_ya_paso(ciclo_referencia: str | None, ciclo_vigente: str) -> bool | None:
    """True si `ciclo_referencia` (ej. el `Máximo Ciclo` de un alumno) ya
    quedó atrás respecto al ciclo vigente. None si no se puede comparar
    (dato sin formato reconocible)."""
    indice_referencia = indice_ciclo(ciclo_referencia or "")
    indice_vigente = indice_ciclo(ciclo_vigente)
    if indice_referencia is None or indice_vigente is None:
        return None
    return indice_vigente > indice_referencia


def ciclo_actual(hoy: date | None = None) -> str:
    """Ciclo escolar sugerido a partir de la fecha de hoy, con el mismo
    formato que usa el Excel/las actas ('2026 A', '2026 B'). Calendario
    típico UDG: A = enero-julio, B = agosto-diciembre. Es solo una
    SUGERENCIA precargada en los formularios — el usuario la puede
    corregir a mano si su calendario real difiere."""
    hoy = hoy or date.today()
    letra = "A" if hoy.month <= 7 else "B"
    return f"{hoy.year} {letra}"
