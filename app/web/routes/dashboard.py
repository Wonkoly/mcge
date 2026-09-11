from flask import Blueprint, render_template

from app.repositories.dashboard_repository import estadisticas
from app.web.db import get_session

bp = Blueprint("dashboard", __name__)


@bp.route("/")
def inicio():
    stats = estadisticas(get_session())
    return render_template("dashboard.html", stats=stats)
