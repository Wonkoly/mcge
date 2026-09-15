from django.contrib import admin

from actas.models import Acta, ComiteMiembro, ComiteTutorial, Direccion, Lector, Sinodal


@admin.register(Acta)
class ActaAdmin(admin.ModelAdmin):
    list_display = ("numero", "fecha", "anio")
    search_fields = ("numero",)


@admin.register(Direccion)
class DireccionAdmin(admin.ModelAdmin):
    list_display = ("alumno", "profesor", "rol", "fecha_inicio", "fecha_fin")
    list_filter = ("rol",)


class ComiteMiembroInline(admin.TabularInline):
    model = ComiteMiembro
    extra = 0


@admin.register(ComiteTutorial)
class ComiteTutorialAdmin(admin.ModelAdmin):
    list_display = ("alumno", "ciclo", "fecha_inicio", "fecha_fin")
    inlines = [ComiteMiembroInline]


@admin.register(Lector)
class LectorAdmin(admin.ModelAdmin):
    list_display = ("alumno", "profesor", "fecha")


@admin.register(Sinodal)
class SinodalAdmin(admin.ModelAdmin):
    list_display = ("alumno", "profesor", "cargo", "fecha_examen")
    list_filter = ("cargo",)
