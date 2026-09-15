from django.shortcuts import get_object_or_404, render

from actas.models import Acta


def listar(request):
    actas = Acta.objects.all()
    return render(request, "actas/list.html", {"actas": actas})


def detalle(request, acta_id):
    acta = get_object_or_404(
        Acta.objects.prefetch_related(
            "direccion_set__alumno", "direccion_set__profesor",
            "comitetutorial_set__alumno", "comitetutorial_set__miembros__profesor",
            "lector_set__alumno", "lector_set__profesor",
            "sinodal_set__alumno", "sinodal_set__profesor",
        ),
        pk=acta_id,
    )
    return render(request, "actas/detalle.html", {"acta": acta})
