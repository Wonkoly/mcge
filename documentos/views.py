from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from actas.models import ComiteTutorial
from core.configuracion import obtener as obtener_config
from documentos import generador
from profesores.models import Profesor


def _descargar(buffer, nombre_archivo):
    respuesta = HttpResponse(
        buffer.read(),
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    respuesta["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    return respuesta


@require_POST
def oficio_comite_alumno(request, comite_id):
    comite = get_object_or_404(ComiteTutorial.objects.select_related("alumno", "acta"), pk=comite_id)
    coordinador_nombre = obtener_config("coordinador_nombre")
    buffer = generador.generar_oficio_comite_tutorial_alumno(comite=comite, coordinador_nombre=coordinador_nombre)
    nombre = f"Oficio comite tutorial - {comite.alumno.nombre.title()}.docx"
    return _descargar(buffer, nombre)


@require_POST
def oficio_comite_docente(request, comite_id, profesor_id):
    comite = get_object_or_404(ComiteTutorial.objects.select_related("alumno", "acta"), pk=comite_id)
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    if not comite.miembros.filter(profesor_id=profesor_id).exists():
        return redirect("alumnos:detalle", alumno_id=comite.alumno_id)
    coordinador_nombre = obtener_config("coordinador_nombre")
    buffer = generador.generar_oficio_comite_tutorial_docente(comite=comite, profesor_destinatario=profesor, coordinador_nombre=coordinador_nombre)
    nombre = f"Oficio comite tutorial - {profesor.nombre} - {comite.alumno.nombre.title()}.docx"
    return _descargar(buffer, nombre)
