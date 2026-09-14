import json
import re

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.repositories.acta_repository import listar_actas, obtener_acta
from app.repositories.alumno_repository import buscar_alumnos
from app.repositories.profesor_repository import listar_profesores
from app.repositories.tipo_documento_repository import listar_tipos_confirmados
from app.services.acta_service import TIPOS_PUNTO, TIPOS_PUNTO_INFO, NumeroDuplicadoError, actualizar_acta, crear_acta
from app.services.configuracion_service import ciclo_escolar_vigente
from app.services.tipo_documento_service import (
    necesita_alumno,
    necesita_profesor,
    necesita_profesores_lista,
    variables_libres,
)
from app.web.db import get_session

bp = Blueprint("actas", __name__, url_prefix="/actas")

_PATRON_INDICE_PUNTO = re.compile(r"punto_tipo_(\d+)")
_PATRON_CAMPO_LIBRE = re.compile(r"punto_campo_(\d+)__(\w+)")


def _puntos_desde_form(form) -> list[dict]:
    """Cada bloque de punto en el formulario tiene un índice único
    (`punto_tipo_0`, `punto_alumno_id_0`, ...) asignado por JS al
    agregarlo — así los campos de bloques con distinto `tipo` (que
    muestran/ocultan distintos inputs) no se desalinean entre sí como
    pasaría con `getlist()` posicional plano."""
    indices = sorted(int(m.group(1)) for k in form.keys() if (m := _PATRON_INDICE_PUNTO.fullmatch(k)))

    campos_libres_por_indice: dict[int, dict[str, str]] = {}
    for k in form.keys():
        m = _PATRON_CAMPO_LIBRE.fullmatch(k)
        if m:
            i, clave = int(m.group(1)), m.group(2)
            campos_libres_por_indice.setdefault(i, {})[clave] = form.get(k, "")

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

        elif tipo == "personalizado":
            tipo_documento_id = form.get(f"punto_tipo_documento_id_{i}", type=int)
            titulo = (form.get(f"punto_titulo_{i}") or "").strip()
            if not (tipo_documento_id and titulo):
                continue
            puntos.append(
                {
                    "tipo": "personalizado",
                    "tipo_documento_id": tipo_documento_id,
                    "titulo": titulo,
                    "resolutivo": form.get(f"punto_resolutivo_{i}", ""),
                    "alumno_id": form.get(f"punto_alumno_id_{i}", type=int),
                    "profesor_id": form.get(f"punto_profesor_id_{i}", type=int),
                    "miembro_ids": [int(v) for v in form.getlist(f"punto_profesores_lista_{i}")],
                    "campos_libres": campos_libres_por_indice.get(i, {}),
                }
            )

        else:
            titulo = (form.get(f"punto_titulo_{i}") or "").strip()
            if not titulo:
                continue
            puntos.append({"tipo": "otro", "titulo": titulo, "resolutivo": form.get(f"punto_resolutivo_{i}", "")})

    return puntos


def _contexto_formulario(session, acta=None):
    alumnos = buscar_alumnos(session)
    profesores = listar_profesores(session)
    tipos_personalizados = listar_tipos_confirmados(session)
    for t in tipos_personalizados:
        t.necesita_alumno = necesita_alumno(t.cuerpo_texto or "")
        t.necesita_profesor = necesita_profesor(t.cuerpo_texto or "")
        t.necesita_profesores_lista = necesita_profesores_lista(t.cuerpo_texto or "")
        t.campos_libres = variables_libres(t.cuerpo_texto or "")
    if acta:
        for p in acta.puntos:
            if p.tipo == "personalizado":
                p.datos_dict = json.loads(p.datos_json) if p.datos_json else {}
    return dict(
        acta=acta,
        alumnos=alumnos,
        profesores=profesores,
        alumnos_json=[{"id": a.id, "texto": f"{a.nombre} ({a.codigo})"} for a in alumnos],
        profesores_json=[{"id": p.id, "texto": p.nombre} for p in profesores],
        tipos_punto=TIPOS_PUNTO,
        tipos_punto_info=TIPOS_PUNTO_INFO,
        tipos_personalizados=tipos_personalizados,
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
