from django.contrib import admin

from core.models import Configuracion, HistorialCambio, Lies, StatusAlumno


@admin.register(StatusAlumno)
class StatusAlumnoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "categoria", "confirmado")


@admin.register(Lies)
class LiesAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")


@admin.register(Configuracion)
class ConfiguracionAdmin(admin.ModelAdmin):
    list_display = ("clave", "valor")


@admin.register(HistorialCambio)
class HistorialCambioAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "entidad", "entidad_id", "accion", "campo")
    list_filter = ("entidad", "accion")
    readonly_fields = [f.name for f in HistorialCambio._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
