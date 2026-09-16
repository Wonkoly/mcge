"""Generación de oficios .docx a partir de las plantillas en
templates_docx/ — construidas editando los documentos reales del
coordinador (ver documentos/texto.py y documentos/folios.py), nunca
reconstruyendo el formato desde código."""

import json
from io import BytesIO
from pathlib import Path

from docxtpl import DocxTemplate

from documentos import contexto as ctx
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


def generar_oficio_comite_tutorial_alumno(*, comite, folio_numero: int, anio: int, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`comite` es un actas.models.ComiteTutorial con `.miembros` (hasta 3).
    `folio_numero`/`anio` los fija quien llama (el usuario los confirma en
    un prompt antes de generar — ver documentos/views.py y
    documentos/folios.py:usar_folio)."""
    miembros = list(comite.miembros.select_related("profesor").all())
    tutor_1, tutor_2, tutor_3 = _tres_tutores(miembros)
    contexto = {
        "folio_numero": f"{folio_numero:03d}",
        "anio": anio,
        # Mayúsculas: el destinatario ya está en negritas en la propia
        # plantilla (párrafo completo), aquí solo se pone el texto.
        "alumno_nombre": comite.alumno.nombre.upper(),
        "alumno_codigo": comite.alumno.codigo,
        # La plantilla ya trae en negritas solo el tramo {{ acta_numero }},
        # el resto del párrafo alrededor queda normal.
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


def generar_oficio_direccion(
    *, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None,
) -> BytesIO:
    rol_texto_largo, rol_corto, articulo_del_rol = texto.campos_rol(direccion)
    contexto = {
        "oficio_numero": folios.siguiente_folio_formateado("oficio_direccion", "oficio"),
        "alumno_nombre": texto.formatear_nombre(direccion.alumno.nombre),
        "rol_texto": rol_texto_largo,
        "rol_texto_corto": rol_corto,
        "articulo_del_rol": articulo_del_rol,
        "profesor_nombre": profesor_tratamiento_nombre or texto.nombre_con_tratamiento(direccion.profesor),
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "acta_numero": direccion.acta.numero if direccion.acta else "",
        "acta_fecha": texto.fecha_larga(direccion.acta.fecha) if direccion.acta and direccion.acta.fecha else "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_asignacion.docx", contexto)


def generar_constancia_direccion(
    *, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None,
) -> BytesIO:
    rol_texto_largo, _, _ = texto.campos_rol(direccion)
    contexto = {
        "constancia_numero": folios.siguiente_folio_formateado("constancia_direccion", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": profesor_tratamiento_nombre or texto.nombre_con_tratamiento(direccion.profesor),
        "rol_texto": rol_texto_largo,
        "alumno_nombre": texto.formatear_nombre(direccion.alumno.nombre),
        "alumno_codigo": direccion.alumno.codigo,
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "fecha_grado": texto.fecha_larga(direccion.alumno.fecha_grado) if direccion.alumno.fecha_grado else "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
    }
    return _render("constancia_director_individual.docx", contexto)


def generar_oficio_comite_tutorial_docente(*, comite, profesor_destinatario, folio_numero: int, anio: int, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """Una carta por cada miembro del comité — `profesor_destinatario` es a
    quien va dirigida esta copia; los otros 2 miembros van en el cuerpo."""
    miembros = list(comite.miembros.select_related("profesor").all())
    otro_1, otro_2 = _tres_tutores(miembros, excluir_profesor_id=profesor_destinatario.id)
    contexto = {
        "folio_numero": f"{folio_numero:03d}",
        "anio": anio,
        # Mayúsculas: el destinatario ya está en negritas en la propia
        # plantilla (párrafo completo), aquí solo se pone el texto.
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


def generar_constancia_lector(*, lector, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    contexto = {
        "constancia_numero": folios.siguiente_folio_formateado("constancia_lector", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": texto.nombre_con_tratamiento(lector.profesor),
        "alumno_nombre": texto.formatear_nombre(lector.alumno.nombre),
        "alumno_codigo": lector.alumno.codigo,
        "tesis_titulo": lector.alumno.tesis_titulo or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
    }
    return _render("constancia_lector.docx", contexto)


def generar_constancia_jurado(*, sinodal, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    nombre_tratado = texto.nombre_con_tratamiento(sinodal.profesor)
    contexto = {
        "constancia_numero": folios.siguiente_folio_formateado("constancia_jurado", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": nombre_tratado,
        "a_profesor": texto.a_contraido(nombre_tratado),
        "cargo_texto": sinodal.cargo or "Vocal",
        "alumno_nombre": texto.formatear_nombre(sinodal.alumno.nombre),
        "alumno_codigo": sinodal.alumno.codigo,
        "fecha_examen": texto.fecha_larga(sinodal.fecha_examen) if sinodal.fecha_examen else "",
        "tesis_titulo": sinodal.alumno.tesis_titulo or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
    }
    return _render("constancia_jurado.docx", contexto)


def generar_oficio_invitacion_jurado(*, sinodal, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    contexto = {
        "oficio_numero": folios.siguiente_folio_formateado("oficio_invitacion_jurado", "oficio"),
        "profesor_tratamiento_nombre": texto.nombre_con_tratamiento(sinodal.profesor),
        "acta_referencia": texto.acta_referencia(sinodal.acta),
        "cargo_texto": sinodal.cargo or "Vocal",
        "alumno_nombre": texto.formatear_nombre(sinodal.alumno.nombre),
        "alumno_codigo": sinodal.alumno.codigo,
        "tesis_titulo": sinodal.alumno.tesis_titulo or "",
        "fecha_examen": texto.fecha_larga(sinodal.fecha_examen) if sinodal.fecha_examen else "",
        "hora_examen": sinodal.hora_examen or "",
        "lugar_examen": sinodal.lugar_examen or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": texto.fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_invitacion_jurado.docx", contexto)


def generar_acta(*, acta, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`acta` es un actas.models.Acta con `.puntos` (ya ordenados por
    `orden`). No genera tablas dinámicas dentro de un punto (ej. listas de
    comité tutorial) — eso va como texto libre dentro del resolutivo de
    ese punto."""
    puntos_ctx = [
        {"titulo": p.titulo, "resolutivo": p.resolutivo or "", "numero_texto": texto.numero_a_texto(p.orden)}
        for p in acta.puntos.all()
    ]
    contexto = {
        "numero": acta.numero,
        "lugar": acta.lugar or "Puerto Vallarta, Jalisco",
        "hora_inicio": acta.hora_inicio or "",
        "hora_fin": acta.hora_fin or "",
        "sede": acta.sede or "",
        "asistentes": acta.asistentes or "",
        "fecha_larga": texto.fecha_larga(acta.fecha) if acta.fecha else texto.fecha_larga(),
        "puntos": puntos_ctx,
        "lema_ciclo": lema_ciclo,
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("acta.docx", contexto)


class CamposFaltantesError(Exception):
    """El cuerpo de un tipo de documento personalizado usa una variable
    que quedó vacía — se detecta ANTES de generar para no entregar un
    oficio/constancia con huecos."""

    def __init__(self, campos: list[str]):
        self.campos = campos
        super().__init__(f"Faltan datos para generar el documento: {', '.join(campos)}")


def generar_documento_personalizado(*, tipo_documento, punto, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`tipo_documento` es un documentos.models.TipoDocumentoPersonalizado
    ya confirmado (con `.plantilla_archivo`), `punto` el actas.models.PuntoActa
    que lo usa — `punto.datos_json` trae los campos libres capturados (ej.
    destinatario_nombre); `punto.alumno`/`punto.profesor`/`punto.acta` y,
    según el tipo de punto del que se creó, `punto.direccion`/
    `punto.comite_tutorial` aportan sus grupos de variables vía
    documentos.contexto — la fuente decide qué se puebla, un solo catálogo
    en vez de dos desincronizados."""
    contexto = json.loads(punto.datos_json) if punto.datos_json else {}

    if punto.alumno_id:
        contexto.update(ctx.contexto_alumno(punto.alumno))
        contexto.update(ctx.contexto_lectores(punto.alumno))
        contexto.update(ctx.contexto_sinodales(punto.alumno))
    if punto.profesor_id:
        contexto.update(ctx.contexto_profesor(punto.profesor))
    if punto.acta_id:
        contexto.update(ctx.contexto_acta(punto.acta))
    if punto.direccion_id:
        contexto.update(ctx.contexto_direccion(punto.direccion))
    if punto.comite_tutorial_id:
        contexto.update(ctx.contexto_comite(punto.comite_tutorial))
        contexto["comite_miembros"] = ctx.lista_comite_miembros(punto.comite_tutorial)

    miembros = list(punto.miembros.select_related("profesor").all())
    if miembros:
        contexto["profesores_lista"] = [{"nombre": texto.nombre_con_tratamiento(m.profesor)} for m in miembros]

    contexto.update({
        "numero_documento": folios.siguiente_folio_formateado(f"personalizado_{tipo_documento.clave}", tipo_documento.categoria),
        "fecha_larga": texto.fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
        "lema_ciclo": lema_ciclo,
    })

    variables_usadas = ctx.variables_usadas(tipo_documento.cuerpo_texto or "")
    faltantes = sorted(
        v for v in variables_usadas
        if v != "lema_ciclo" and not str(contexto.get(v, "")).strip()
    )
    if "profesores_lista" in (tipo_documento.cuerpo_texto or "") and not contexto.get("profesores_lista"):
        faltantes.append("profesores_lista (no se marcó ningún profesor)")
    if faltantes:
        raise CamposFaltantesError(faltantes)

    from documentos.tipos import ruta_plantillas

    tpl = DocxTemplate(str(ruta_plantillas() / tipo_documento.plantilla_archivo))
    tpl.render(contexto)
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer
