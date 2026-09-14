"""Genera documentos .docx (oficios, constancias, actas) a partir de las
plantillas en templates_docx/ — construidas EDITANDO archivos reales
(machotes propios del coordinador cuando existían, o documentos ya
emitidos generalizados) en vez de reconstruir el formato desde código, ver
scripts/construir_plantillas.py y scripts/construir_plantillas_lote2.py.

Nombre del coordinador y el lema del ciclo NO están fijos en el código:
viven en Configuración (app/services/configuracion_service.py) y se
precargan en el formulario, editable ahí mismo.

El folio de cada documento se pide con app/services/folio_service.py
(incremento atómico) — nunca se calcula aquí a mano, así dos PCs pidiendo
folio del mismo tipo casi al mismo tiempo no pueden chocar."""

import json
import re
from datetime import date
from io import BytesIO

from docxtpl import DocxTemplate
from sqlalchemy.orm import Session

from app.models.profesor import PREFIJO_POR_TRATAMIENTO

from app.services.folio_service import siguiente_folio_formateado
from app.utils.rutas import directorio_plantillas_personalizadas, directorio_recursos

_PATRON_VARIABLE = re.compile(r"\{\{\s*(\w+)\s*\}\}")
CAMPOS_OPCIONALES = {"lema_ciclo"}


class CamposFaltantesError(Exception):
    """El cuerpo de un tipo de documento personalizado usa una variable
    que quedó vacía — se detecta ANTES de generar para no entregar un
    oficio/constancia con huecos."""

    def __init__(self, campos: list[str]):
        self.campos = campos
        super().__init__(f"Faltan datos para generar el documento: {', '.join(campos)}")

TEMPLATES_DIR = directorio_recursos() / "app" / "documents" / "templates_docx"

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

NUMEROS_TEXTO = [
    "", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
    "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte",
]


def fecha_larga(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def numero_a_texto(n: int) -> str:
    if 0 < n < len(NUMEROS_TEXTO):
        return NUMEROS_TEXTO[n]
    return str(n)


_MINUSCULAS = {"de", "del", "la", "las", "los", "y"}


def formatear_nombre(nombre: str) -> str:
    """Los nombres de alumno vienen en MAYÚSCULAS del Excel — se ve mal en
    un documento formal. Convierte a Capitalizado manteniendo minúsculas en
    partículas comunes ("de", "del", "la"...)."""
    if not nombre:
        return nombre
    palabras = nombre.strip().split()
    resultado = [
        p.lower() if p.lower() in _MINUSCULAS and i > 0 else p.capitalize()
        for i, p in enumerate(palabras)
    ]
    return " ".join(resultado)


def es_femenino_texto(grado: str | None) -> bool:
    """Heurística de respaldo a partir de texto libre — solo se usa si el
    profesor no tiene `tratamiento` capturado (catálogo cerrado, Módulo
    3.2). El generador siempre deja el documento como borrador editable —
    si se equivoca, se corrige a mano antes de imprimir."""
    return bool(grado) and ("doctora" in grado.lower() or "maestra" in grado.lower())


def es_femenino(profesor) -> bool:
    if profesor.tratamiento:
        return profesor.tratamiento in ("Doctora", "Maestra")
    return es_femenino_texto(profesor.grado)


def tratamiento_con_nombre(profesor, nombre: str) -> str:
    """'el Dr. Fulano' / 'la Dra. Fulana' / solo 'Fulano' si no se conoce
    el tratamiento — evita el "el/la" literal cuando no hay dato. Usa el
    campo `tratamiento` (catálogo cerrado) si existe; si no, cae en la
    heurística vieja sobre el texto libre de `grado` (profesores
    importados antes del catálogo)."""
    if profesor.tratamiento:
        prefijo = PREFIJO_POR_TRATAMIENTO.get(profesor.tratamiento, "")
        articulo = "la" if es_femenino(profesor) else "el"
        return f"{articulo} {prefijo} {nombre}" if prefijo else nombre

    grado = profesor.grado
    femenino = es_femenino_texto(grado)
    if grado and "doctor" in grado.lower():
        return f"{'la Dra.' if femenino else 'el Dr.'} {nombre}"
    if grado and ("maestro" in grado.lower() or "maestra" in grado.lower() or "m.c" in grado.lower() or "m. en c" in grado.lower()):
        return f"{'la Mtra.' if femenino else 'el Mtro.'} {nombre}"
    return nombre


def _a_contraido(nombre_con_tratamiento: str) -> str:
    """"A el Dr. X" no es español correcto — es "Al Dr. X". Si el nombre
    no trae artículo (o es femenino, "la Dra. X"), "A " normal sí aplica."""
    if nombre_con_tratamiento.startswith("el "):
        return "Al " + nombre_con_tratamiento[3:]
    return f"A {nombre_con_tratamiento}"


def _nombre_con_tratamiento(profesor) -> str:
    return tratamiento_con_nombre(profesor, formatear_nombre(profesor.nombre))


def _acta_referencia(acta) -> str:
    if not acta:
        return ""
    if acta.fecha:
        return f"Acta {acta.numero} con fecha del {fecha_larga(acta.fecha)}"
    return f"Acta {acta.numero}"


def _render(nombre_plantilla: str, contexto: dict) -> BytesIO:
    tpl = DocxTemplate(str(TEMPLATES_DIR / nombre_plantilla))
    tpl.render(contexto)
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer


def _campos_rol(direccion):
    femenino = es_femenino(direccion.profesor)
    if direccion.rol == "Director":
        rol_texto_largo = "Directora" if femenino else "Director"
        rol_corto = "directora" if femenino else "director"
    else:
        rol_texto_largo = "Codirectora" if femenino else "Codirector"
        rol_corto = "codirectora" if femenino else "codirector"
    articulo_del_rol = "de la" if femenino else "del"
    return rol_texto_largo, rol_corto, articulo_del_rol


# ---------------------------------------------------------------- Dirección

def generar_oficio_direccion(
    *, session: Session, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None
) -> BytesIO:
    rol_texto_largo, rol_corto, articulo_del_rol = _campos_rol(direccion)
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_direccion", "oficio"),
        "alumno_nombre": formatear_nombre(direccion.alumno.nombre),
        "rol_texto": rol_texto_largo,
        "rol_texto_corto": rol_corto,
        "articulo_del_rol": articulo_del_rol,
        "profesor_nombre": profesor_tratamiento_nombre or _nombre_con_tratamiento(direccion.profesor),
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "acta_numero": direccion.acta.numero if direccion.acta else "",
        "acta_fecha": fecha_larga(direccion.acta.fecha) if direccion.acta and direccion.acta.fecha else "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_asignacion.docx", contexto)


