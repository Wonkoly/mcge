from datetime import date

from core import fechas


def test_ciclo_actual_primer_semestre_es_a():
    assert fechas.ciclo_actual(date(2026, 3, 1)) == "2026 A"


def test_ciclo_actual_segundo_semestre_es_b():
    assert fechas.ciclo_actual(date(2026, 9, 15)) == "2026 B"


def test_indice_ciclo_ordena_a_antes_que_b_mismo_anio():
    assert fechas.indice_ciclo("2026 A") < fechas.indice_ciclo("2026 B")


def test_indice_ciclo_formato_no_reconocible_es_none():
    assert fechas.indice_ciclo("no es un ciclo") is None


def test_semestre_desde_ciclo_cuenta_ingreso_como_semestre_1():
    assert fechas.semestre_desde_ciclo("2026 A", "2026 A") == 1
    assert fechas.semestre_desde_ciclo("2026 A", "2027 A") == 3


def test_semestre_desde_ciclo_dato_historico_sin_formato_es_none():
    assert fechas.semestre_desde_ciclo("desconocido", "2026 B") is None


def test_ciclo_ya_paso():
    assert fechas.ciclo_ya_paso("2025 B", "2026 A") is True
    assert fechas.ciclo_ya_paso("2027 A", "2026 A") is False
