from urllib.parse import urlencode

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.models import Lector, Sinodal
from app.repositories.acta_repository import listar_actas
from app.repositories.alumno_repository import (
    buscar_alumnos_filtrado,
    obtener_alumno,
    valores_distintos_ciclo_ingreso,
    valores_distintos_dictamen,
)
from app.repositories.catalogo_repository import listar_lies, listar_status
from app.repositories.comite_repository import comite_vigente, historial_comites
from app.repositories.direccion_repository import direcciones_vigentes, historial_direcciones
from app.repositories.profesor_repository import listar_profesores
from app.repositories.titulacion_repository import lectores_de_alumno, sinodales_de_alumno
from app.services.alumno_service import CodigoDuplicadoError, actualizar_alumno, crear_alumno
from app.services.comite_service import asignar_comite_tutorial
from app.services.direccion_service import asignar_direccion
from app.services.configuracion_service import ciclo_escolar_vigente
from app.services.titulacion_service import agregar_lector, agregar_sinodal, quitar_lector, quitar_sinodal
from app.utils.fechas import PROGRAMA_SEMESTRES, semestre_desde_ciclo
from app.web.db import get_session

bp = Blueprint("alumnos", __name__, url_prefix="/alumnos")


def _filtros_desde_form():
    return dict(
        texto=request.args.get("q", ""),
        ciclo_ingreso=request.args.get("ciclo_ingreso", ""),
        status_codigo=request.args.get("status_codigo", ""),
        categoria=request.args.get("categoria", ""),
        lies_id=request.args.get("lies_id", ""),
        director_id=request.args.get("director_id", ""),
        dictamen=request.args.get("dictamen", ""),
        creditos_min=request.args.get("creditos_min", ""),
        creditos_max=request.args.get("creditos_max", ""),
        orden=request.args.get("orden", "nombre"),
    )


@bp.route("/")
def listar():
    session = get_session()
    filtros = _filtros_desde_form()
    alumnos = buscar_alumnos_filtrado(session, **filtros)
    filtros_sin_orden = {k: v for k, v in filtros.items() if k != "orden" and v}

    contexto = dict(
        alumnos=alumnos,
        filtros=filtros,
        filtros_qs=urlencode(filtros_sin_orden),
        status_list=listar_status(session),
        lies_list=listar_lies(session),
        directores=listar_profesores(session),
        ciclo_opciones=valores_distintos_ciclo_ingreso(session),
        dictamen_opciones=valores_distintos_dictamen(session),
    )
    if request.headers.get("HX-Request"):
        return render_template("alumnos/_tabla.html", **contexto)
    return render_template("alumnos/list.html", **contexto)


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
    ciclo_vigente = ciclo_escolar_vigente(session)
    semestre = semestre_desde_ciclo(alumno.ciclo_ingreso, ciclo_vigente)

    return render_template(
        "alumnos/detalle.html",
        alumno=alumno,
        semestre=semestre,
        semestre_maximo=PROGRAMA_SEMESTRES,
        comite=comite,
        historial_comite=historial_comites(session, alumno_id),
        director=director,
        codirector=codirector,
        historial_direccion=historial_direcciones(session, alumno_id),
        profesores=listar_profesores(session),
        ciclo_sugerido=ciclo_escolar_vigente(session),
        lectores=lectores_de_alumno(session, alumno_id),
        sinodales=sinodales_de_alumno(session, alumno_id),
        actas=listar_actas(session),
    )


@bp.route("/<int:alumno_id>/direccion", methods=["POST"])
def asignar_direccion_route(alumno_id):
    session = get_session()
    rol = request.form.get("rol")
    profesor_id = request.form.get("profesor_id", type=int)
    acta_id = request.form.get("acta_id", type=int)
    if not rol or not profesor_id:
        flash("Selecciona rol y profesor.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))

    _, aviso = asignar_direccion(session, alumno_id=alumno_id, profesor_id=profesor_id, rol=rol, acta_id=acta_id)
    session.commit()
    flash(f"{rol} asignado.", "exito")
    if aviso:
        flash(aviso, "aviso")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/comite", methods=["POST"])
def asignar_comite_route(alumno_id):
    session = get_session()
    profesor_ids = [int(pid) for pid in request.form.getlist("profesor_ids")]
    ciclo = request.form.get("ciclo") or ciclo_escolar_vigente(session)
    acta_id = request.form.get("acta_id", type=int)
    if not profesor_ids:
        flash("Selecciona al menos un profesor para el comité tutorial.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))

    asignar_comite_tutorial(session, alumno_id=alumno_id, profesor_ids=profesor_ids, ciclo=ciclo, acta_id=acta_id)
    session.commit()
    flash("Comité tutorial actualizado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/lector", methods=["POST"])
def agregar_lector_route(alumno_id):
    session = get_session()
    profesor_id = request.form.get("profesor_id", type=int)
    if not profesor_id:
        flash("Selecciona un profesor para el lector.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))
    agregar_lector(session, alumno_id=alumno_id, profesor_id=profesor_id, fecha=request.form.get("fecha"))
    session.commit()
    flash("Lector agregado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/lector/<int:lector_id>/quitar", methods=["POST"])
def quitar_lector_route(alumno_id, lector_id):
    session = get_session()
    lector = session.get(Lector, lector_id)
    if lector and lector.alumno_id == alumno_id:
        quitar_lector(session, lector)
        session.commit()
        flash("Lector eliminado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/sinodal", methods=["POST"])
def agregar_sinodal_route(alumno_id):
    session = get_session()
    profesor_id = request.form.get("profesor_id", type=int)
    cargo = request.form.get("cargo")
    if not profesor_id or not cargo:
        flash("Selecciona profesor y cargo para el sinodal.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))
    agregar_sinodal(
        session, alumno_id=alumno_id, profesor_id=profesor_id, cargo=cargo,
        fecha_examen=request.form.get("fecha_examen"),
        hora_examen=request.form.get("hora_examen"),
        lugar_examen=request.form.get("lugar_examen"),
    )
    session.commit()
    flash("Sinodal agregado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))


@bp.route("/<int:alumno_id>/sinodal/<int:sinodal_id>/quitar", methods=["POST"])
def quitar_sinodal_route(alumno_id, sinodal_id):
    session = get_session()
    sinodal = session.get(Sinodal, sinodal_id)
    if sinodal and sinodal.alumno_id == alumno_id:
        quitar_sinodal(session, sinodal)
        session.commit()
        flash("Sinodal eliminado.", "exito")
    return redirect(url_for("alumnos.detalle", alumno_id=alumno_id))
