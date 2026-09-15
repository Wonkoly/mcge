from datetime import date

import pytest
from docxtpl import DocxTemplate

from actas.models import Acta, ComiteMiembro, ComiteTutorial
from alumnos.models import Alumno
from documentos import generador
from profesores.models import Profesor


@pytest.fixture
def comite_de_prueba():
    acta = Acta.objects.create(numero="MCG/1/2026", fecha=date(2026, 1, 10), anio=2026)
    alumno = Alumno.objects.create(codigo="X1", nombre="PEREZ GOMEZ JUAN")
    comite = ComiteTutorial.objects.create(alumno=alumno, ciclo="2026 A", acta=acta)
    p1 = Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora")
    p2 = Profesor.objects.create(nombre="Christian Rene Escudero Ayala", tratamiento="Doctor")
    ComiteMiembro.objects.create(comite=comite, profesor=p1)
    ComiteMiembro.objects.create(comite=comite, profesor=p2)
    return comite


@pytest.mark.django_db
def test_generar_oficio_comite_alumno_produce_docx_valido(comite_de_prueba):
    buffer = generador.generar_oficio_comite_tutorial_alumno(comite=comite_de_prueba, coordinador_nombre="Dr. Coordinador Prueba")
    # Un DocxTemplate válido se puede volver a abrir sin error.
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_oficio_comite_alumno_incrementa_folio_atomicamente(comite_de_prueba):
    from documentos import folios

    antes = folios.siguiente_folio("oficio_comite_tutorial", 2026)
    generador.generar_oficio_comite_tutorial_alumno(comite=comite_de_prueba, coordinador_nombre="Dr. X")
    despues = folios.siguiente_folio("oficio_comite_tutorial", 2026)
    assert despues == antes + 2  # el de arriba + el que consume generar_oficio_...


@pytest.mark.django_db
def test_generar_oficio_comite_docente_excluye_al_destinatario(comite_de_prueba):
    destinatario = comite_de_prueba.miembros.first().profesor
    buffer = generador.generar_oficio_comite_tutorial_docente(
        comite=comite_de_prueba, profesor_destinatario=destinatario, coordinador_nombre="Dr. X",
    )
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_tres_tutores_rellena_con_vacio_si_faltan(comite_de_prueba):
    miembros = list(comite_de_prueba.miembros.select_related("profesor").all())
    t1, t2, t3 = generador._tres_tutores(miembros)
    assert t3 == ""
    assert t1 and t2
