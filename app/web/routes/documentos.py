import re

from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for

from app.documents.generador import (
    generar_acta,
    generar_constancia_direccion,
    generar_constancia_evaluador_aspirantes,
    generar_constancia_jurado,
    generar_constancia_lector,
    generar_documento_personalizado,
    generar_oficio_asentamiento_creditos,
    generar_oficio_comite_tutorial_alumno,
    generar_oficio_comite_tutorial_docente,
    generar_oficio_direccion,
    generar_oficio_invitacion_jurado,
    generar_oficio_permiso_municipio,
)
from app.documents.variables_disponibles import VARIABLES_ALUMNO, VARIABLES_GENERALES, VARIABLES_PROFESOR
from app.models import Alumno, ComiteTutorial, Direccion, Lector, Profesor, PuntoActa, Sinodal
from app.repositories.acta_repository import obtener_acta
from app.repositories.profesor_repository import listar_profesores
from app.repositories.tipo_documento_repository import listar_moldes, listar_tipos, obtener_tipo
from app.services.configuracion_service import obtener as obtener_config
from app.services.tipo_documento_service import (
    CATEGORIAS_VALIDAS,
    MoldeFaltanteError,
    actualizar_cuerpo,
    compilar_plantilla,
    confirmar_plantilla,
    crear_tipo,
    guardar_molde_base,
    variables_libres,
)
from app.web.db import get_session

bp = Blueprint("documentos", __name__, url_prefix="/documentos")


def _nombre_archivo(texto: str) -> str:
    limpio = re.sub(r"[^\w\s-]", "", texto).strip()
    return re.sub(r"[\s]+", "_", limpio) + ".docx"


def _descargar(buffer, nombre_archivo):
    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


def _coordinador_y_lema(session):
    coordinador_nombre = request.form.get("coordinador_nombre") or obtener_config(session, "coordinador_nombre")
    lema_ciclo = request.form.get("lema_ciclo") or ""
    return coordinador_nombre, lema_ciclo


@bp.route("/")
def index():
    session = get_session()
    tipos = listar_tipos(session)
    return render_template(
        "documentos/index.html",
        moldes=listar_moldes(session),
        tipos_oficio=[t for t in tipos if t.categoria == "oficio"],
        tipos_constancia=[t for t in tipos if t.categoria == "constancia"],
    )


@bp.route("/moldes/<categoria>", methods=["POST"])
def subir_molde(categoria):
    session = get_session()
    if categoria not in CATEGORIAS_VALIDAS:
        flash("Categoría inválida.", "error")
        return redirect(url_for("documentos.index"))
    try:
        guardar_molde_base(session, categoria, request.files.get("archivo"))
        session.commit()
        flash(f"Molde base de {categoria} actualizado.", "exito")
    except ValueError as exc:
        flash(str(exc), "error")
    return redirect(url_for("documentos.index"))


@bp.route("/tipos/nuevo", methods=["GET", "POST"])
def tipos_nuevo():
    session = get_session()
    if request.method == "POST":
        try:
            tipo = crear_tipo(
                session,
                etiqueta=request.form.get("etiqueta", ""),
                categoria=request.form.get("categoria", ""),
                descripcion=request.form.get("descripcion", ""),
            )
            session.commit()
            return redirect(url_for("documentos.tipos_detalle", tipo_id=tipo.id))
        except ValueError as exc:
            flash(str(exc), "error")
    categoria_sugerida = request.args.get("categoria", "oficio")
    return render_template("documentos/tipos_nuevo.html", categoria_sugerida=categoria_sugerida)


@bp.route("/tipos/<int:tipo_id>", methods=["GET", "POST"])
def tipos_detalle(tipo_id):
    session = get_session()
    tipo = obtener_tipo(session, tipo_id)
    if tipo is None:
        flash("Tipo de documento no encontrado.", "error")
        return redirect(url_for("documentos.index"))

    if request.method == "POST":
        actualizar_cuerpo(session, tipo, request.form.get("cuerpo_texto", ""))
        session.commit()
        flash("Cuerpo guardado.", "exito")
        return redirect(url_for("documentos.tipos_detalle", tipo_id=tipo.id))

    return render_template(
        "documentos/tipos_detalle.html",
        tipo=tipo,
        molde=listar_moldes(session).get(tipo.categoria),
        variables_alumno=VARIABLES_ALUMNO,
        variables_profesor=VARIABLES_PROFESOR,
        variables_generales=VARIABLES_GENERALES,
        libres=variables_libres(tipo.cuerpo_texto or ""),
    )


