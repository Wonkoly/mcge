from django.urls import path

from . import views

app_name = "aspirantes"

urlpatterns = [
    path("", views.listar, name="listar"),
]
