import re

from flask import Blueprint, flash, redirect, request, send_file, url_for

from app.documents.generador import (
    COORDINADOR_DEFAULT,
    generar_acta,
    generar_constancia_direccion,
    generar_oficio_direccion,
)
from app.models import Direccion
from app.repositories.acta_repository import obtener_acta
from app.web.db import get_session

bp = Blueprint("documentos", __name__, url_prefix="/documentos")


def _nombre_archivo(texto: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", texto).strip()
    return re.sub(r"[\s]+", "_", limpio) + ".docx"


@bp.route("/direccion/<int:direccion_id>", methods=["POST"])
def documento_direccion(direccion_id):
    session = get_session()
    direccion = session.get(Direccion, direccion_id)
    if direccion is None:
        flash("Registro de dirección no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    tipo = request.form.get("tipo")
    coordinador_nombre = request.form.get("coordinador_nombre") or COORDINADOR_DEFAULT
    lema_ciclo = request.form.get("lema_ciclo") or ""
    tratamiento_manual = request.form.get("profesor_tratamiento_nombre") or None

    kwargs = dict(
        direccion=direccion,
        coordinador_nombre=coordinador_nombre,
        lema_ciclo=lema_ciclo,
        profesor_tratamiento_nombre=tratamiento_manual,
    )

    if tipo == "oficio":
        buffer = generar_oficio_direccion(**kwargs)
        nombre_archivo = _nombre_archivo(f"Oficio {direccion.rol} {direccion.alumno.nombre}")
    elif tipo == "constancia":
        buffer = generar_constancia_direccion(**kwargs)
        nombre_archivo = _nombre_archivo(f"Constancia {direccion.rol} {direccion.alumno.nombre}")
    else:
        flash("Tipo de documento no reconocido.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=direccion.alumno_id))

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@bp.route("/acta/<int:acta_id>", methods=["GET"])
def documento_acta(acta_id):
    session = get_session()
    acta = obtener_acta(session, acta_id)
    if acta is None:
        flash("Acta no encontrada.", "error")
        return redirect(url_for("actas.listar"))

    coordinador_nombre = request.args.get("coordinador_nombre") or COORDINADOR_DEFAULT
    lema_ciclo = request.args.get("lema_ciclo") or ""

    buffer = generar_acta(acta=acta, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
    nombre_archivo = _nombre_archivo(f"Acta {acta.numero}")
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
