import pytest

from core import configuracion


@pytest.mark.django_db
def test_obtener_usa_default_cuando_no_hay_fila():
    assert configuracion.obtener("backup_retencion_dias") == "30"


@pytest.mark.django_db
def test_establecer_y_obtener_roundtrip():
    configuracion.establecer("coordinador_nombre", "Dra. Prueba")
    assert configuracion.obtener("coordinador_nombre") == "Dra. Prueba"


@pytest.mark.django_db
def test_establecer_sobrescribe_valor_existente():
    configuracion.establecer("ciclo_escolar_actual", "2026 A")
    configuracion.establecer("ciclo_escolar_actual", "2026 B")
    assert configuracion.obtener("ciclo_escolar_actual") == "2026 B"


@pytest.mark.django_db
def test_obtener_todas_incluye_todas_las_claves_conocidas():
    valores = configuracion.obtener_todas()
    assert set(valores) == set(configuracion.CLAVES_DEFAULT)


@pytest.mark.django_db
def test_ciclo_escolar_vigente_usa_valor_manual_si_existe():
    configuracion.establecer("ciclo_escolar_actual", "2030 A")
    assert configuracion.ciclo_escolar_vigente() == "2030 A"


@pytest.mark.django_db
def test_ciclo_escolar_vigente_calcula_por_fecha_si_no_hay_manual():
    assert configuracion.ciclo_escolar_vigente() == configuracion.ciclo_actual()
