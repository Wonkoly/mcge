import pytest

from actas import direccion_service
from actas.models import Direccion
from alumnos.models import Alumno
from profesores.models import Profesor


@pytest.fixture
def alumno():
    return Alumno.objects.create(codigo="X1", nombre="PEREZ GOMEZ JUAN")


@pytest.fixture
def profesor():
    return Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora")


@pytest.mark.django_db
def test_asignar_direccion_crea_registro_vigente(alumno, profesor):
    direccion, aviso = direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Director")
    assert direccion.vigente
    assert aviso is None


@pytest.mark.django_db
def test_reasignar_mismo_rol_cierra_el_anterior(alumno, profesor):
    otro_profesor = Profesor.objects.create(nombre="Christian Rene Escudero Ayala", tratamiento="Doctor")
    primero, _ = direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Director")
    segundo, _ = direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=otro_profesor.id, rol="Director")

    primero.refresh_from_db()
    assert not primero.vigente
    assert primero.fecha_fin is not None
    assert segundo.vigente
    # El Codirector (si hubiera) no se toca al reasignar el Director — solo
    # se cierra el registro vigente del MISMO rol.
    assert Direccion.objects.filter(alumno_id=alumno.id, fecha_fin__isnull=True).count() == 1


@pytest.mark.django_db
def test_director_y_codirector_conviven(alumno, profesor):
    codirector = Profesor.objects.create(nombre="Mario Alberto Fuentes Arreazola", tratamiento="Doctor")
    direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Director")
    direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=codirector.id, rol="Codirector")

    vigentes = Direccion.objects.filter(alumno_id=alumno.id, fecha_fin__isnull=True)
    assert vigentes.count() == 2


@pytest.mark.django_db
def test_rol_invalido_lanza_valueerror(alumno, profesor):
    with pytest.raises(ValueError):
        direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Asesor")


@pytest.mark.django_db
def test_aviso_al_superar_limite_de_alumnos(profesor):
    for i in range(direccion_service.LIMITE_ALUMNOS_POR_PROFESOR + 1):
        alumno = Alumno.objects.create(codigo=f"L{i}", nombre=f"ALUMNO {i}")
        _, aviso = direccion_service.asignar_direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Director")
    assert aviso is not None
    assert "máximo" in aviso
