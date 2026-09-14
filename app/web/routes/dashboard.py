from flask import Blueprint, render_template

from app.repositories.dashboard_repository import alumnos_activos_por_ciclo, estadisticas
from app.services.configuracion_service import ciclo_escolar_vigente
from app.services.dashboard_service import LIMITE_ALUMNOS_POR_PROFESOR, alertas, distribucion_semestres
from app.utils.fechas import PROGRAMA_SEMESTRES
from app.web.db import get_session

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def inicio():
    session = get_session()
    ciclo_vigente = ciclo_escolar_vigente(session)

    return render_template(
        "dashboard.html",
        stats=estadisticas(session),
        ciclo_vigente=ciclo_vigente,
        por_ciclo=alumnos_activos_por_ciclo(session),
        semestres=distribucion_semestres(session, ciclo_vigente),
        programa_semestres=PROGRAMA_SEMESTRES,
        limite_alumnos_profesor=LIMITE_ALUMNOS_POR_PROFESOR,
        alertas=alertas(session, ciclo_vigente),
    )
