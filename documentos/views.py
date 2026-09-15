from datetime import date

from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from actas.models import ComiteTutorial
from core.configuracion import obtener as obtener_config
from documentos import folios, generador
from profesores.models import Profesor


def _descargar(buffer, nombre_archivo):
    respuesta = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return respuesta


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
