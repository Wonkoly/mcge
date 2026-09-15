from django.contrib import admin

from aspirantes.models import Aspirante


@admin.register(Aspirante)
class AspiranteAdmin(admin.ModelAdmin):
    list_display = ("nombre", "ciclo", "estado")
    list_filter = ("estado",)
    search_fields = ("nombre",)
