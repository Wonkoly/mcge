from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("configuracion/", views.configuracion_view, name="configuracion"),
    path("configuracion/respaldo/generar", views.generar_respaldo, name="generar_respaldo"),
    path("configuracion/respaldo/restaurar", views.restaurar_respaldo, name="restaurar_respaldo"),
]
