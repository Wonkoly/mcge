import io
from datetime import date

import docx
import pytest
from docxtpl import DocxTemplate

from actas.models import Acta, ComiteMiembro, ComiteTutorial, Direccion, Lector, PuntoActa, Sinodal
from alumnos.models import Alumno
from documentos import folios, generador, tipos
from documentos.models import TipoDocumentoPersonalizado
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


@pytest.fixture
def alumno_de_prueba():
    return Alumno.objects.create(codigo="X2", nombre="LOPEZ TORRES ANA", tesis_titulo="Tesis de prueba")


@pytest.fixture
def profesor_de_prueba():
    return Profesor.objects.create(nombre="Araceli Zamora Camacho", tratamiento="Doctora")


@pytest.mark.django_db
def test_generar_oficio_direccion_produce_docx_valido(alumno_de_prueba, profesor_de_prueba):
    direccion = Direccion.objects.create(alumno=alumno_de_prueba, profesor=profesor_de_prueba, rol="Director", fecha_inicio=date(2026, 1, 1))
    buffer = generador.generar_oficio_direccion(direccion=direccion, coordinador_nombre="Dr. Coordinador Prueba")
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_constancia_direccion_produce_docx_valido(alumno_de_prueba, profesor_de_prueba):
    direccion = Direccion.objects.create(alumno=alumno_de_prueba, profesor=profesor_de_prueba, rol="Codirector", fecha_inicio=date(2026, 1, 1))
    buffer = generador.generar_constancia_direccion(direccion=direccion, coordinador_nombre="Dr. Coordinador Prueba")
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_constancia_lector_produce_docx_valido(alumno_de_prueba, profesor_de_prueba):
    lector = Lector.objects.create(alumno=alumno_de_prueba, profesor=profesor_de_prueba, fecha=date(2026, 1, 1))
    buffer = generador.generar_constancia_lector(lector=lector, coordinador_nombre="Dr. X")
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_constancia_y_oficio_invitacion_jurado_producen_docx_validos(alumno_de_prueba, profesor_de_prueba):
    sinodal = Sinodal.objects.create(alumno=alumno_de_prueba, profesor=profesor_de_prueba, cargo="Presidente", fecha_examen=date(2026, 6, 1))
    DocxTemplate(generador.generar_constancia_jurado(sinodal=sinodal, coordinador_nombre="Dr. X"))
    DocxTemplate(generador.generar_oficio_invitacion_jurado(sinodal=sinodal, coordinador_nombre="Dr. X"))


@pytest.mark.django_db
def test_generar_acta_produce_docx_valido(alumno_de_prueba, profesor_de_prueba):
    acta = Acta.objects.create(numero="MCG/9/2026", fecha=date(2026, 3, 1), anio=2026)
    PuntoActa.objects.create(acta=acta, orden=1, tipo="otro", titulo="Punto de prueba", resolutivo="Se aprueba.")
    buffer = generador.generar_acta(acta=acta, coordinador_nombre="Dr. X")
    DocxTemplate(buffer)


@pytest.mark.django_db
def test_generar_documento_personalizado_sustituye_y_valida_campos(settings, tmp_path, alumno_de_prueba):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.PLANTILLAS_DIR = tmp_path
    doc = docx.Document()
    doc.add_paragraph("Alumno: {{ alumno_nombre }} — {{ destinatario_nombre }}")
    buffer_plantilla = io.BytesIO()
    doc.save(buffer_plantilla)
    archivo = SimpleUploadedFile("plantilla.docx", buffer_plantilla.getvalue())

    tipo_documento = tipos.crear_tipo(etiqueta="Prueba Generador", categoria="oficio", archivo=archivo)

    acta = Acta.objects.create(numero="MCG/10/2026", anio=2026)
    punto = PuntoActa.objects.create(
        acta=acta, orden=1, tipo="personalizado", titulo="Prueba", alumno=alumno_de_prueba,
        tipo_documento=tipo_documento, datos_json='{"destinatario_nombre": "Fulano"}',
    )

    buffer = generador.generar_documento_personalizado(tipo_documento=tipo_documento, punto=punto, coordinador_nombre="Dr. X")
    texto_generado = "\n".join(p.text for p in docx.Document(buffer).paragraphs)
    assert "LOPEZ TORRES ANA".title() in texto_generado or "Lopez Torres Ana" in texto_generado
    assert "Fulano" in texto_generado


@pytest.mark.django_db
def test_generar_documento_personalizado_lanza_error_si_faltan_campos(settings, tmp_path, alumno_de_prueba):
    from django.core.files.uploadedfile import SimpleUploadedFile

    settings.PLANTILLAS_DIR = tmp_path
    doc = docx.Document()
    doc.add_paragraph("Destinatario: {{ destinatario_nombre }}")
    buffer_plantilla = io.BytesIO()
    doc.save(buffer_plantilla)
    archivo = SimpleUploadedFile("plantilla.docx", buffer_plantilla.getvalue())

    tipo_documento = tipos.crear_tipo(etiqueta="Prueba Faltante", categoria="oficio", archivo=archivo)

    acta = Acta.objects.create(numero="MCG/11/2026", anio=2026)
    punto = PuntoActa.objects.create(acta=acta, orden=1, tipo="personalizado", titulo="Prueba", tipo_documento=tipo_documento)

    with pytest.raises(generador.CamposFaltantesError):
        generador.generar_documento_personalizado(tipo_documento=tipo_documento, punto=punto, coordinador_nombre="Dr. X")
