import json
import re

from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from actas import acta_service
from actas.acta_service import NumeroDuplicadoError, TIPOS_PUNTO_INFO
from actas.models import Acta
from alumnos.models import Alumno
from core.configuracion import ciclo_escolar_vigente
from documentos.models import TipoDocumentoPersonalizado
from profesores.models import Profesor

_PATRON_INDICE_PUNTO = re.compile(r"punto_tipo_(\d+)")
_PATRON_CAMPO_LIBRE = re.compile(r"punto_campo_(\d+)__(\w+)")


def listar(request):
    actas = Acta.objects.all()
    return render(request, "actas/list.html", {"actas": actas})


def detalle(request, acta_id):
    acta = get_object_or_404(
        Acta.objects.prefetch_related(
            "puntos__alumno", "puntos__profesor", "puntos__tipo_documento", "puntos__miembros__profesor",
            "direccion_set__alumno", "direccion_set__profesor",
            "comitetutorial_set__alumno", "comitetutorial_set__miembros__profesor",
            "lector_set__alumno", "lector_set__profesor",
            "sinodal_set__alumno", "sinodal_set__profesor",
        ),
        pk=acta_id,
    )
    return render(request, "actas/detalle.html", {"acta": acta})


def buscar_alumno(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)
    resultados = Alumno.objects.filter(Q(nombre__icontains=q) | Q(codigo__icontains=q)).order_by("nombre")[:15]
    return JsonResponse([{"id": a.id, "texto": f"{a.nombre} ({a.codigo})"} for a in resultados], safe=False)


def buscar_profesor(request):
    q = (request.GET.get("q") or "").strip()
    if not q:
        return JsonResponse([], safe=False)
    resultados = Profesor.objects.filter(nombre__icontains=q).order_by("nombre")[:15]
    return JsonResponse([{"id": p.id, "texto": p.nombre} for p in resultados], safe=False)


def _punto_a_json(punto) -> dict:
    base = {
        "_key": f"p{punto.id}", "punto_id": punto.id, "tipo": punto.tipo,
        "titulo": punto.titulo, "resolutivo": punto.resolutivo or "",
        "alumno_id": punto.alumno_id,
        "alumno_texto": f"{punto.alumno.nombre} ({punto.alumno.codigo})" if punto.alumno_id else "",
        "profesor_id": punto.profesor_id,
        "profesor_texto": punto.profesor.nombre if punto.profesor_id else "",
        "rol": punto.rol or "Director",
        "ciclo": punto.ciclo or "",
        "miembros": [{"id": m.profesor_id, "texto": m.profesor.nombre} for m in punto.miembros.all()],
        "tipo_documento_id": punto.tipo_documento_id,
        "tipo_documento_etiqueta": punto.tipo_documento.etiqueta if punto.tipo_documento_id else "",
        "campos_libres": json.loads(punto.datos_json) if punto.datos_json else {},
    }
    return base


