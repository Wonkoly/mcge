from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.alumno_repository import buscar_alumnos, obtener_alumno
from app.repositories.catalogo_repository import listar_lies, listar_status
from app.repositories.comite_repository import comite_vigente, historial_comites
from app.repositories.direccion_repository import direcciones_vigentes, historial_direcciones
from app.repositories.profesor_repository import listar_profesores
from app.services.alumno_service import CodigoDuplicadoError, actualizar_alumno, crear_alumno
from app.services.comite_service import asignar_comite_tutorial
from app.services.direccion_service import asignar_direccion
from app.web.db import get_session

bp = Blueprint("alumnos", __name__, url_prefix="/alumnos")


@bp.route("/")
def listar():
    session = get_session()
    texto = request.args.get("q", "")
    alumnos = buscar_alumnos(session, texto)
    return render_template("alumnos/list.html", alumnos=alumnos, texto=texto)


@bp.route("/nuevo", methods=["GET", "POST"])
def nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            alumno = crear_alumno(session, **request.form)
            session.commit()
            flash(f"Alumno {alumno.nombre} creado.", "exito")
            return redirect(url_for("alumnos.detalle", alumno_id=alumno.id))
        except CodigoDuplicadoError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("alumnos/nuevo.html", status_list=listar_status(session), lies_list=listar_lies(session))


@bp.route("/<int:alumno_id>/editar", methods=["GET", "POST"])
def editar(alumno_id):
    session = get_session()
    alumno = obtener_alumno(session, alumno_id)
    if alumno is None:
        flash("Alumno no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    if request.method == "POST":
        try:
            actualizar_alumno(session, alumno, **request.form)
            session.commit()
            flash(f"Alumno {alumno.nombre} actualizado.", "exito")
            return redirect(url_for("alumnos.detalle", alumno_id=alumno.id))
        except CodigoDuplicadoError as exc:
            flash(str(exc), "error")
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template(
        "alumnos/editar.html", alumno=alumno, status_list=listar_status(session), lies_list=listar_lies(session)
    )


@bp.route("/<int:alumno_id>")
def detalle(alumno_id):
    session = get_session()
    alumno = obtener_alumno(session, alumno_id)
    if alumno is None:
        flash("Alumno no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    comite = comite_vigente(session, alumno_id)
    vigentes = direcciones_vigentes(session, alumno_id)
    director = next((d for d in vigentes if d.rol == "Director"), None)
    codirector = next((d for d in vigentes if d.rol == "Codirector"), None)

    return render_template(
        "alumnos/detalle.html",
        alumno=alumno,
        comite=comite,
        historial_comite=historial_comites(session, alumno_id),
        director=director,
        codirector=codirector,
        historial_direccion=historial_direcciones(session, alumno_id),
        profesores=listar_profesores(session),
    )


@bp.route("/<int:alumno_id>/direccion", methods=["POST"])
def asignar_direccion_route(alumno_id):
    session = get_session()
    rol = request.form.get("rol")
    profesor_id = request.form.get("profesor_id", type=int)
    if not rol or not profesor_id:
        flash("Selecciona rol y profesor.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))

    _, aviso = asignar_direccion(session, alumno_id=alumno_id, profesor_id=profesor_id, rol=rol)
    session.commit()
    flash(f"{rol} asignado.", "exito")
    if aviso:
        flash(aviso, "aviso")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/comite", methods=["POST"])
def asignar_comite_route(alumno_id):
    session = get_session()
    profesor_ids = [int(pid) for pid in request.form.getlist("profesor_ids")]
    ciclo = request.form.get("ciclo") or None
    if not profesor_ids:
        flash("Selecciona al menos un profesor para el comité tutorial.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))

    asignar_comite_tutorial(session, alumno_id=alumno_id, profesor_ids=profesor_ids, ciclo=ciclo)
    session.commit()
    flash("Comité tutorial actualizado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))
