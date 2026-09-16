import re
from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from actas.models import ComiteTutorial
from core.configuracion import obtener as obtener_config
from documentos import folios, generador, tipos
from documentos.contexto import GRUPOS_VARIABLES, LISTAS_DISPONIBLES, ejemplos_variables, variables_libres
from documentos.models import PlantillaBase, TipoDocumentoPersonalizado
from documentos.tipos import CATEGORIAS_VALIDAS, MoldeFaltanteError
from profesores.models import Profesor


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
    moldes = {m.categoria: m for m in PlantillaBase.objects.all()}
    return render(request, "documentos/index.html", {
        "moldes": moldes,
        "tipos_oficio": [t for t in todos if t.categoria == "oficio"],
        "tipos_constancia": [t for t in todos if t.categoria == "constancia"],
    })


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
                usuario=request.user.get_username(),
            )
            return redirect("documentos:tipos_detalle", tipo_id=tipo.id)
        except ValueError as exc:
            messages.error(request, str(exc))
    categoria_sugerida = request.GET.get("categoria", "oficio")
    return render(request, "documentos/tipos_nuevo.html", {"categoria_sugerida": categoria_sugerida})


def tipos_detalle(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)

    if request.method == "POST":
        tipos.actualizar_cuerpo(tipo, request.POST.get("cuerpo_texto", ""), usuario=request.user.get_username())
        messages.success(request, "Cuerpo guardado.")
        return redirect("documentos:tipos_detalle", tipo_id=tipo.id)

    ejemplos = ejemplos_variables()
    variables_buscables = [
        {"grupo": grupo, "clave": clave, "etiqueta": etiqueta, "ejemplo": str(ejemplos.get(clave, ""))}
        for grupo, campos in GRUPOS_VARIABLES.items()
        for clave, etiqueta in campos.items()
    ]
    listas_disponibles = [{"clave": clave, "etiqueta": etiqueta} for clave, etiqueta in LISTAS_DISPONIBLES.items()]

    return render(request, "documentos/tipos_detalle.html", {
        "tipo": tipo,
        "molde": PlantillaBase.objects.filter(pk=tipo.categoria).first(),
        "variables_buscables": variables_buscables,
        "listas_disponibles": listas_disponibles,
        "libres": variables_libres(tipo.cuerpo_texto or ""),
    })


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
    except MoldeFaltanteError as exc:
        messages.error(request, str(exc))
        return redirect("documentos:tipos_detalle", tipo_id=tipo.id)
    return _descargar(buffer, _nombre_archivo(f"Vista previa {tipo.etiqueta}"))


@require_POST
def tipos_confirmar(request, tipo_id):
    tipo = get_object_or_404(TipoDocumentoPersonalizado, pk=tipo_id)
    try:
        tipos.confirmar_tipo(tipo, usuario=request.user.get_username())
        messages.success(request, f'"{tipo.etiqueta}" confirmado — ya aparece como opción en Actas.')
    except MoldeFaltanteError as exc:
        messages.error(request, str(exc))
    return redirect("documentos:tipos_detalle", tipo_id=tipo.id)
