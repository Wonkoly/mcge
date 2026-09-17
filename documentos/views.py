import re
from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from actas.models import Acta, ComiteTutorial, Direccion, Lector, PuntoActa, Sinodal
from core import configuracion as config
from core.configuracion import obtener as obtener_config
from documentos import folios, generador, tipos
from documentos.contexto import GRUPOS_VARIABLES, LISTAS_DISPONIBLES, ejemplos_variables
from documentos.generador import CamposFaltantesError
from documentos.models import PlantillaBase, TipoDocumentoPersonalizado
from documentos.tipos import CATEGORIAS_VALIDAS, PlantillaFaltanteError
from profesores.models import Profesor

CLAVES_CONFIG_DOCUMENTOS = ("coordinador_nombre", "ciclo_escolar_actual", "lema_ciclo")
EJEMPLO_PLANTILLA_ARCHIVO = "oficio_comite_tutorial_alumno.docx"


def _coordinador_y_lema():
    return obtener_config("coordinador_nombre"), (obtener_config("lema_ciclo") or "")


def _descargar(buffer, nombre_archivo):
    respuesta = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return respuesta


def _nombre_archivo(texto: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", texto).strip()
    return re.sub(r"\s+", "_", limpio) + ".docx"


def _folio_numero_desde_form(request, alumno_id):
    """El botón pregunta el número por prompt() antes de enviar el POST —
    aquí solo se valida lo que llegó. Si falta o no es un entero positivo,
    se aborta sin generar nada (el usuario canceló el prompt o escribió
    algo inválido)."""
    crudo = (request.POST.get("folio_numero") or "").strip()
    if not crudo.isdigit() or int(crudo) <= 0:
        messages.error(request, "No se generó el oficio: el número de folio no es válido.")
        return None
    return int(crudo)


@require_POST
def oficio_comite_alumno(request, comite_id):
    comite = get_object_or_404(ComiteTutorial.objects.select_related("alumno", "acta"), pk=comite_id)
    folio_numero = _folio_numero_desde_form(request, comite.alumno_id)
    if folio_numero is None:
        return redirect("alumnos:detalle", alumno_id=comite.alumno_id)

    anio = date.today().year
    folios.usar_folio("oficio_comite_tutorial", folio_numero, anio)
    coordinador_nombre = obtener_config("coordinador_nombre")
    lema_ciclo = obtener_config("lema_ciclo")
    buffer = generador.generar_oficio_comite_tutorial_alumno(
        comite=comite, folio_numero=folio_numero, anio=anio,
        coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
    )
    nombre = f"Oficio comite tutorial - {comite.alumno.nombre.title()}.docx"
    return _descargar(buffer, nombre)


@require_POST
def oficio_comite_docente(request, comite_id, profesor_id):
    comite = get_object_or_404(ComiteTutorial.objects.select_related("alumno", "acta"), pk=comite_id)
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    if not comite.miembros.filter(profesor_id=profesor_id).exists():
        return redirect("alumnos:detalle", alumno_id=comite.alumno_id)

    folio_numero = _folio_numero_desde_form(request, comite.alumno_id)
    if folio_numero is None:
        return redirect("alumnos:detalle", alumno_id=comite.alumno_id)

    anio = date.today().year
    folios.usar_folio("oficio_comite_tutorial", folio_numero, anio)
    coordinador_nombre = obtener_config("coordinador_nombre")
    lema_ciclo = obtener_config("lema_ciclo")
    buffer = generador.generar_oficio_comite_tutorial_docente(
        comite=comite, profesor_destinatario=profesor, folio_numero=folio_numero, anio=anio,
        coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
    )
    nombre = f"Oficio comite tutorial - {profesor.nombre} - {comite.alumno.nombre.title()}.docx"
    return _descargar(buffer, nombre)


# --------------------------------------------------------- Taller de plantillas

def index(request):
    todos = TipoDocumentoPersonalizado.objects.all()
    if request.method == "POST":
        for clave in CLAVES_CONFIG_DOCUMENTOS:
            if clave in request.POST:
                config.establecer(clave, request.POST.get(clave, "").strip())
        messages.success(request, "Configuración guardada.")
        return redirect("documentos:index")

    moldes = {m.categoria: m for m in PlantillaBase.objects.all()}
    ejemplos = ejemplos_variables()
    variables_buscables = [
        {"grupo": grupo, "clave": clave, "etiqueta": etiqueta, "ejemplo": str(ejemplos.get(clave, ""))}
        for grupo, campos in GRUPOS_VARIABLES.items()
        for clave, etiqueta in campos.items()
    ]
    listas_disponibles = [{"clave": clave, "etiqueta": etiqueta} for clave, etiqueta in LISTAS_DISPONIBLES.items()]
    return render(request, "documentos/index.html", {
        "config": {clave: obtener_config(clave) for clave in CLAVES_CONFIG_DOCUMENTOS},
        "moldes": moldes,
        "tipos_oficio": [t for t in todos if t.categoria == "oficio"],
        "tipos_constancia": [t for t in todos if t.categoria == "constancia"],
        "variables_buscables": variables_buscables,
        "listas_disponibles": listas_disponibles,
    })


def plantilla_ejemplo(request):
    """Descarga la plantilla de comité tutorial ya en uso (real, no
    inventada) como ejemplo de cómo debe quedar un .docx preparado a
    mano: membrete intacto + {{ variables }} escritas directo en el
    cuerpo — la referencia que pide la documentación de abajo."""
    ruta = generador.TEMPLATES_DIR / EJEMPLO_PLANTILLA_ARCHIVO
    return _descargar(open(ruta, "rb"), EJEMPLO_PLANTILLA_ARCHIVO)


@require_POST
def subir_molde(request, categoria):
    if categoria not in CATEGORIAS_VALIDAS:
        messages.error(request, "Categoría inválida.")
        return redirect("documentos:index")
    try:
        tipos.guardar_molde_base(categoria, request.FILES.get("archivo"), usuario=request.user.get_username())
        messages.success(request, f"Molde base de {categoria} actualizado.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("documentos:index")


def tipos_nuevo(request):
    if request.method == "POST":
        try:
            tipo = tipos.crear_tipo(
                etiqueta=request.POST.get("etiqueta", ""),
                categoria=request.POST.get("categoria", ""),
                descripcion=request.POST.get("descripcion", ""),
                archivo=request.FILES.get("archivo"),
                usuario=request.user.get_username(),
            )
            messages.success(request, f'"{tipo.etiqueta}" creado — ya aparece como opción en Actas.')
            return redirect("documentos:tipos_detalle", tipo_id=tipo.id)
        except ValueError as exc:
            messages.error(request, str(exc))
    categoria_sugerida = request.GET.get("categoria", "oficio")
    return render(request, "documentos/tipos_nuevo.html", {"categoria_sugerida": categoria_sugerida})


def tipos_detalle(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    return render(request, "documentos/tipos_detalle.html", {"tipo": tipo})


@require_POST
def tipos_reemplazar(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    try:
        tipos.reemplazar_plantilla(tipo, request.FILES.get("archivo"), usuario=request.user.get_username())
        messages.success(request, "Plantilla reemplazada.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("documentos:tipos_detalle", tipo_id=tipo.id)


@require_POST
def tipos_editar(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    try:
        tipos.actualizar_metadatos(
            tipo, etiqueta=request.POST.get("etiqueta", ""), descripcion=request.POST.get("descripcion", ""),
            usuario=request.user.get_username(),
        )
        messages.success(request, "Datos actualizados.")
    except ValueError as exc:
        messages.error(request, str(exc))
    return redirect("documentos:tipos_detalle", tipo_id=tipo.id)


@require_POST
def tipos_eliminar(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    etiqueta = tipo.etiqueta
    tipos.eliminar_tipo(tipo, usuario=request.user.get_username())
    messages.success(request, f'"{etiqueta}" eliminado.')
    return redirect("documentos:index")


def tipos_vista_previa(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    try:
        buffer = tipos.generar_vista_previa(tipo)
    except PlantillaFaltanteError as exc:
        messages.error(request, str(exc))
        return redirect("documentos:tipos_detalle", tipo_id=tipo.id)
    return _descargar(buffer, _nombre_archivo(f"Vista previa {tipo.etiqueta}"))


# --------------------------------------- Generación de oficios/constancias
# (dirección, lector, sinodal, acta, personalizado) — a diferencia de los
# de comité tutorial (arriba), estos SÍ usan un solo folio automático por
# clic (siguiente_folio_formateado), no piden confirmar el número: cada
# botón genera un documento distinto, no hace falta que varias cartas
# compartan el mismo folio como pasa con comité tutorial (alumno + hasta 3
# tutores deben llevar el mismo número).

@require_POST
def documento_direccion(request, direccion_id):
    direccion = get_object_or_404(Direccion.objects.select_related("alumno", "profesor", "acta"), pk=direccion_id)
    tipo = request.POST.get("tipo")
    coordinador_nombre, lema_ciclo = _coordinador_y_lema()

    if tipo == "oficio":
        buffer = generador.generar_oficio_direccion(direccion=direccion, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre = _nombre_archivo(f"Oficio {direccion.rol} {direccion.alumno.nombre}")
    elif tipo == "constancia":
        buffer = generador.generar_constancia_direccion(direccion=direccion, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre = _nombre_archivo(f"Constancia {direccion.rol} {direccion.alumno.nombre}")
    else:
        messages.error(request, "Tipo de documento no reconocido.")
        return redirect("alumnos:detalle", alumno_id=direccion.alumno_id)

    return _descargar(buffer, nombre)


@require_POST
def documento_lector(request, lector_id):
    lector = get_object_or_404(Lector.objects.select_related("alumno", "profesor"), pk=lector_id)
    coordinador_nombre, lema_ciclo = _coordinador_y_lema()
    buffer = generador.generar_constancia_lector(lector=lector, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
    return _descargar(buffer, _nombre_archivo(f"Constancia Lector {lector.profesor.nombre}"))


@require_POST
def documento_sinodal(request, sinodal_id):
    sinodal = get_object_or_404(Sinodal.objects.select_related("alumno", "profesor", "acta"), pk=sinodal_id)
    tipo = request.POST.get("tipo")
    coordinador_nombre, lema_ciclo = _coordinador_y_lema()

    if tipo == "constancia":
        buffer = generador.generar_constancia_jurado(sinodal=sinodal, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre = _nombre_archivo(f"Constancia Jurado {sinodal.profesor.nombre}")
    elif tipo == "invitacion":
        buffer = generador.generar_oficio_invitacion_jurado(sinodal=sinodal, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre = _nombre_archivo(f"Oficio Invitacion Jurado {sinodal.profesor.nombre}")
    else:
        messages.error(request, "Tipo de documento no reconocido.")
        return redirect("alumnos:detalle", alumno_id=sinodal.alumno_id)

    return _descargar(buffer, nombre)


def documento_acta(request, acta_id):
    acta = get_object_or_404(Acta.objects.prefetch_related("puntos"), pk=acta_id)
    coordinador_nombre, lema_ciclo = _coordinador_y_lema()
    buffer = generador.generar_acta(acta=acta, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
    return _descargar(buffer, _nombre_archivo(f"Acta {acta.numero}"))


@require_POST
def documento_personalizado(request, punto_id):
    punto = get_object_or_404(
        PuntoActa.objects.select_related("alumno", "profesor", "acta", "direccion", "comite_tutorial", "tipo_documento")
        .prefetch_related("miembros__profesor"),
        pk=punto_id,
    )
    if punto.tipo_documento_id is None:
        messages.error(request, "Este punto no tiene un tipo de documento personalizado asociado.")
        return redirect("actas:detalle", acta_id=punto.acta_id)

    coordinador_nombre, lema_ciclo = _coordinador_y_lema()
    try:
        buffer = generador.generar_documento_personalizado(
            tipo_documento=punto.tipo_documento, punto=punto, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
        )
    except CamposFaltantesError as exc:
        messages.error(request, f"No se generó el documento — {exc}")
        return redirect("actas:detalle", acta_id=punto.acta_id)
    return _descargar(buffer, _nombre_archivo(f"{punto.tipo_documento.etiqueta} {punto.titulo}"))
