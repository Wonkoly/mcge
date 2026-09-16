import pytest

from actas import acta_service
from actas.models import ComiteTutorial, Direccion, PuntoActa
from alumnos.models import Alumno
from documentos.models import TipoDocumentoPersonalizado
from profesores.models import Profesor


@pytest.fixture
def alumnos():
    return [
        Alumno.objects.create(codigo="A1", nombre="PEREZ GOMEZ JUAN"),
        Alumno.objects.create(codigo="A2", nombre="LOPEZ TORRES ANA"),
    ]


@pytest.fixture
def profesores():
    return [
        Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora"),
        Profesor.objects.create(nombre="Christian Rene Escudero Ayala", tratamiento="Doctor"),
    ]


def _puntos_iniciales(alumnos, profesores):
    return [
        {"tipo": "direccion", "punto_id": None, "alumno_id": alumnos[0].id, "profesor_id": profesores[0].id, "rol": "Director"},
        {"tipo": "comite_tutorial", "punto_id": None, "alumno_id": alumnos[1].id, "ciclo": "2026 A", "miembro_ids": [profesores[0].id, profesores[1].id]},
    ]


@pytest.mark.django_db
def test_crear_acta_dispara_alta_real_y_compone_texto(alumnos, profesores):
    acta, avisos = acta_service.crear_acta(numero="MCG/1/2026", fecha="2026-01-10", puntos=_puntos_iniciales(alumnos, profesores))

    assert avisos == []
    puntos = list(acta.puntos.order_by("orden"))
    assert len(puntos) == 2
    assert puntos[0].tipo == "direccion"
    assert "Director" in puntos[0].titulo
    assert Direccion.objects.get(pk=puntos[0].direccion_id).vigente
    assert puntos[1].tipo == "comite_tutorial"
    assert ComiteTutorial.objects.get(pk=puntos[1].comite_tutorial_id).miembros.count() == 2


@pytest.mark.django_db
def test_numero_duplicado_lanza_error(alumnos, profesores):
    acta_service.crear_acta(numero="MCG/1/2026", puntos=[])
    with pytest.raises(acta_service.NumeroDuplicadoError):
        acta_service.crear_acta(numero="MCG/1/2026", puntos=[])


@pytest.mark.django_db
def test_numero_vacio_lanza_valueerror():
    with pytest.raises(ValueError):
        acta_service.crear_acta(numero="  ", puntos=[])


@pytest.mark.django_db
def test_resaving_sin_cambios_reutiliza_registros(alumnos, profesores):
    acta, _ = acta_service.crear_acta(numero="MCG/2/2026", puntos=_puntos_iniciales(alumnos, profesores))
    puntos_guardados = list(acta.puntos.order_by("orden"))
    direccion_id_original = puntos_guardados[0].direccion_id
    comite_id_original = puntos_guardados[1].comite_tutorial_id

    puntos_resend = [
        {"tipo": "direccion", "punto_id": puntos_guardados[0].id, "alumno_id": alumnos[0].id, "profesor_id": profesores[0].id, "rol": "Director"},
        {"tipo": "comite_tutorial", "punto_id": puntos_guardados[1].id, "alumno_id": alumnos[1].id, "ciclo": "2026 A", "miembro_ids": [profesores[0].id, profesores[1].id]},
    ]
    acta_service.actualizar_acta(acta, numero="MCG/2/2026", puntos=puntos_resend)

    direccion = Direccion.objects.get(pk=direccion_id_original)
    comite = ComiteTutorial.objects.get(pk=comite_id_original)
    assert direccion.vigente, "Reguardar sin cambios no debe cerrar la Dirección vigente"
    assert comite.vigente, "Reguardar sin cambios no debe cerrar el Comité vigente"
    assert Direccion.objects.filter(alumno_id=alumnos[0].id).count() == 1
    assert ComiteTutorial.objects.filter(alumno_id=alumnos[1].id).count() == 1


