from django.urls import path

from . import views

app_name = "actas"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("nuevo", views.nuevo, name="nuevo"),
    path("buscar-alumno", views.buscar_alumno, name="buscar_alumno"),
    path("buscar-profesor", views.buscar_profesor, name="buscar_profesor"),
    path("<int:acta_id>", views.detalle, name="detalle"),
    path("<int:acta_id>/editar", views.editar, name="editar"),
]
