from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.acta_repository import listar_actas, obtener_acta
from app.services.acta_service import NumeroDuplicadoError, actualizar_acta, crear_acta
from app.web.db import get_session

bp = Blueprint("actas", __name__, url_prefix="/actas")


def _puntos_desde_form(form) -> list[dict]:
    titulos = form.getlist("punto_titulo")
    resolutivos = form.getlist("punto_resolutivo")
    return [
        {"titulo": t, "resolutivo": r}
        for t, r in zip(titulos, resolutivos)
        if t.strip()
    ]


@bp.route("/")
def listar():
    session = get_session()
    actas = listar_actas(session)
    return render_template("actas/list.html", actas=actas)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            acta = crear_acta(session, puntos=_puntos_desde_form(request.form), **request.form)
            session.commit()
            flash(f"Acta {acta.numero} creada.", "exito")
            return redirect(url_for("actas.detalle", acta_id=acta.id))
        except (NumeroDuplicadoError, ValueError) as exc:
            flash(str(exc), "error")
    return render_template("actas/formulario.html", acta=None)


@bp.route("/<int:acta_id>")
def detalle(acta_id):
    session = get_session()
    acta = obtener_acta(session, acta_id)
    if acta is None:
        flash("Acta no encontrada.", "error")
        return redirect(url_for("actas.listar"))
    return render_template("actas/detalle.html", acta=acta)


@bp.route("/<int:acta_id>/editar", methods=["GET", "POST"])
def editar(acta_id):
    session = get_session()
    acta = obtener_acta(session, acta_id)
    if acta is None:
        flash("Acta no encontrada.", "error")
        return redirect(url_for("actas.listar"))

    if request.method == "POST":
        try:
            actualizar_acta(session, acta, puntos=_puntos_desde_form(request.form), **request.form)
            session.commit()
            flash(f"Acta {acta.numero} actualizada.", "exito")
            return redirect(url_for("actas.detalle", acta_id=acta.id))
        except (NumeroDuplicadoError, ValueError) as exc:
            flash(str(exc), "error")
    return render_template("actas/formulario.html", acta=acta)
