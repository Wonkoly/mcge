from datetime import datetime

from django.contrib import messages
from django.shortcuts import redirect, render

from core import configuracion
from core.backup import crear_respaldo, listar_respaldos, restaurar_respaldo as _restaurar_respaldo


def inicio(request):
    return render(request, "core/inicio.html")


def configuracion_view(request):
    if request.method == "POST":
        for clave in configuracion.CLAVES_DEFAULT:
            if clave in request.POST:
                configuracion.establecer(clave, request.POST.get(clave, "").strip())
        messages.success(request, "Configuración guardada.")
        return redirect("core:configuracion")

    respaldos = [
        {"nombre": p.name, "tamano_kb": round(p.stat().st_size / 1024), "fecha": datetime.fromtimestamp(p.stat().st_mtime)}
        for p in listar_respaldos()
    ]
    return render(
        request,
        "core/configuracion.html",
        {"config": configuracion.obtener_todas(), "respaldos": respaldos},
    )


def generar_respaldo(request):
    destino = crear_respaldo()
    if destino:
        messages.success(request, f"Respaldo generado: {destino.name}")
    else:
        messages.error(request, "No se pudo generar el respaldo (¿todavía no existe la base de datos?).")
    return redirect("core:configuracion")


def restaurar_respaldo(request):
    nombre = request.POST.get("nombre")
    confirmacion = request.POST.get("confirmacion")
    if confirmacion != nombre:
        messages.error(request, "Confirmación incorrecta — no se restauró nada.")
        return redirect("core:configuracion")
    try:
        _restaurar_respaldo(nombre)
        messages.warning(
            request,
            f"Respaldo {nombre} restaurado. Cierra y vuelve a abrir la app para que quede todo limpio.",
        )
    except FileNotFoundError as exc:
        messages.error(request, str(exc))
    return redirect("core:configuracion")
