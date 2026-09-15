from django.urls import path

from . import views

app_name = "actas"

urlpatterns = [
    path("", views.listar, name="listar"),
    path("<int:acta_id>", views.detalle, name="detalle"),
]
