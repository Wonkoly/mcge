import pytest

from actas.models import Direccion
from alumnos.models import Alumno
from profesores import services
from profesores.models import Profesor


@pytest.mark.django_db
def test_crear_profesor_limpia_prefijos_del_nombre():
    profesor = services.crear_profesor(nombre="Dr. Juan Pérez", tratamiento="Doctor")
    assert profesor.nombre == "Juan Pérez"
    assert profesor.prefijo == "Dr."


@pytest.mark.django_db
def test_crear_profesor_nombre_duplicado():
    services.crear_profesor(nombre="Juan Pérez")
    with pytest.raises(services.NombreDuplicadoError):
        services.crear_profesor(nombre="Juan Pérez")


@pytest.mark.django_db
def test_crear_profesor_tratamiento_invalido():
    with pytest.raises(ValueError):
        services.crear_profesor(nombre="Juan Pérez", tratamiento="Ingeniero")


@pytest.mark.django_db
def test_actualizar_profesor_sin_nombre_falla():
    profesor = services.crear_profesor(nombre="Juan Pérez")
    with pytest.raises(ValueError):
        services.actualizar_profesor(profesor, nombre="  ")


@pytest.mark.django_db
def test_resumen_direcciones_agrupa_por_rol_y_status_solo_vigentes():
    profesora = Profesor.objects.create(nombre="Ana López", tratamiento="Doctora")
    alumno_activo = Alumno.objects.create(codigo="A1", nombre="Alumno Uno", status_id=None)
    alumno_cerrado = Alumno.objects.create(codigo="A2", nombre="Alumno Dos", status_id=None)
    Direccion.objects.create(alumno=alumno_activo, profesor=profesora, rol="Director")
    Direccion.objects.create(alumno=alumno_cerrado, profesor=profesora, rol="Director", fecha_fin="2020-01-01")

    direcciones = list(Direccion.objects.filter(profesor=profesora))
    resumen = services.resumen_direcciones(profesora, direcciones)

    assert len(resumen) == 1
    assert "directora" in resumen[0]


@pytest.mark.django_db
def test_buscar_profesores_filtrado_cuenta_alumnos_vigentes():
    profesor = Profesor.objects.create(nombre="Carlos Ruiz")
    alumno = Alumno.objects.create(codigo="A3", nombre="Alumno Tres")
    Direccion.objects.create(alumno=alumno, profesor=profesor, rol="Director")

    resultados = dict(services.buscar_profesores_filtrado())
    assert resultados[profesor] == 1


@pytest.mark.django_db
def test_buscar_profesores_filtrado_por_texto():
    services.crear_profesor(nombre="Ana Ramírez")
    services.crear_profesor(nombre="Beto Gómez")
    resultados = services.buscar_profesores_filtrado(texto="ana")
    nombres = [p.nombre for p, _ in resultados]
    assert nombres == ["Ana Ramírez"]