@bp.route("/tipos/<int:tipo_id>/generar", methods=["GET"])
def tipos_generar(tipo_id):
    session = get_session()
    tipo = obtener_tipo(session, tipo_id)
    if tipo is None:
        flash("Tipo de documento no encontrado.", "error")
        return redirect(url_for("documentos.index"))
    try:
        buffer = compilar_plantilla(session, tipo)
    except MoldeFaltanteError as exc:
        flash(str(exc), "error")
        return redirect(url_for("documentos.tipos_detalle", tipo_id=tipo.id))
    return _descargar(buffer, _nombre_archivo(f"Vista previa {tipo.etiqueta}"))


@bp.route("/tipos/<int:tipo_id>/confirmar", methods=["POST"])
def tipos_confirmar(tipo_id):
    session = get_session()
    tipo = obtener_tipo(session, tipo_id)
    if tipo is None:
        flash("Tipo de documento no encontrado.", "error")
        return redirect(url_for("documentos.index"))
    try:
        confirmar_plantilla(session, tipo)
        session.commit()
        flash(f'"{tipo.etiqueta}" confirmado — ya aparece como opción en Actas.', "exito")
    except MoldeFaltanteError as exc:
        flash(str(exc), "error")
    return redirect(url_for("documentos.tipos_detalle", tipo_id=tipo.id))


@bp.route("/personalizado/<int:punto_id>", methods=["POST"])
def documento_personalizado(punto_id):
    session = get_session()
    punto = session.get(PuntoActa, punto_id)
    if punto is None or punto.tipo_documento is None:
        flash("Punto no encontrado.", "error")
        return redirect(url_for("actas.listar"))

    coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
    buffer = generar_documento_personalizado(
        session=session, tipo_documento=punto.tipo_documento, punto=punto,
        coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
    )
    return _descargar(buffer, _nombre_archivo(f"{punto.tipo_documento.etiqueta} {punto.titulo}"))


