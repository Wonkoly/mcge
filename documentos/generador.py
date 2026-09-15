"""Generación de oficios .docx a partir de las plantillas en
templates_docx/ — construidas editando los documentos reales del
coordinador (ver documentos/texto.py y documentos/folios.py), nunca
reconstruyendo el formato desde código."""

from datetime import date
from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from documentos import folios, texto

TEMPLATES_DIR = Path(__file__).resolve().parent / "templates_docx"


def _render(nombre_plantilla: str, contexto: dict) -> BytesIO:
    tpl = DocxTemplate(str(TEMPLATES_DIR / nombre_plantilla))
    tpl.render(contexto)
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer


def _prefijo_y_nombre_mayusculas(profesor) -> str:
    """"Dr. CHRISTIAN RENE ESCUDERO AYALA" — prefijo mixto + nombre en
    mayúsculas, sin artículo "el/la": es el formato que usan las actas
    reales para listar nombres (no una oración completa), y el que piden
    las plantillas de comité tutorial ("... en Mayúsculas")."""
    prefijo = texto.PREFIJO_POR_TRATAMIENTO.get(profesor.tratamiento or "", "")
    nombre = profesor.nombre.upper()
    return f"{prefijo} {nombre}".strip()


def _tres_tutores(miembros, excluir_profesor_id=None):
    nombres = [
        _prefijo_y_nombre_mayusculas(m.profesor)
        for m in miembros
        if excluir_profesor_id is None or m.profesor_id != excluir_profesor_id
    ]
    tope = 2 if excluir_profesor_id is not None else 3
    nombres += [""] * tope
    return nombres[:tope]


def generar_oficio_comite_tutorial_alumno(*, comite, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`comite` es un actas.models.ComiteTutorial con `.miembros` (hasta 3)."""
    miembros = list(comite.miembros.select_related("profesor").all())
    tutor_1, tutor_2, tutor_3 = _tres_tutores(miembros)
    anio = date.today().year
    contexto = {
        "folio_numero": f"{folios.siguiente_folio('oficio_comite_tutorial', anio):03d}",
        "anio": anio,
        "alumno_nombre": texto.formatear_nombre(comite.alumno.nombre),
        "alumno_codigo": comite.alumno.codigo,
        "acta_numero": comite.acta.numero if comite.acta else "",
        "acta_fecha_corta": texto.fecha_corta_sin_anio(comite.acta.fecha) if comite.acta and comite.acta.fecha else "",
        "tutor_1": tutor_1,
        "tutor_2": tutor_2,
        "tutor_3": tutor_3,
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_comite_tutorial_alumno.docx", contexto)


def generar_oficio_comite_tutorial_docente(*, comite, profesor_destinatario, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """Una carta por cada miembro del comité — `profesor_destinatario` es a
    quien va dirigida esta copia; los otros 2 miembros van en el cuerpo."""
    miembros = list(comite.miembros.select_related("profesor").all())
    otro_1, otro_2 = _tres_tutores(miembros, excluir_profesor_id=profesor_destinatario.id)
    anio = date.today().year
    contexto = {
        "folio_numero": f"{folios.siguiente_folio('oficio_comite_tutorial', anio):03d}",
        "anio": anio,
        "profesor_nombre_mayusculas": profesor_destinatario.nombre.upper(),
        "acta_numero": comite.acta.numero if comite.acta else "",
        "acta_fecha_corta": texto.fecha_corta_sin_anio(comite.acta.fecha) if comite.acta and comite.acta.fecha else "",
        "tutor_2": otro_1,
        "tutor_3": otro_2,
        "alumno_nombre": texto.formatear_nombre(comite.alumno.nombre),
        "alumno_codigo": comite.alumno.codigo,
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_comite_tutorial_docente.docx", contexto)
