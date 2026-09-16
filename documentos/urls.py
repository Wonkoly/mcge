from django.urls import path

from . import views

app_name = "documentos"

urlpatterns = [
    path("", views.index, name="index"),
    path("comite/<int:comite_id>/alumno", views.oficio_comite_alumno, name="oficio_comite_alumno"),
    path("comite/<int:comite_id>/docente/<int:profesor_id>", views.oficio_comite_docente, name="oficio_comite_docente"),
    path("moldes/<str:categoria>", views.subir_molde, name="subir_molde"),
    path("tipos/nuevo", views.tipos_nuevo, name="tipos_nuevo"),
    path("tipos/<int:tipo_id>", views.tipos_detalle, name="tipos_detalle"),
    path("tipos/<int:tipo_id>/editar", views.tipos_editar, name="tipos_editar"),
    path("tipos/<int:tipo_id>/eliminar", views.tipos_eliminar, name="tipos_eliminar"),
    path("tipos/<int:tipo_id>/vista-previa", views.tipos_vista_previa, name="tipos_vista_previa"),
    path("tipos/<int:tipo_id>/confirmar", views.tipos_confirmar, name="tipos_confirmar"),
]
