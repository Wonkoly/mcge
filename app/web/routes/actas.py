import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.acta_repository import listar_actas, obtener_acta
from app.repositories.alumno_repository import buscar_alumnos
from app.repositories.profesor_repository import listar_profesores
from app.services.acta_service import TIPOS_PUNTO, NumeroDuplicadoError, actualizar_acta, crear_acta
from app.services.configuracion_service import ciclo_escolar_vigente
from app.web.db import get_session

bp = Blueprint("actas", __name__, url_prefix="/actas")

_PATRON_INDICE_PUNTO = re.compile(r"punto_tipo_(\d+)")


def _puntos_desde_form(form) -> list[dict]:
    """Cada bloque de punto en el formulario tiene un índice único
    (`punto_tipo_0`, `punto_alumno_id_0`, ...) asignado por JS al
    agregarlo — así los campos de bloques con distinto `tipo` (que
    muestran/ocultan distintos inputs) no se desalinean entre sí como
    pasaría con `getlist()` posicional plano."""
    indices = sorted(int(m.group(1)) for k in form.keys() if (m := _PATRON_INDICE_PUNTO.fullmatch(k)))

    puntos = []
    for i in indices:
        tipo = form.get(f"punto_tipo_{i}", "otro")

        if tipo == "direccion":
            alumno_id = form.get(f"punto_alumno_id_{i}", type=int)
            profesor_id = form.get(f"punto_profesor_id_{i}", type=int)
            rol = form.get(f"punto_rol_{i}")
            if not (alumno_id and profesor_id and rol):
                continue
            puntos.append({"tipo": "direccion", "alumno_id": alumno_id, "profesor_id": profesor_id, "rol": rol})

        elif tipo == "comite_tutorial":
            alumno_id = form.get(f"punto_alumno_id_{i}", type=int)
            ciclo = form.get(f"punto_ciclo_{i}") or None
            miembro_ids = [int(v) for v in form.getlist(f"punto_miembro_ids_{i}")]
            if not (alumno_id and miembro_ids):
                continue
            puntos.append({"tipo": "comite_tutorial", "alumno_id": alumno_id, "ciclo": ciclo, "miembro_ids": miembro_ids})

        else:
            titulo = (form.get(f"punto_titulo_{i}") or "").strip()
            if not titulo:
                continue
            puntos.append({"tipo": "otro", "titulo": titulo, "resolutivo": form.get(f"punto_resolutivo_{i}", "")})

    return puntos


def _contexto_formulario(session, acta=None):
    return dict(
        acta=acta,
        alumnos=buscar_alumnos(session),
        profesores=listar_profesores(session),
        tipos_punto=TIPOS_PUNTO,
        ciclo_sugerido=ciclo_escolar_vigente(session),
    )


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
            acta, avisos = crear_acta(session, puntos=_puntos_desde_form(request.form), **request.form)
            session.commit()
            flash(f"Acta {acta.numero} creada.", "exito")
            for aviso in avisos:
                flash(aviso, "aviso")
            return redirect(url_for("actas.detalle", acta_id=acta.id))
        except (NumeroDuplicadoError, ValueError) as exc:
            flash(str(exc), "error")
    return render_template("actas/formulario.html", **_contexto_formulario(session))


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
            acta, avisos = actualizar_acta(session, acta, puntos=_puntos_desde_form(request.form), **request.form)
            session.commit()
            flash(f"Acta {acta.numero} actualizada.", "exito")
            for aviso in avisos:
                flash(aviso, "aviso")
            return redirect(url_for("actas.detalle", acta_id=acta.id))
        except (NumeroDuplicadoError, ValueError) as exc:
            flash(str(exc), "error")
    return render_template("actas/formulario.html", **_contexto_formulario(session, acta))
