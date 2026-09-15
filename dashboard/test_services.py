import pytest

from actas.models import Direccion
from alumnos.models import Alumno
from core.models import StatusAlumno
from dashboard import services
from profesores.models import Profesor


@pytest.fixture
def activo():
    return StatusAlumno.objects.create(codigo="AC", nombre="Activo", categoria="activo")


@pytest.mark.django_db
def test_en_ultimo_semestre(activo):
    Alumno.objects.create(codigo="A1", nombre="Justo en semestre 4", status=activo, ciclo_ingreso="2025 A")
    resultado = services.alertas("2026 B")
    assert [a.nombre for a in resultado["en_ultimo_semestre"]] == ["Justo en semestre 4"]
    assert resultado["excedieron"] == []


@pytest.mark.django_db
def test_excedieron_semestres(activo):
    Alumno.objects.create(codigo="A2", nombre="Muy rezagado", status=activo, ciclo_ingreso="2020 A")
    resultado = services.alertas("2026 B")
    assert [a.nombre for a in resultado["excedieron"]] == ["Muy rezagado"]


@pytest.mark.django_db
def test_creditos_faltantes_en_semestre_avanzado(activo):
    Alumno.objects.create(
        codigo="A3", nombre="Le faltan créditos", status=activo, ciclo_ingreso="2025 A", creditos_faltantes=10,
    )
    Alumno.objects.create(
        codigo="A4", nombre="Sin créditos faltantes", status=activo, ciclo_ingreso="2025 A", creditos_faltantes=0,
    )
    resultado = services.alertas("2026 B")
    assert [a.nombre for a in resultado["creditos_faltantes_avanzado"]] == ["Le faltan créditos"]


@pytest.mark.django_db
def test_maximo_ciclo_rebasado(activo):
    Alumno.objects.create(codigo="A5", nombre="Rebasó su máximo", status=activo, maximo_ciclo="2026 A")
    resultado = services.alertas("2026 B")
    assert [a.nombre for a in resultado["max_ciclo_rebasado"]] == ["Rebasó su máximo"]


@pytest.mark.django_db
def test_profesor_con_exceso_de_alumnos(activo):
    profesor = Profesor.objects.create(nombre="Sobrecargado")
    for i in range(5):
        alumno = Alumno.objects.create(codigo=f"B{i}", nombre=f"Alumno {i}", status=activo)
        Direccion.objects.create(alumno=alumno, profesor=profesor, rol="Director")
    resultado = services.alertas("2026 B")
    assert resultado["profesores_exceso"] == [(profesor, 5)]


@pytest.mark.django_db
def test_director_con_alumno_rezagado_no_deberia_recibir_nuevos(activo):
    profesor = Profesor.objects.create(nombre="Con rezago")
    rezagado = Alumno.objects.create(codigo="C1", nombre="Rezagado", status=activo, ciclo_ingreso="2020 A")
    Direccion.objects.create(alumno=rezagado, profesor=profesor, rol="Director")
    resultado = services.alertas("2026 B")
    assert [p.nombre for p in resultado["directores_alumno_rezagado"]] == ["Con rezago"]


@pytest.mark.django_db
def test_sin_alumnos_activos_no_genera_alertas():
    resultado = services.alertas("2026 B")
    assert all(v == [] for v in resultado.values())


@pytest.mark.django_db
def test_distribucion_semestres_agrupa_excedidos_y_sin_dato(activo):
    Alumno.objects.create(codigo="D1", nombre="Semestre 1", status=activo, ciclo_ingreso="2026 B")
    Alumno.objects.create(codigo="D2", nombre="Excedido", status=activo, ciclo_ingreso="2020 A")
    Alumno.objects.create(codigo="D3", nombre="Sin ciclo", status=activo, ciclo_ingreso=None)

    distribucion = services.distribucion_semestres("2026 B")
    assert distribucion[1] == 1
    assert distribucion["excedido"] == 1
    assert distribucion["sin_dato"] == 1
