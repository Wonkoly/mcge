from datetime import date


def ciclo_actual(hoy: date | None = None) -> str:
    """Ciclo escolar sugerido a partir de la fecha de hoy, con el mismo
    formato que usa el Excel/las actas ('2026 A', '2026 B'). Calendario
    típico UDG: A = enero-julio, B = agosto-diciembre. Es solo una
    SUGERENCIA precargada en los formularios — el usuario la puede
    corregir a mano si su calendario real difiere."""
    hoy = hoy or date.today()
    letra = "A" if hoy.month <= 7 else "B"
    return f"{hoy.year} {letra}"
