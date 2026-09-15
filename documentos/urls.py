from django.urls import path

from . import views

app_name = "documentos"

urlpatterns = [
    path("comite/<int:comite_id>/alumno", views.oficio_comite_alumno, name="oficio_comite_alumno"),
    path("comite/<int:comite_id>/docente/<int:profesor_id>", views.oficio_comite_docente, name="oficio_comite_docente"),
]
