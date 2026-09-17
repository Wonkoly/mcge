from django.urls import path

from . import views

app_name = "documentos"

urlpatterns = [
    path("", views.index, name="index"),
    path("comite/<int:comite_id>/alumno", views.oficio_comite_alumno, name="oficio_comite_alumno"),
    path("comite/<int:comite_id>/docente/<int:profesor_id>", views.oficio_comite_docente, name="oficio_comite_docente"),
    path("moldes/<str:categoria>", views.subir_molde, name="subir_molde"),
    path("plantilla-ejemplo", views.plantilla_ejemplo, name="plantilla_ejemplo"),
    path("tipos/nuevo", views.tipos_nuevo, name="tipos_nuevo"),
    path("tipos/<int:tipo_id>", views.tipos_detalle, name="tipos_detalle"),
    path("tipos/<int:tipo_id>/reemplazar", views.tipos_reemplazar, name="tipos_reemplazar"),
    path("tipos/<int:tipo_id>/editar", views.tipos_editar, name="tipos_editar"),
    path("tipos/<int:tipo_id>/eliminar", views.tipos_eliminar, name="tipos_eliminar"),
    path("tipos/<int:tipo_id>/vista-previa", views.tipos_vista_previa, name="tipos_vista_previa"),
    path("direccion/<int:direccion_id>", views.documento_direccion, name="documento_direccion"),
    path("lector/<int:lector_id>", views.documento_lector, name="documento_lector"),
    path("sinodal/<int:sinodal_id>", views.documento_sinodal, name="documento_sinodal"),
    path("acta/<int:acta_id>", views.documento_acta, name="documento_acta"),
    path("personalizado/<int:punto_id>", views.documento_personalizado, name="documento_personalizado"),
]
