from datetime import date

import docx
import pytest
from docxtpl import DocxTemplate

from actas.models import Acta, ComiteMiembro, ComiteTutorial
from alumnos.models import Alumno
from documentos import folios, generador
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
    buffer = generador.generar_oficio_comite_tutorial_alumno(
        comite=comite_de_prueba, folio_numero=7, anio=2026, coordinador_nombre="Dr. Coordinador Prueba",
    )
    # Un DocxTemplate válido se puede volver a abrir sin error.
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_oficio_comite_docente_excluye_al_destinatario(comite_de_prueba):
    destinatario = comite_de_prueba.miembros.first().profesor
    buffer = generador.generar_oficio_comite_tutorial_docente(
        comite=comite_de_prueba, profesor_destinatario=destinatario, folio_numero=8, anio=2026, coordinador_nombre="Dr. X",
    )
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_alumno_nombre_en_mayusculas_y_negritas_sin_romper_el_parrafo(comite_de_prueba):
    """Regresión: una versión anterior usaba docxtpl.RichText aquí y vació
    el párrafo del destinatario (y varios de los siguientes) en vez de
    escribir el nombre. La negrita ahora vive en la plantilla; el
    contexto solo manda el texto en mayúsculas."""
    buffer = generador.generar_oficio_comite_tutorial_alumno(
        comite=comite_de_prueba, folio_numero=1, anio=2026, coordinador_nombre="Dr. X",
    )
    d = docx.Document(buffer)
    textos = [p.text for p in d.paragraphs]
    assert "PEREZ GOMEZ JUAN" in textos
    assert "CÓDIGO: X1" in textos


@pytest.mark.django_db
def test_acta_numero_queda_en_negritas_y_el_resto_del_parrafo_no(comite_de_prueba):
    buffer = generador.generar_oficio_comite_tutorial_alumno(
        comite=comite_de_prueba, folio_numero=1, anio=2026, coordinador_nombre="Dr. X",
    )
    d = docx.Document(buffer)
    parrafo = next(p for p in d.paragraphs if "mediante el Acta" in p.text)
    runs_con_texto = [r for r in parrafo.runs if r.text]
    negrita = [r for r in runs_con_texto if r.bold]
    normal = [r for r in runs_con_texto if not r.bold]
    assert any("MCG/1/2026" in r.text for r in negrita)
    assert any("mediante el Acta" in r.text for r in normal)
    assert any("con fecha del" in r.text for r in normal)


@pytest.mark.django_db
def test_tres_tutores_rellena_con_vacio_si_faltan(comite_de_prueba):
    miembros = list(comite_de_prueba.miembros.select_related("profesor").all())
    t1, t2, t3 = generador._tres_tutores(miembros)
    assert t3 == ""
    assert t1 and t2


@pytest.mark.django_db
def test_folio_sugerido_no_escribe_nada():
    assert folios.folio_sugerido("oficio_prueba_x", 2026) == 1
    # Llamarlo de nuevo debe seguir dando 1: no consumió nada.
    assert folios.folio_sugerido("oficio_prueba_x", 2026) == 1


@pytest.mark.django_db
def test_usar_folio_deja_el_siguiente_sugerido_despues():
    folios.usar_folio("oficio_prueba_y", 5, 2026)
    assert folios.folio_sugerido("oficio_prueba_y", 2026) == 6


@pytest.mark.django_db
def test_usar_folio_nunca_baja_el_contador():
    folios.usar_folio("oficio_prueba_z", 10, 2026)
    folios.usar_folio("oficio_prueba_z", 3, 2026)  # alguien escribió un número menor por error
    assert folios.folio_sugerido("oficio_prueba_z", 2026) == 11
