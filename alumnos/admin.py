from django.contrib import admin

from alumnos.models import Alumno


@admin.register(Alumno)
class AlumnoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "ciclo_ingreso", "status")
    list_filter = ("status",)
    search_fields = ("codigo", "nombre")
