from django.contrib import admin

from profesores.models import Profesor, ProfesorAlias


class ProfesorAliasInline(admin.TabularInline):
    model = ProfesorAlias
    extra = 0


@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tratamiento", "nucleo_academico", "activo")
    list_filter = ("nucleo_academico", "activo", "tratamiento")
    search_fields = ("nombre",)
    inlines = [ProfesorAliasInline]
