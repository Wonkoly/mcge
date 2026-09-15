from datetime import date

import pytest

from documentos import texto
from profesores.models import Profesor


def test_fecha_larga():
    assert texto.fecha_larga(date(2026, 9, 14)) == "14 de septiembre de 2026"


def test_fecha_corta_sin_anio():
    assert texto.fecha_corta_sin_anio(date(2026, 9, 14)) == "14 de septiembre"


def test_numero_a_texto():
    assert texto.numero_a_texto(4) == "cuatro"
    assert texto.numero_a_texto(99) == "99"


def test_formatear_nombre_mantiene_particulas_en_minuscula():
    assert texto.formatear_nombre("CRUZ LOPEZ HARLEN IRENE") == "Cruz Lopez Harlen Irene"
    assert texto.formatear_nombre("GARCIA DE LA TORRE JUAN") == "Garcia de la Torre Juan"


@pytest.mark.django_db
def test_tratamiento_con_nombre_usa_catalogo_cerrado():
    p = Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora")
    assert texto.tratamiento_con_nombre(p, "Araceli Zamora Camacho") == "la Dra. Araceli Zamora Camacho"


@pytest.mark.django_db
def test_tratamiento_con_nombre_masculino():
    p = Profesor.objects.create(nombre="Christian Rene Escudero Ayala", tratamiento="Doctor")
    assert texto.tratamiento_con_nombre(p, "Christian Rene Escudero Ayala") == "el Dr. Christian Rene Escudero Ayala"


@pytest.mark.django_db
def test_tratamiento_con_nombre_sin_tratamiento_capturado():
    p = Profesor.objects.create(nombre="Alguien Sin Catalogar")
    assert texto.tratamiento_con_nombre(p, "Alguien Sin Catalogar") == "Alguien Sin Catalogar"


def test_a_contraido_contrae_el():
    assert texto.a_contraido("el Dr. Juan Pérez") == "Al Dr. Juan Pérez"


def test_a_contraido_no_contrae_la():
    assert texto.a_contraido("la Dra. Ana López") == "A la Dra. Ana López"


@pytest.mark.django_db
def test_acta_referencia_con_fecha():
    from actas.models import Acta

    acta = Acta.objects.create(numero="MCG/1/2026", fecha=date(2026, 1, 10), anio=2026)
    assert texto.acta_referencia(acta) == "Acta MCG/1/2026 con fecha del 10 de enero de 2026"


def test_acta_referencia_sin_acta():
    assert texto.acta_referencia(None) == ""
