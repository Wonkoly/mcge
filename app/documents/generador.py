"""Genera documentos .docx (oficios, constancias, actas) a partir de las
plantillas en templates_docx/, construidas a partir de la estructura real
de Docs/Oficios y Docs/Constancias — ver scripts/construir_plantillas.py.

Nombre del coordinador y el lema del ciclo NO están fijos en el código:
se piden en el formulario de generación (el coordinador puede cambiar con
el tiempo, y el lema institucional cambia cada año)."""

from datetime import date
from io import BytesIO

from docxtpl import DocxTemplate

from app.utils.rutas import directorio_recursos

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


def es_femenino(grado: str | None) -> bool:
    """Heurística simple a partir del campo `grado` ('Doctora en...',
    'Maestra en...'). El generador siempre deja el documento como borrador
    editable — si se equivoca, se corrige a mano antes de imprimir."""
    return bool(grado) and ("doctora" in grado.lower() or "maestra" in grado.lower())


def tratamiento_con_nombre(grado: str | None, nombre: str) -> str:
    """'el Dr. Fulano' / 'la Dra. Fulana' / solo 'Fulano' si no se conoce
    el grado — evita el "el/la" literal cuando no hay dato."""
    femenino = es_femenino(grado)
    if grado and "doctor" in grado.lower():
        return f"{'la Dra.' if femenino else 'el Dr.'} {nombre}"
    if grado and ("maestro" in grado.lower() or "maestra" in grado.lower() or "m.c" in grado.lower() or "m. en c" in grado.lower()):
        return f"{'la Mtra.' if femenino else 'el Mtro.'} {nombre}"
    return nombre


def _render(nombre_plantilla: str, contexto: dict) -> BytesIO:
    tpl = DocxTemplate(str(TEMPLATES_DIR / nombre_plantilla))
    tpl.render(contexto)
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer


def _campos_rol(direccion, profesor_tratamiento_nombre: str | None = None):
    femenino = es_femenino(direccion.profesor.grado)
    if direccion.rol == "Director":
        rol_texto_largo = "Directora" if femenino else "Director"
        rol_corto = "directora" if femenino else "director"
    else:
        rol_texto_largo = "Codirectora" if femenino else "Codirector"
        rol_corto = "codirectora" if femenino else "codirector"
    articulo_del_rol = "de la" if femenino else "del"
    return rol_texto_largo, rol_corto, articulo_del_rol


def generar_oficio_direccion(
    *, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None
) -> BytesIO:
    """`direccion` es un objeto app.models.Direccion (con .alumno, .profesor, .rol, .acta).
    `profesor_tratamiento_nombre` (ej. "el Dr. Fulano de Tal") viene del
    formulario — se precarga con una heurística pero el usuario puede
    corregirlo antes de generar."""
    rol_texto_largo, rol_corto, articulo_del_rol = _campos_rol(direccion)

    contexto = {
        "oficio_numero": f"CUCPV/MCG/___/{date.today().year}",
        "alumno_nombre": formatear_nombre(direccion.alumno.nombre),
        "rol_texto": rol_texto_largo,
        "rol_texto_corto": rol_corto,
        "articulo_del_rol": articulo_del_rol,
        "profesor_nombre": profesor_tratamiento_nombre
        or tratamiento_con_nombre(direccion.profesor.grado, formatear_nombre(direccion.profesor.nombre)),
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "acta_numero": direccion.acta.numero if direccion.acta else "",
        "acta_fecha": fecha_larga(direccion.acta.fecha) if direccion.acta and direccion.acta.fecha else "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
        "coordinador_nombre": coordinador_nombre,
    }
    return _render("oficio_asignacion.docx", contexto)


def generar_constancia_direccion(
    *, direccion, coordinador_nombre: str, lema_ciclo: str = "", profesor_tratamiento_nombre: str | None = None
) -> BytesIO:
    rol_texto_largo, _, _ = _campos_rol(direccion)

    contexto = {
        "constancia_numero": f"MCG/___/{date.today().year}",
        "coordinador_nombre": coordinador_nombre,
        "profesor_nombre": profesor_tratamiento_nombre
        or tratamiento_con_nombre(direccion.profesor.grado, formatear_nombre(direccion.profesor.nombre)),
        "rol_texto": rol_texto_largo,
        "alumno_nombre": formatear_nombre(direccion.alumno.nombre),
        "tesis_titulo": direccion.alumno.tesis_titulo or "",
        "fecha_defensa": "",
        "lema_ciclo": lema_ciclo,
        "fecha_larga": fecha_larga(),
    }
    return _render("constancia_direccion.docx", contexto)


def generar_acta(*, acta, coordinador_nombre: str, lema_ciclo: str = "") -> BytesIO:
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