def _puntos_desde_form(post) -> list[dict]:
    """Mismo esquema de nombres de campo que usaba Flask
    (`punto_tipo_{i}`, `punto_alumno_id_{i}`, ...), con un campo nuevo
    `punto_id_{i}` (vacío si el punto es nuevo) que usa
    acta_service._reemplazar_puntos para decidir si reutiliza el
    Direccion/ComiteTutorial ya creado — ver el docstring ahí."""
    indices = sorted(int(m.group(1)) for k in post.keys() if (m := _PATRON_INDICE_PUNTO.fullmatch(k)))

    campos_libres_por_indice: dict[int, dict[str, str]] = {}
    for k in post.keys():
        m = _PATRON_CAMPO_LIBRE.fullmatch(k)
        if m:
            i, clave = int(m.group(1)), m.group(2)
            campos_libres_por_indice.setdefault(i, {})[clave] = post.get(k, "")

    def _punto_id(i):
        crudo = post.get(f"punto_id_{i}")
        return int(crudo) if crudo and crudo.isdigit() else None

    puntos = []
    for i in indices:
        tipo = post.get(f"punto_tipo_{i}", "otro")
        punto_id = _punto_id(i)

        if tipo == "direccion":
            alumno_id = post.get(f"punto_alumno_id_{i}")
            profesor_id = post.get(f"punto_profesor_id_{i}")
            rol = post.get(f"punto_rol_{i}")
            if not (alumno_id and profesor_id and rol):
                continue
            puntos.append({
                "tipo": "direccion", "punto_id": punto_id,
                "alumno_id": int(alumno_id), "profesor_id": int(profesor_id), "rol": rol,
            })

        elif tipo == "comite_tutorial":
            alumno_id = post.get(f"punto_alumno_id_{i}")
            ciclo = post.get(f"punto_ciclo_{i}") or None
            miembro_ids = [int(v) for v in post.getlist(f"punto_miembro_ids_{i}")]
            if not (alumno_id and miembro_ids):
                continue
            puntos.append({
                "tipo": "comite_tutorial", "punto_id": punto_id,
                "alumno_id": int(alumno_id), "ciclo": ciclo, "miembro_ids": miembro_ids,
            })

        elif tipo == "personalizado":
            tipo_documento_id = post.get(f"punto_tipo_documento_id_{i}")
            titulo = (post.get(f"punto_titulo_{i}") or "").strip()
            if not (tipo_documento_id and titulo):
                continue
            alumno_id = post.get(f"punto_alumno_id_{i}")
            profesor_id = post.get(f"punto_profesor_id_{i}")
            puntos.append({
                "tipo": "personalizado", "punto_id": punto_id,
                "tipo_documento_id": int(tipo_documento_id), "titulo": titulo,
                "resolutivo": post.get(f"punto_resolutivo_{i}", ""),
                "alumno_id": int(alumno_id) if alumno_id else None,
                "profesor_id": int(profesor_id) if profesor_id else None,
                "miembro_ids": [int(v) for v in post.getlist(f"punto_profesores_lista_{i}")],
                "campos_libres": campos_libres_por_indice.get(i, {}),
            })

        else:
            titulo = (post.get(f"punto_titulo_{i}") or "").strip()
            if not titulo:
                continue
            puntos.append({
                "tipo": "otro", "punto_id": punto_id, "titulo": titulo, "resolutivo": post.get(f"punto_resolutivo_{i}", ""),
            })

    return puntos


def _contexto_formulario(acta=None) -> dict:
    puntos_json = [_punto_a_json(p) for p in acta.puntos.select_related("alumno", "profesor", "tipo_documento").prefetch_related("miembros__profesor").all()] if acta else []
    return {
        "acta": acta,
        "tipos_punto_info": TIPOS_PUNTO_INFO,
        "puntos_json": puntos_json,
        "ciclo_sugerido": ciclo_escolar_vigente(),
        "tipos_personalizados_confirmados": TipoDocumentoPersonalizado.objects.filter(estado="confirmado").order_by("etiqueta"),
    }


def nuevo(request):
    if request.method == "POST":
        try:
            acta, avisos = acta_service.crear_acta(
                usuario=request.user.get_username(), puntos=_puntos_desde_form(request.POST), **request.POST.dict(),
            )
            messages.success(request, f"Acta {acta.numero} creada.")
            for aviso in avisos:
                messages.warning(request, aviso)
            return redirect("actas:detalle", acta_id=acta.id)
        except (NumeroDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(request, "actas/formulario.html", _contexto_formulario())


def editar(request, acta_id):
    acta = get_object_or_404(Acta, pk=acta_id)
    if request.method == "POST":
        try:
            acta, avisos = acta_service.actualizar_acta(
                acta, usuario=request.user.get_username(), puntos=_puntos_desde_form(request.POST), **request.POST.dict(),
            )
            messages.success(request, f"Acta {acta.numero} actualizada.")
            for aviso in avisos:
                messages.warning(request, aviso)
            return redirect("actas:detalle", acta_id=acta.id)
        except (NumeroDuplicadoError, ValueError) as exc:
            messages.error(request, str(exc))
    return render(request, "actas/formulario.html", _contexto_formulario(acta))
