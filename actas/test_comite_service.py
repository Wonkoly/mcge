import pytest

from actas import comite_service
from actas.models import ComiteTutorial
from alumnos.models import Alumno
from profesores.models import Profesor


@pytest.fixture
def alumno():
    return Alumno.objects.create(codigo="X1", nombre="PEREZ GOMEZ JUAN")


@pytest.fixture
def profesores():
    return [
        Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora"),
        Profesor.objects.create(nombre="Christian Rene Escudero Ayala", tratamiento="Doctor"),
    ]


@pytest.mark.django_db
def test_asignar_comite_crea_registro_con_miembros(alumno, profesores):
    comite = comite_service.asignar_comite_tutorial(alumno_id=alumno.id, profesor_ids=[p.id for p in profesores], ciclo="2026 A")
    assert comite.vigente
    assert comite.miembros.count() == 2


@pytest.mark.django_db
def test_reasignar_comite_cierra_el_anterior(alumno, profesores):
    primero = comite_service.asignar_comite_tutorial(alumno_id=alumno.id, profesor_ids=[profesores[0].id])
    segundo = comite_service.asignar_comite_tutorial(alumno_id=alumno.id, profesor_ids=[profesores[1].id])

    primero.refresh_from_db()
    assert not primero.vigente
    assert segundo.vigente
    assert ComiteTutorial.objects.filter(alumno_id=alumno.id, fecha_fin__isnull=True).count() == 1


@pytest.mark.django_db
def test_sin_profesores_lanza_valueerror(alumno):
    with pytest.raises(ValueError):
        comite_service.asignar_comite_tutorial(alumno_id=alumno.id, profesor_ids=[])