@bp.route("/direccion/<int:direccion_id>", methods=["POST"])
def documento_direccion(direccion_id):
    session = get_session()
    direccion = session.get(Direccion, direccion_id)
    if direccion is None:
        flash("Registro de dirección no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    tipo = request.form.get("tipo")
    coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
    tratamiento_manual = request.form.get("profesor_tratamiento_nombre") or None

    kwargs = dict(
        session=session,
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

    return _descargar(buffer, nombre_archivo)


@bp.route("/acta/<int:acta_id>", methods=["GET"])
def documento_acta(acta_id):
    session = get_session()
    acta = obtener_acta(session, acta_id)
    if acta is None:
        flash("Acta no encontrada.", "error")
        return redirect(url_for("actas.listar"))

    coordinador_nombre = request.args.get("coordinador_nombre") or obtener_config(session, "coordinador_nombre")
    lema_ciclo = request.args.get("lema_ciclo") or ""

    buffer = generar_acta(session=session, acta=acta, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
    return _descargar(buffer, _nombre_archivo(f"Acta {acta.numero}"))


@bp.route("/comite/<int:comite_id>", methods=["POST"])
def documento_comite(comite_id):
    session = get_session()
    comite = session.get(ComiteTutorial, comite_id)
    if comite is None:
        flash("Comité tutorial no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
    tipo = request.form.get("tipo")

    if tipo == "alumno":
        buffer = generar_oficio_comite_tutorial_alumno(
            session=session, comite=comite, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo
        )
        nombre_archivo = _nombre_archivo(f"Oficio Comite Tutorial Alumno {comite.alumno.nombre}")
    elif tipo == "docente":
        profesor_id = request.form.get("profesor_id", type=int)
        profesor = session.get(Profesor, profesor_id) if profesor_id else None
        if profesor is None:
            flash("Selecciona a qué integrante del comité va dirigido el oficio.", "error")
            return redirect(url_for("alumnos.detalle", alumno_id=comite.alumno_id))
        buffer = generar_oficio_comite_tutorial_docente(
            session=session, comite=comite, profesor_destinatario=profesor,
            coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
        )
        nombre_archivo = _nombre_archivo(f"Oficio Comite Tutorial {profesor.nombre}")
    else:
        flash("Tipo de documento no reconocido.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=comite.alumno_id))

    return _descargar(buffer, nombre_archivo)


@bp.route("/lector/<int:lector_id>", methods=["POST"])
def documento_lector(lector_id):
    session = get_session()
    lector = session.get(Lector, lector_id)
    if lector is None:
        flash("Registro de lector no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
    buffer = generar_constancia_lector(session=session, lector=lector, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
    return _descargar(buffer, _nombre_archivo(f"Constancia Lector {lector.profesor.nombre}"))


@bp.route("/sinodal/<int:sinodal_id>", methods=["POST"])
def documento_sinodal(sinodal_id):
    session = get_session()
    sinodal = session.get(Sinodal, sinodal_id)
    if sinodal is None:
        flash("Registro de sinodal no encontrado.", "error")
        return redirect(url_for("alumnos.listar"))

    coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
    tipo = request.form.get("tipo")

    if tipo == "constancia":
        buffer = generar_constancia_jurado(session=session, sinodal=sinodal, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre_archivo = _nombre_archivo(f"Constancia Jurado {sinodal.profesor.nombre}")
    elif tipo == "invitacion":
        buffer = generar_oficio_invitacion_jurado(session=session, sinodal=sinodal, coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo)
        nombre_archivo = _nombre_archivo(f"Oficio Invitacion Jurado {sinodal.profesor.nombre}")
    else:
        flash("Tipo de documento no reconocido.", "error")
        return redirect(url_for("alumnos.detalle", alumno_id=sinodal.alumno_id))

    return _descargar(buffer, nombre_archivo)


@bp.route("/evaluador-aspirantes", methods=["GET", "POST"])
def documento_evaluador_aspirantes():
    session = get_session()
    if request.method == "POST":
        profesor = session.get(Profesor, request.form.get("profesor_id", type=int))
        if profesor is None:
            flash("Selecciona un profesor.", "error")
            return redirect(url_for("documentos.documento_evaluador_aspirantes"))
        coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
        buffer = generar_constancia_evaluador_aspirantes(
            session=session, profesor=profesor,
            ciclo=request.form.get("ciclo", ""),
            fecha_entrevista=request.form.get("fecha_entrevista", ""),
            lugar=request.form.get("lugar", ""),
            coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
        )
        return _descargar(buffer, _nombre_archivo(f"Constancia Evaluador Aspirantes {profesor.nombre}"))
    return render_template("documentos/evaluador_aspirantes.html", profesores=listar_profesores(session))


@bp.route("/asentamiento-creditos", methods=["GET", "POST"])
def documento_asentamiento_creditos():
    session = get_session()
    if request.method == "POST":
        alumno = session.get(Alumno, request.form.get("alumno_id", type=int))
        if alumno is None:
            flash("Selecciona un alumno.", "error")
            return redirect(url_for("documentos.documento_asentamiento_creditos"))
        coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
        buffer = generar_oficio_asentamiento_creditos(
            session=session, alumno=alumno,
            materia_nombre=request.form.get("materia_nombre", ""),
            materia_clave=request.form.get("materia_clave", ""),
            creditos=request.form.get("creditos", type=int) or 0,
            ciclo=request.form.get("ciclo", ""),
            destinatario_nombre=request.form.get("destinatario_nombre") or "Coordinadora de Control Escolar",
            coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
        )
        return _descargar(buffer, _nombre_archivo(f"Oficio Asentamiento Creditos {alumno.nombre}"))
    from app.repositories.alumno_repository import buscar_alumnos

    return render_template("documentos/asentamiento_creditos.html", alumnos=buscar_alumnos(session))


@bp.route("/permiso-municipio", methods=["GET", "POST"])
def documento_permiso_municipio():
    session = get_session()
    if request.method == "POST":
        coordinador_nombre, lema_ciclo = _coordinador_y_lema(session)
        buffer = generar_oficio_permiso_municipio(
            session=session,
            destinatario_nombre=request.form.get("destinatario_nombre", ""),
            destinatario_cargo=request.form.get("destinatario_cargo", ""),
            municipio=request.form.get("municipio", ""),
            cuerpo_solicitud=request.form.get("cuerpo_solicitud", ""),
            cuerpo_parrafo2=request.form.get("cuerpo_parrafo2", ""),
            coordinador_nombre=coordinador_nombre, lema_ciclo=lema_ciclo,
        )
        return _descargar(buffer, _nombre_archivo(f"Oficio Permiso {request.form.get('municipio', '')}"))
    return render_template("documentos/permiso_municipio.html")
