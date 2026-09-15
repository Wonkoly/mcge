from django.urls import path

from . import views

app_name = "profesores"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("nuevo", views.nuevo, name="nuevo"),
    path("<int:profesor_id>", views.detalle, name="detalle"),
    path("<int:profesor_id>/editar", views.editar, name="editar"),
]