@pytest.mark.django_db
def test_reordenar_puntos_sin_cambios_no_reabre_historial(alumnos, profesores):
    """Regresión: en el original (Flask), la reutilización se decidía por
    POSICIÓN en la lista — reordenar dos puntos sin cambiar sus datos
    disparaba un cierre/reapertura espurio del historial. Aquí se decide
    por punto_id (la PK real), así que reordenar no debe afectar nada."""
    acta, _ = acta_service.crear_acta(numero="MCG/3/2026", puntos=_puntos_iniciales(alumnos, profesores))
    puntos_guardados = list(acta.puntos.order_by("orden"))
    direccion_id_original = puntos_guardados[0].direccion_id
    comite_id_original = puntos_guardados[1].comite_tutorial_id

    # Mismos datos, orden invertido (el punto de comité ahora va primero).
    puntos_reordenados = [
        {"tipo": "comite_tutorial", "punto_id": puntos_guardados[1].id, "alumno_id": alumnos[1].id, "ciclo": "2026 A", "miembro_ids": [profesores[0].id, profesores[1].id]},
        {"tipo": "direccion", "punto_id": puntos_guardados[0].id, "alumno_id": alumnos[0].id, "profesor_id": profesores[0].id, "rol": "Director"},
    ]
    acta_service.actualizar_acta(acta, numero="MCG/3/2026", puntos=puntos_reordenados)

    direccion = Direccion.objects.get(pk=direccion_id_original)
    comite = ComiteTutorial.objects.get(pk=comite_id_original)
    assert direccion.vigente
    assert comite.vigente
    assert Direccion.objects.filter(alumno_id=alumnos[0].id).count() == 1
    assert ComiteTutorial.objects.filter(alumno_id=alumnos[1].id).count() == 1
    # El punto de comité ahora es el #1 en el orden del día.
    assert PuntoActa.objects.get(acta=acta, orden=1).tipo == "comite_tutorial"


@pytest.mark.django_db
def test_cambiar_datos_de_un_punto_si_cierra_el_anterior(alumnos, profesores):
    acta, _ = acta_service.crear_acta(numero="MCG/4/2026", puntos=_puntos_iniciales(alumnos, profesores))
    punto_direccion = acta.puntos.get(tipo="direccion")
    direccion_original_id = punto_direccion.direccion_id

    otro_profesor = Profesor.objects.create(nombre="Mario Alberto Fuentes Arreazola", tratamiento="Doctor")
    puntos_cambiados = [
        {"tipo": "direccion", "punto_id": punto_direccion.id, "alumno_id": alumnos[0].id, "profesor_id": otro_profesor.id, "rol": "Director"},
    ]
    acta_service.actualizar_acta(acta, numero="MCG/4/2026", puntos=puntos_cambiados)

    direccion_anterior = Direccion.objects.get(pk=direccion_original_id)
    assert not direccion_anterior.vigente
    nueva = Direccion.objects.get(alumno_id=alumnos[0].id, fecha_fin__isnull=True)
    assert nueva.profesor_id == otro_profesor.id


@pytest.mark.django_db
def test_punto_personalizado_se_conserva_al_reguardar(alumnos):
    tipo_documento = TipoDocumentoPersonalizado.objects.create(
        clave="visita_qa", etiqueta="Visita QA de Prueba", categoria="oficio", estado="confirmado",
    )
    acta, _ = acta_service.crear_acta(
        numero="MCG/5/2026",
        puntos=[{
            "tipo": "personalizado", "punto_id": None, "tipo_documento_id": tipo_documento.id,
            "titulo": "Visita QA de Prueba", "resolutivo": "", "alumno_id": alumnos[0].id, "profesor_id": None,
            "miembro_ids": [], "campos_libres": {"destinatario_nombre": "Fulano"},
        }],
    )
    punto = acta.puntos.get()

    # Reguardar sin tocar nada (como pasaría al editar la acta por otro
    # motivo) no debe perder el punto personalizado ni sus campos libres.
    acta_service.actualizar_acta(
        acta, numero="MCG/5/2026",
        puntos=[{
            "tipo": "personalizado", "punto_id": punto.id, "tipo_documento_id": tipo_documento.id,
            "titulo": "Visita QA de Prueba", "resolutivo": "", "alumno_id": alumnos[0].id, "profesor_id": None,
            "miembro_ids": [], "campos_libres": {"destinatario_nombre": "Fulano"},
        }],
    )

    puntos = list(acta.puntos.all())
    assert len(puntos) == 1
    assert puntos[0].tipo == "personalizado"
    assert puntos[0].tipo_documento_id == tipo_documento.id
    assert "Fulano" in puntos[0].datos_json
