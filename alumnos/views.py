from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

from actas import queries as actas_queries
from actas import services as actas_services
from alumnos import services
from alumnos.models import Alumno
from core.configuracion import ciclo_escolar_vigente
from core.fechas import PROGRAMA_SEMESTRES, semestre_desde_ciclo


def _filtros_desde_form(request):
    return dict(
        texto=request.GET.get("q", ""),
        ciclo_ingreso=request.GET.getlist("ciclo_ingreso"),
        status_codigo=request.GET.getlist("status_codigo"),
        categoria=request.GET.getlist("categoria"),
        lies_id=request.GET.getlist("lies_id"),
        director_id=request.GET.getlist("director_id"),
        dictamen=request.GET.getlist("dictamen"),
        creditos_min=request.GET.get("creditos_min", ""),
        creditos_max=request.GET.get("creditos_max", ""),
        orden=request.GET.get("orden", "nombre"),
    )


def listar(request):
    from core.models import Lies, StatusAlumno
    from profesores.models import Profesor

    filtros = _filtros_desde_form(request)
    alumnos = services.buscar_alumnos_filtrado(**filtros)
    filtros_sin_orden = {k: v for k, v in filtros.items() if k != "orden" and v}
    status_list = list(StatusAlumno.objects.order_by("codigo"))

    contexto = dict(
        alumnos=alumnos,
        filtros=filtros,
        filtros_qs=urlencode(filtros_sin_orden, doseq=True),
        status_list=status_list,
        status_opciones=[(s.codigo, s.nombre) for s in status_list],
        lies_list=Lies.objects.order_by("nombre"),
        directores=Profesor.objects.filter(activo=True).order_by("nombre"),
        ciclo_opciones=[(c, c) for c in services.valores_distintos_ciclo_ingreso()],
        dictamen_opciones=services.valores_distintos_dictamen(),
    )
    plantilla = "alumnos/_tabla.html" if request.headers.get("HX-Request") else "alumnos/list.html"
    return render(request, plantilla, contexto)


def nuevo(request):
    from core.models import Lies, StatusAlumno

    if request.method == "POST":
        try:
            alumno = services.crear_alumno(usuario=request.user.get_username(), **request.POST.dict())
            messages.success(request, f"Alumno {alumno.nombre} creado.")
            return redirect("alumnos:detalle", alumno_id=alumno.id)
        except (services.CodigoDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(
        request, "alumnos/nuevo.html",
        {"status_list": StatusAlumno.objects.order_by("codigo"), "lies_list": Lies.objects.order_by("nombre")},
    )


def editar(request, alumno_id):
    from core.models import Lies, StatusAlumno

    alumno = get_object_or_404(Alumno, pk=alumno_id)
    if request.method == "POST":
        try:
            services.actualizar_alumno(alumno, usuario=request.user.get_username(), **request.POST.dict())
            messages.success(request, f"Alumno {alumno.nombre} actualizado.")
            return redirect("alumnos:detalle", alumno_id=alumno.id)
        except (services.CodigoDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(
        request, "alumnos/editar.html",
        {"alumno": alumno, "status_list": StatusAlumno.objects.order_by("codigo"), "lies_list": Lies.objects.order_by("nombre")},
    )


def detalle(request, alumno_id):
    from profesores.models import Profesor

    alumno = get_object_or_404(Alumno.objects.select_related("status", "lies"), pk=alumno_id)

    comite = actas_queries.comite_vigente(alumno_id)
    vigentes = actas_queries.direcciones_vigentes(alumno_id)
    director = next((d for d in vigentes if d.rol == "Director"), None)
    codirector = next((d for d in vigentes if d.rol == "Codirector"), None)
    ciclo_vigente = ciclo_escolar_vigente()
    semestre = semestre_desde_ciclo(alumno.ciclo_ingreso, ciclo_vigente)

    folio_sugerido_comite = None
    if comite:
        from documentos.folios import folio_sugerido

        folio_sugerido_comite = folio_sugerido("oficio_comite_tutorial")

    return render(
        request,
        "alumnos/detalle.html",
        {
            "alumno": alumno,
            "semestre": semestre,
            "semestre_maximo": PROGRAMA_SEMESTRES,
            "comite": comite,
            "folio_sugerido_comite": folio_sugerido_comite,
            "historial_comite": actas_queries.historial_comites(alumno_id),
            "director": director,
            "codirector": codirector,
            "historial_direccion": actas_queries.historial_direcciones(alumno_id),
            "profesores": Profesor.objects.filter(activo=True).order_by("nombre"),
            "lectores": actas_queries.lectores_de_alumno(alumno_id),
            "sinodales": actas_queries.sinodales_de_alumno(alumno_id),
        },
    )


def agregar_lector_route(request, alumno_id):
    profesor_id = request.POST.get("profesor_id")
    if not profesor_id:
        messages.error(request, "Selecciona un profesor para el lector.")
        return redirect("alumnos:detalle", alumno_id=alumno_id)
    actas_services.agregar_lector(
        alumno_id=alumno_id, profesor_id=int(profesor_id), fecha=request.POST.get("fecha"),
        usuario=request.user.get_username(),
    )
    messages.success(request, "Lector agregado.")
    return redirect("alumnos:detalle", alumno_id=alumno_id)


def quitar_lector_route(request, alumno_id, lector_id):
    from actas.models import Lector

    lector = Lector.objects.filter(pk=lector_id, alumno_id=alumno_id).first()
    if lector:
        actas_services.quitar_lector(lector, usuario=request.user.get_username())
        messages.success(request, "Lector eliminado.")
    return redirect("alumnos:detalle", alumno_id=alumno_id)


def agregar_sinodal_route(request, alumno_id):
    profesor_id = request.POST.get("profesor_id")
    cargo = request.POST.get("cargo")
    if not profesor_id or not cargo:
        messages.error(request, "Selecciona profesor y cargo para el sinodal.")
        return redirect("alumnos:detalle", alumno_id=alumno_id)
    actas_services.agregar_sinodal(
        alumno_id=alumno_id, profesor_id=int(profesor_id), cargo=cargo,
        fecha_examen=request.POST.get("fecha_examen"),
        hora_examen=request.POST.get("hora_examen"),
        lugar_examen=request.POST.get("lugar_examen"),
        usuario=request.user.get_username(),
    )
    messages.success(request, "Sinodal agregado.")
    return redirect("alumnos:detalle", alumno_id=alumno_id)


def quitar_sinodal_route(request, alumno_id, sinodal_id):
    from actas.models import Sinodal

    sinodal = Sinodal.objects.filter(pk=sinodal_id, alumno_id=alumno_id).first()
    if sinodal:
        actas_services.quitar_sinodal(sinodal, usuario=request.user.get_username())
        messages.success(request, "Sinodal eliminado.")
    return redirect("alumnos:detalle", alumno_id=alumno_id)