def generar_constancia_direccion(
    *, session: Session, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None
) -> BytesIO:
    rol_texto_largo, _, _ = _campos_rol(direccion)
    contexto = {
        "constancia_numero": siguiente_folio_formateado(session, "constancia_direccion", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": profesor_tratamiento_nombre or _nombre_con_tratamiento(direccion.profesor),
        "rol_texto": rol_texto_largo,
        "alumno_nombre": formatear_nombre(direccion.alumno.nombre),
        "alumno_codigo": direccion.alumno.codigo,
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "fecha_grado": fecha_larga(direccion.alumno.fecha_grado) if direccion.alumno.fecha_grado else "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
    }
    return _render("constancia_director_individual.docx", contexto)


# ------------------------------------------------------------ Comité tutorial

def generar_oficio_comite_tutorial_alumno(*, session: Session, comite, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`comite` es un ComiteTutorial con `.miembros` (lista de ComiteMiembro)."""
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_comite_tutorial", "oficio"),
        "alumno_nombre": formatear_nombre(comite.alumno.nombre),
        "alumno_codigo": comite.alumno.codigo,
        "acta_referencia": _acta_referencia(comite.acta),
        "comite_miembros": [_nombre_con_tratamiento(m.profesor) for m in comite.miembros],
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_comite_tutorial_alumno.docx", contexto)


def generar_oficio_comite_tutorial_docente(
    *, session: Session, comite, profesor_destinatario, coordinador_nombre: str, lema_ciclo: str = ""
) -> BytesIO:
    """Una carta por cada miembro del comité — `profesor_destinatario` es a
    quien va dirigida esta copia; `otros_miembros` son los demás (sin él)."""
    otros = [_nombre_con_tratamiento(m.profesor) for m in comite.miembros if m.profesor_id != profesor_destinatario.id]
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_comite_tutorial", "oficio"),
        "profesor_tratamiento_nombre": _nombre_con_tratamiento(profesor_destinatario),
        "acta_referencia": _acta_referencia(comite.acta),
        "otros_miembros": otros,
        "alumno_nombre": formatear_nombre(comite.alumno.nombre),
        "alumno_codigo": comite.alumno.codigo,
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_comite_tutorial_docente.docx", contexto)


# ------------------------------------------------------------------- Lector

def generar_constancia_lector(*, session: Session, lector, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    contexto = {
        "constancia_numero": siguiente_folio_formateado(session, "constancia_lector", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": _nombre_con_tratamiento(lector.profesor),
        "alumno_nombre": formatear_nombre(lector.alumno.nombre),
        "alumno_codigo": lector.alumno.codigo,
        "tesis_titulo": lector.alumno.tesis_titulo or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
    }
    return _render("constancia_lector.docx", contexto)


# ------------------------------------------------------------------ Sinodal

def generar_constancia_jurado(*, session: Session, sinodal, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    nombre_tratado = _nombre_con_tratamiento(sinodal.profesor)
    contexto = {
        "constancia_numero": siguiente_folio_formateado(session, "constancia_jurado", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": nombre_tratado,
        "a_profesor": _a_contraido(nombre_tratado),
        "cargo_texto": sinodal.cargo or "Vocal",
        "alumno_nombre": formatear_nombre(sinodal.alumno.nombre),
        "alumno_codigo": sinodal.alumno.codigo,
        "fecha_examen": fecha_larga(sinodal.fecha_examen) if sinodal.fecha_examen else "",
        "tesis_titulo": sinodal.alumno.tesis_titulo or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
    }
    return _render("constancia_jurado.docx", contexto)


def generar_oficio_invitacion_jurado(*, session: Session, sinodal, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_invitacion_jurado", "oficio"),
        "profesor_tratamiento_nombre": _nombre_con_tratamiento(sinodal.profesor),
        "acta_referencia": _acta_referencia(sinodal.acta),
        "cargo_texto": sinodal.cargo or "Vocal",
        "alumno_nombre": formatear_nombre(sinodal.alumno.nombre),
        "alumno_codigo": sinodal.alumno.codigo,
        "tesis_titulo": sinodal.alumno.tesis_titulo or "",
        "fecha_examen": fecha_larga(sinodal.fecha_examen) if sinodal.fecha_examen else "",
        "hora_examen": sinodal.hora_examen or "",
        "lugar_examen": sinodal.lugar_examen or "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_invitacion_jurado.docx", contexto)


# --------------------------------------------------------------- Aspirantes

def generar_constancia_evaluador_aspirantes(
    *, session: Session, profesor, ciclo: str, coordinador_nombre: str,
    fecha_entrevista: str = "", lugar: str = "", lema_ciclo: str = "",
) -> BytesIO:
    nombre_tratado = _nombre_con_tratamiento(profesor)
    contexto = {
        "constancia_numero": siguiente_folio_formateado(session, "constancia_evaluador_aspirantes", "constancia"),
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": nombre_tratado,
        "a_profesor": _a_contraido(nombre_tratado),
        "ciclo": ciclo,
        "fecha_entrevista": fecha_entrevista,
        "lugar": lugar,
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
    }
    return _render("constancia_evaluador_aspirantes.docx", contexto)


# ----------------------------------------------------- Trabajo de campo / SEP

def generar_oficio_asentamiento_creditos(
    *, session: Session, alumno, materia_nombre: str, materia_clave: str, creditos: int, ciclo: str,
    coordinador_nombre: str, destinatario_nombre: str = "Coordinadora de Control Escolar",
    acta=None, lema_ciclo: str = "",
) -> BytesIO:
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_asentamiento_creditos", "oficio"),
        "destinatario_nombre": destinatario_nombre,
        "creditos": creditos,
        "materia_nombre": materia_nombre,
        "materia_clave": materia_clave,
        "ciclo": ciclo,
        "alumno_es_mujer": None,  # se deja "el/la" si no se sabe; el formulario puede fijarlo luego
        "alumno_nombre": formatear_nombre(alumno.nombre),
        "alumno_codigo": alumno.codigo,
        "acta_referencia": _acta_referencia(acta),
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_asentamiento_creditos.docx", contexto)


def generar_oficio_permiso_municipio(
    *, session: Session, destinatario_nombre: str, destinatario_cargo: str, municipio: str,
    cuerpo_solicitud: str, coordinador_nombre: str, cuerpo_parrafo2: str = "", lema_ciclo: str = "",
) -> BytesIO:
    """Carta de solicitud de datos/permiso de exploración a una autoridad
    municipal — el cuerpo es texto libre porque cada solicitud describe un
    proyecto de investigación distinto (no se fuerza a variables fijas que
    no reflejarían el caso real)."""
    contexto = {
        "oficio_numero": siguiente_folio_formateado(session, "oficio_permiso_municipio", "oficio"),
        "destinatario_nombre": destinatario_nombre,
        "destinatario_cargo": destinatario_cargo,
        "municipio": municipio,
        "cuerpo_solicitud": cuerpo_solicitud,
        "cuerpo_parrafo2": cuerpo_parrafo2,
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_permiso_municipio.docx", contexto)


# ----------------------------------------------------------------------- Acta

def generar_acta(*, session: Session, acta, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
    """`acta` es un objeto app.models.Acta con `.puntos` (lista de
    PuntoActa, ya ordenada). No genera tablas dinámicas dentro de un punto
    (ej. listas de comité tutorial) — eso va como texto libre dentro del
    resolutivo de ese punto."""
    puntos_ctx = [
        {
            "titulo": p.titulo,
            "resolutivo": p.resolutivo or "",
            "numero_texto": numero_a_texto(p.orden),
        }
        for p in acta.puntos
    ]
    contexto = {
        "numero": acta.numero,
        "lugar": acta.lugar or "Puerto Vallarta, Jalisco",
        "hora_inicio": acta.hora_inicio or "",
        "hora_fin": acta.hora_fin or "",
        "sede": acta.sede or "",
        "asistentes": acta.asistentes or "",
        "fecha_larga": fecha_larga(acta.fecha) if acta.fecha else fecha_larga(),
        "puntos": puntos_ctx,
        "lema_ciclo": lema_ciclo,
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("acta.docx", contexto)


# ------------------------------------------ Tipos de documento personalizados

def generar_documento_personalizado(
    *, session: Session, tipo_documento, punto, coordinador_nombre: str, lema_ciclo: str = ""
) -> BytesIO:
    """`tipo_documento` es un TipoDocumentoPersonalizado ya confirmado
    (con `.plantilla_archivo`), `punto` el PuntoActa que lo usa —
    `punto.datos_json` trae los campos libres capturados (ej.
    destinatario_nombre) y `punto.alumno`/`punto.profesor` los registros
    reales si el cuerpo los usa. La plantilla vive en la carpeta
    escribible (subida desde el taller, no empaquetada) — se lee con la
    misma DocxTemplate/_render de siempre, solo cambia de dónde sale la
    ruta."""
    contexto = json.loads(punto.datos_json) if punto.datos_json else {}

    if punto.alumno is not None:
        a = punto.alumno
        contexto.update(
            {
                "alumno_nombre": formatear_nombre(a.nombre),
                "alumno_codigo": a.codigo,
                "alumno_ciclo_ingreso": a.ciclo_ingreso or "",
                "alumno_tesis_titulo": a.tesis_titulo or "",
                "alumno_dictamen": a.dictamen or "",
                "alumno_correo_institucional": a.correo_institucional or "",
                "alumno_correo_personal": a.correo_personal or "",
                "alumno_telefono": a.telefono or "",
                "alumno_creditos_acumulados": a.creditos_acumulados if a.creditos_acumulados is not None else "",
                "alumno_creditos_faltantes": a.creditos_faltantes if a.creditos_faltantes is not None else "",
                "alumno_promedio": a.promedio if a.promedio is not None else "",
                "alumno_cvu": a.cvu or "",
                "alumno_lies": a.lies.nombre if a.lies else "",
                "alumno_maximo_ciclo": a.maximo_ciclo or "",
            }
        )
    if punto.profesor is not None:
        p = punto.profesor
        contexto.update(
            {
                "profesor_nombre": _nombre_con_tratamiento(p),
                "profesor_nombre_simple": formatear_nombre(p.nombre),
                "profesor_correo": p.correo or "",
                "profesor_telefono": p.telefono or "",
                "profesor_cvu": p.cvu or "",
                "profesor_linea_investigacion": p.linea_investigacion or "",
                "profesor_lies": p.lies.nombre if p.lies else "",
                "profesor_sni": p.sni or "",
                "profesor_centro_universitario": p.centro_universitario or "",
            }
        )
    if punto.acta is not None:
        acta = punto.acta
        contexto.update(
            {
                "acta_numero": acta.numero,
                "acta_fecha": fecha_larga(acta.fecha) if acta.fecha else "",
                "acta_lugar": acta.lugar or "",
                "acta_sede": acta.sede or "",
                "acta_hora_inicio": acta.hora_inicio or "",
                "acta_hora_fin": acta.hora_fin or "",
                "acta_asistentes": acta.asistentes or "",
            }
        )

    if punto.miembros:
        contexto["profesores_lista"] = [{"nombre": _nombre_con_tratamiento(m.profesor)} for m in punto.miembros]

    contexto.update(
        {
            "numero_documento": siguiente_folio_formateado(
                session, f"personalizado_{tipo_documento.clave}", tipo_documento.categoria
            ),
            "fecha_larga": fecha_larga(),
            "coordinador_nombre": coordinador_nombre,
            "lema_ciclo": lema_ciclo,
        }
    )

    variables_usadas = set(_PATRON_VARIABLE.findall(tipo_documento.cuerpo_texto or ""))
    faltantes = sorted(
        v for v in variables_usadas
        if v not in CAMPOS_OPCIONALES and not str(contexto.get(v, "")).strip()
    )
    if "profesores_lista" in (tipo_documento.cuerpo_texto or "") and not contexto.get("profesores_lista"):
        faltantes.append("profesores_lista (no se marcó ningún profesor)")
    if faltantes:
        raise CamposFaltantesError(faltantes)

    tpl = DocxTemplate(str(directorio_plantillas_personalizadas() / tipo_documento.plantilla_archivo))
    tpl.render(contexto)
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer
