from django.shortcuts import render

from core.configuracion import ciclo_escolar_vigente
from core.fechas import PROGRAMA_SEMESTRES
from dashboard import services


def inicio(request):
    ciclo_vigente = ciclo_escolar_vigente()
    return render(
        request,
        "dashboard/inicio.html",
        {
            "stats": services.estadisticas(),
            "ciclo_vigente": ciclo_vigente,
            "por_ciclo": services.alumnos_activos_por_ciclo(),
            "semestres": services.distribucion_semestres(ciclo_vigente),
            "programa_semestres": PROGRAMA_SEMESTRES,
            "limite_alumnos_profesor": services.LIMITE_ALUMNOS_POR_PROFESOR,
            "alertas": services.alertas(ciclo_vigente),
        },
    )
