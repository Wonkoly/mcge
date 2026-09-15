from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("accounts.urls")),
    path("actas/", include("actas.urls")),
    path("profesores/", include("profesores.urls")),
    path("alumnos/", include("alumnos.urls")),
    path("aspirantes/", include("aspirantes.urls")),
    path("documentos/", include("documentos.urls")),
    path("", include("core.urls")),
    path("", include("dashboard.urls")),
]
