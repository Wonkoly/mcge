import docx
import pytest
from docx import Document
from docxtpl import DocxTemplate

from documentos import tipos
from documentos.models import PlantillaBase, TipoDocumentoPersonalizado


@pytest.fixture
def molde_oficio(settings, tmp_path):
    settings.PLANTILLAS_DIR = tmp_path
    doc = Document()
    doc.add_paragraph("MEMBRETE DE PRUEBA")
    doc.save(tmp_path / "base_oficio.docx")
    return PlantillaBase.objects.create(categoria="oficio", archivo="base_oficio.docx")


def _texto_completo(buffer) -> str:
    doc = docx.Document(buffer)
    return "\n".join(p.text for p in doc.paragraphs)


@pytest.mark.django_db
def test_crear_tipo_dedupe_clave():
    uno = tipos.crear_tipo(etiqueta="Cambio de Estatus", categoria="oficio")
    dos = tipos.crear_tipo(etiqueta="Cambio de Estatus", categoria="oficio")
    assert uno.clave == "cambio_de_estatus"
    assert dos.clave == "cambio_de_estatus_2"


@pytest.mark.django_db
def test_crear_tipo_categoria_invalida_lanza_valueerror():
    with pytest.raises(ValueError):
        tipos.crear_tipo(etiqueta="X", categoria="no-existe")


@pytest.mark.django_db
def test_confirmar_tipo_escribe_archivo_y_estado(molde_oficio, settings):
    tipo = tipos.crear_tipo(etiqueta="Visita de Prueba", categoria="oficio")
    tipos.confirmar_tipo(tipo)
    tipo.refresh_from_db()
    assert tipo.estado == "confirmado"
    assert tipo.plantilla_archivo == "visita_de_prueba.docx"
    assert (settings.PLANTILLAS_DIR / tipo.plantilla_archivo).exists()


@pytest.mark.django_db
def test_compilar_plantilla_sin_molde_lanza_error():
    tipo = tipos.crear_tipo(etiqueta="Sin Molde", categoria="constancia")
    with pytest.raises(tipos.MoldeFaltanteError):
        tipos.compilar_plantilla(tipo)


@pytest.mark.django_db
def test_generar_vista_previa_sustituye_variables_de_ejemplo(molde_oficio):
    tipo = tipos.crear_tipo(etiqueta="Vista Previa", categoria="oficio")
    tipos.actualizar_cuerpo(tipo, "Firma: {{ coordinador_nombre }}")

    buffer = tipos.generar_vista_previa(tipo)

    texto = _texto_completo(buffer)
    assert "{{" not in texto
    assert "Coordinador" in texto or "Rendón" in texto
