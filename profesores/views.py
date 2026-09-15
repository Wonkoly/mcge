from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from actas.queries import direcciones_de_profesor, membresias_de_profesor
from profesores import services
from profesores.models import Profesor, TRATAMIENTOS


def _filtros_desde_form(request):
    return dict(
        texto=request.GET.get("q", ""),
        tratamiento=request.GET.getlist("tratamiento"),
        sni=request.GET.getlist("sni"),
        dedicacion=request.GET.getlist("dedicacion"),
        lies_id=request.GET.getlist("lies_id"),
        nucleo=request.GET.getlist("nucleo"),
        orden=request.GET.get("orden", "nombre"),
    )


def listar(request):
    from core.models import Lies

    filtros = _filtros_desde_form(request)
    resultados = services.buscar_profesores_filtrado(**filtros)
    filtros_sin_orden = {k: v for k, v in filtros.items() if k != "orden" and v}

    contexto = dict(
        resultados=resultados,
        filtros=filtros,
        filtros_qs=urlencode(filtros_sin_orden, doseq=True),
        tratamientos=TRATAMIENTOS,
        tratamiento_opciones=[(t, t) for t in TRATAMIENTOS],
        nucleo_opciones=[("si", "Sí (núcleo)"), ("no", "Externo")],
        sni_opciones=services.valores_distintos_sni(),
        dedicacion_opciones=services.valores_distintos_dedicacion(),
        lies_opciones=Lies.objects.order_by("nombre"),
    )
    plantilla = "profesores/_tabla.html" if request.headers.get("HX-Request") else "profesores/list.html"
    return render(request, plantilla, contexto)


def nuevo(request):
    if request.method == "POST":
        try:
            profesor = services.crear_profesor(usuario=request.user.get_username(), **request.POST.dict())
            messages.success(request, f"Profesor {profesor.nombre} agregado.")
            return redirect("profesores:listar")
        except (services.NombreDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(request, "profesores/nuevo.html", {"tratamientos": TRATAMIENTOS})


def detalle(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    direcciones = direcciones_de_profesor(profesor_id)
    membresias = membresias_de_profesor(profesor_id)
    num_alumnos_vigentes = sum(1 for d in direcciones if d.vigente)
    return render(
        request,
        "profesores/detalle.html",
        {
            "profesor": profesor,
            "direcciones": direcciones,
            "membresias": membresias,
            "num_alumnos_vigentes": num_alumnos_vigentes,
            "resumen": services.resumen_direcciones(profesor, direcciones),
        },
    )


def editar(request, profesor_id):
    profesor = get_object_or_404(Profesor, pk=profesor_id)
    if request.method == "POST":
        try:
            services.actualizar_profesor(profesor, usuario=request.user.get_username(), **request.POST.dict())
            messages.success(request, f"Profesor {profesor.nombre} actualizado.")
            return redirect("profesores:detalle", profesor_id=profesor.id)
        except (services.NombreDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(request, "profesores/editar.html", {"profesor": profesor, "tratamientos": TRATAMIENTOS})
