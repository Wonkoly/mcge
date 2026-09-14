from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from app.services.configuracion_service import CLAVES_DEFAULT, establecer, obtener_todas
from app.services.folio_service import TIPOS_DOCUMENTO, establecer_folio, listar_folios
from app.utils.backup import crear_respaldo, listar_respaldos, restaurar_respaldo
from app.web.db import get_session

bp = Blueprint("configuracion", __name__, url_prefix="/configuracion")


@bp.route("/", methods=["GET", "POST"])
def index():
    session = get_session()
    if request.method == "POST":
        for clave in CLAVES_DEFAULT:
            if clave in request.form:
                establecer(session, clave, request.form.get(clave, "").strip())
        session.commit()
        flash("Configuración guardada.", "exito")
        return redirect(url_for("configuracion.index"))

    respaldos = [
        {"nombre": p.name, "tamano_kb": round(p.stat().st_size / 1024), "fecha": datetime.fromtimestamp(p.stat().st_mtime)}
        for p in listar_respaldos()
    ]
    return render_template(
        "configuracion/index.html",
        config=obtener_todas(session),
        respaldos=respaldos,
        folios=listar_folios(session),
        tipos_documento=TIPOS_DOCUMENTO,
    )


@bp.route("/folio", methods=["POST"])
def establecer_folio_route():
    session = get_session()
    tipo_documento = request.form.get("tipo_documento", "")
    anio = request.form.get("anio", type=int)
    ultimo_folio = request.form.get("ultimo_folio", type=int)
    if tipo_documento not in TIPOS_DOCUMENTO or anio is None or ultimo_folio is None:
        flash("Datos inválidos para el folio.", "error")
        return redirect(url_for("configuracion.index"))

    establecer_folio(session, tipo_documento, anio, ultimo_folio)
    session.commit()
    flash(
        f"Folio de \"{TIPOS_DOCUMENTO[tipo_documento]}\" ({anio}) actualizado — "
        f"el siguiente que se genere será el número {ultimo_folio + 1}.",
        "exito",
    )
    return redirect(url_for("configuracion.index"))


@bp.route("/respaldo/generar", methods=["POST"])
def generar_respaldo():
    destino = crear_respaldo()
    if destino:
        flash(f"Respaldo generado: {destino.name}", "exito")
    else:
        flash("No se pudo generar el respaldo (¿todavía no existe la base de datos?).", "error")
    return redirect(url_for("configuracion.index"))


@bp.route("/respaldo/restaurar", methods=["POST"])
def restaurar():
    nombre = request.form.get("nombre")
    confirmacion = request.form.get("confirmacion")
    if confirmacion != nombre:
        flash("Confirmación incorrecta — no se restauró nada.", "error")
        return redirect(url_for("configuracion.index"))
    try:
        restaurar_respaldo(nombre)
        flash(
            f"Respaldo {nombre} restaurado. Cierra y vuelve a abrir la app para que quede todo limpio.",
            "aviso",
        )
    except FileNotFoundError as exc:
        flash(str(exc), "error")
    return redirect(url_for("configuracion.index"))
