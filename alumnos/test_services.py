import pytest

from alumnos import services
from alumnos.models import Alumno
from core.models import StatusAlumno


@pytest.mark.django_db
def test_crear_alumno_requiere_codigo_y_nombre():
    with pytest.raises(ValueError):
        services.crear_alumno(codigo="", nombre="Alguien")
    with pytest.raises(ValueError):
        services.crear_alumno(codigo="123", nombre="")


@pytest.mark.django_db
def test_crear_alumno_codigo_duplicado():
    services.crear_alumno(codigo="X1", nombre="Alumno Uno")
    with pytest.raises(services.CodigoDuplicadoError):
        services.crear_alumno(codigo="X1", nombre="Alumno Dos")


@pytest.mark.django_db
def test_crear_alumno_traduce_status_codigo_a_fk():
    StatusAlumno.objects.create(codigo="AC", nombre="Activo", categoria="activo")
    alumno = services.crear_alumno(codigo="X2", nombre="Alumno Dos", status_codigo="AC")
    assert alumno.status_id == "AC"
    assert alumno.status.categoria == "activo"


@pytest.mark.django_db
def test_actualizar_alumno_registra_cambios_de_codigo_y_nombre(monkeypatch):
    alumno = services.crear_alumno(codigo="X3", nombre="Nombre Viejo")
    services.actualizar_alumno(alumno, codigo="X3B", nombre="Nombre Nuevo")
    alumno.refresh_from_db()
    assert alumno.codigo == "X3B"
    assert alumno.nombre == "Nombre Nuevo"


@pytest.mark.django_db
def test_buscar_alumnos_filtrado_por_texto_nombre_o_codigo():
    # Nota: la búsqueda es case-insensitive pero NO ignora acentos (mismo
    # comportamiento que ya tenía Flask/SQLAlchemy con `ilike` sobre SQLite:
    # el LIKE nativo no pliega acentos). Se busca tal cual está capturado.
    services.crear_alumno(codigo="X4", nombre="Maria Fernandez")
    services.crear_alumno(codigo="X5", nombre="Pedro Sánchez")
    resultado = services.buscar_alumnos_filtrado(texto="MARIA")
    assert [a.nombre for a in resultado] == ["Maria Fernandez"]

    resultado_codigo = services.buscar_alumnos_filtrado(texto="X5")
    assert [a.nombre for a in resultado_codigo] == ["Pedro Sánchez"]


@pytest.mark.django_db
def test_buscar_alumnos_filtrado_por_categoria_de_status():
    activo = StatusAlumno.objects.create(codigo="AC", nombre="Activo", categoria="activo")
    StatusAlumno.objects.create(codigo="BV", nombre="Baja voluntaria", categoria="baja")
    a1 = Alumno.objects.create(codigo="X6", nombre="Alumno Activo", status=activo)
    Alumno.objects.create(codigo="X7", nombre="Alumno de baja", status_id="BV")

    resultado = services.buscar_alumnos_filtrado(categoria=["activo"])
    assert list(resultado) == [a1]


@pytest.mark.django_db
def test_buscar_alumnos_filtrado_combina_filtros_con_and():
    StatusAlumno.objects.create(codigo="AC", nombre="Activo", categoria="activo")
    services.crear_alumno(codigo="X8", nombre="Alguien", ciclo_ingreso="2025 A", status_codigo="AC")
    services.crear_alumno(codigo="X9", nombre="Alguien Más", ciclo_ingreso="2026 B", status_codigo="AC")

    resultado = services.buscar_alumnos_filtrado(ciclo_ingreso=["2025 A"], status_codigo=["AC"])
    assert [a.codigo for a in resultado] == ["X8"]
