from django.urls import path

from . import views

app_name = "alumnos"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("nuevo", views.nuevo, name="nuevo"),
    path("<int:alumno_id>", views.detalle, name="detalle"),
    path("<int:alumno_id>/editar", views.editar, name="editar"),
    path("<int:alumno_id>/lector", views.agregar_lector_route, name="agregar_lector_route"),
    path("<int:alumno_id>/lector/<int:lector_id>/quitar", views.quitar_lector_route, name="quitar_lector_route"),
    path("<int:alumno_id>/sinodal", views.agregar_sinodal_route, name="agregar_sinodal_route"),
    path("<int:alumno_id>/sinodal/<int:sinodal_id>/quitar", views.quitar_sinodal_route, name="quitar_sinodal_route"),
]
