from django.shortcuts import render

from aspirantes.models import Aspirante


def listar(request):
    aspirantes = Aspirante.objects.exclude(estado__in=["Inscrito", "No aceptado"]).order_by("nombre")
    return render(request, "aspirantes/list.html", {"aspirantes": aspirantes})
