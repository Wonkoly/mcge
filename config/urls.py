from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cuentas/", include("accounts.urls")),
    path("actas/", include("actas.urls")),
    path("profesores/", include("profesores.urls")),
    path("alumnos/", include("alumnos.urls")),
    path("", include("core.urls")),
]
