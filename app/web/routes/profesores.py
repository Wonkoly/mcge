from urllib.parse import urlencode

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models.profesor import TRATAMIENTOS
from app.repositories.catalogo_repository import listar_lies
from app.repositories.comite_repository import membresias_de_profesor
from app.repositories.direccion_repository import direcciones_de_profesor
from app.repositories.profesor_repository import (
    buscar_profesores_filtrado,
    obtener_profesor,
    valores_distintos_dedicacion,
    valores_distintos_sni,
)
from app.services.profesor_service import (
    NombreDuplicadoError,
    actualizar_profesor,
    crear_profesor,
    resumen_direcciones,
)
from app.web.db import get_session

bp = Blueprint("profesores", __name__, url_prefix="/profesores")


def _filtros_desde_form():
    return dict(
        texto=request.args.get("q", ""),
        tratamiento=request.args.get("tratamiento", ""),
        sni=request.args.get("sni", ""),
        dedicacion=request.args.get("dedicacion", ""),
        lies_id=request.args.get("lies_id", ""),
        nucleo=request.args.get("nucleo", ""),
        orden=request.args.get("orden", "nombre"),
    )


@bp.route("/")
def listar():
    session = get_session()
    filtros = _filtros_desde_form()
    resultados = buscar_profesores_filtrado(session, **filtros)
    filtros_sin_orden = {k: v for k, v in filtros.items() if k != "orden" and v}

    contexto = dict(
        resultados=resultados,
        filtros=filtros,
        filtros_qs=urlencode(filtros_sin_orden),
        tratamientos=TRATAMIENTOS,
        sni_opciones=valores_distintos_sni(session),
        dedicacion_opciones=valores_distintos_dedicacion(session),
        lies_opciones=listar_lies(session),
    )
    if request.headers.get("HX-Request"):
        return render_template("profesores/_tabla.html", **contexto)
    return render_template("profesores/list.html", **contexto)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            profesor = crear_profesor(session, **request.form)
            session.commit()
            flash(f"Profesor {profesor.nombre} agregado.", "exito")
            return redirect(url_for("profesores.listar"))
        except NombreDuplicadoError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("profesores/nuevo.html", tratamientos=TRATAMIENTOS)


@bp.route("/<int:profesor_id>")
def detalle(profesor_id):
    session = get_session()
    profesor = obtener_profesor(session, profesor_id)
    if profesor is None:
        flash("Profesor no encontrado.", "error")
        return redirect(url_for("profesores.listar"))

    direcciones = direcciones_de_profesor(session, profesor_id)
    membresias = membresias_de_profesor(session, profesor_id)
    num_alumnos_vigentes = sum(1 for d in direcciones if d.vigente)
    return render_template(
        "profesores/detalle.html",
        profesor=profesor,
        direcciones=direcciones,
        membresias=membresias,
        num_alumnos_vigentes=num_alumnos_vigentes,
        resumen=resumen_direcciones(profesor, direcciones),
    )


@bp.route("/<int:profesor_id>/editar", methods=["GET", "POST"])
def editar(profesor_id):
    session = get_session()
    profesor = obtener_profesor(session, profesor_id)
    if profesor is None:
        flash("Profesor no encontrado.", "error")
        return redirect(url_for("profesores.listar"))

    if request.method == "POST":
        try:
            actualizar_profesor(session, profesor, **request.form)
            session.commit()
            flash(f"Profesor {profesor.nombre} actualizado.", "exito")
            return redirect(url_for("profesores.detalle", profesor_id=profesor.id))
        except NombreDuplicadoError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("profesores/editar.html", profesor=profesor, tratamientos=TRATAMIENTOS)
