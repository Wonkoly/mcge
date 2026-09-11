from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.profesor_repository import listar_profesores
from app.services.profesor_service import NombreDuplicadoError, crear_profesor
from app.web.db import get_session

bp = Blueprint("profesores", __name__, url_prefix="/profesores")


@bp.route("/")
def listar():
    session = get_session()
    profesores = listar_profesores(session, solo_activos=False)
    return render_template("profesores/list.html", profesores=profesores)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            profesor = crear_profesor(session, **request.form, nucleo_academico=request.form.get("nucleo_academico"))
            session.commit()
            flash(f"Profesor {profesor.nombre} agregado.", "exito")
            return redirect(url_for("profesores.listar"))
        except NombreDuplicadoError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("profesores/nuevo.html")
