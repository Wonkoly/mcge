from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.aspirante_repository import buscar_aspirantes, obtener_aspirante
from app.services.aspirante_service import aceptar_aspirante, cambiar_estado, crear_aspirante
from app.web.db import get_session

bp = Blueprint("aspirantes", __name__, url_prefix="/aspirantes")

ESTADOS = [
    "Registrado",
    "Documentación incompleta",
    "En evaluación",
    "Entrevista",
    "Aceptado",
    "No aceptado",
    "Inscrito",
]


@bp.route("/")
def listar():
    session = get_session()
    texto = request.args.get("q", "")
    aspirantes = buscar_aspirantes(session, texto)
    return render_template("aspirantes/list.html", aspirantes=aspirantes, texto=texto)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            aspirante = crear_aspirante(session, **request.form)
            session.commit()
            flash(f"Aspirante {aspirante.nombre} registrado.", "exito")
            return redirect(url_for("aspirantes.listar"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("aspirantes/nuevo.html", estados=ESTADOS)


@bp.route("/<int:aspirante_id>/estado", methods=["POST"])
def cambiar_estado_route(aspirante_id):
    session = get_session()
    aspirante = obtener_aspirante(session, aspirante_id)
    nuevo_estado = request.form.get("estado")
    if aspirante and nuevo_estado:
        cambiar_estado(session, aspirante, nuevo_estado)
        session.commit()
        flash(f"Estado de {aspirante.nombre} actualizado a {nuevo_estado}.", "exito")
    return redirect(url_for("aspirantes.listar"))


@bp.route("/<int:aspirante_id>/aceptar", methods=["POST"])
def aceptar_route(aspirante_id):
    session = get_session()
    aspirante = obtener_aspirante(session, aspirante_id)
    if aspirante is None:
        flash("Aspirante no encontrado.", "error")
        return redirect(url_for("aspirantes.listar"))
    try:
        alumno = aceptar_aspirante(session, aspirante, codigo_alumno=request.form.get("codigo_alumno", ""))
        session.commit()
        flash(f"{aspirante.nombre} convertido a alumno ({alumno.codigo}).", "exito")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno.id))
    except ValueError as exc:
        flash(str(exc), "error")
        return redirect(url_for("aspirantes.listar"))
