import json
from datetime import datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.documents.generador import _campos_rol, formatear_nombre, tratamiento_con_nombre
from app.models import Acta, ComiteTutorial, Direccion, PuntoActa, PuntoActaMiembro
from app.services.auditoria_service import registrar
from app.services.comite_service import asignar_comite_tutorial
from app.services.direccion_service import asignar_direccion

# Catálogo de tipos de punto — "direccion" y "comite_tutorial" son
# estructurados: al guardar el acta disparan el alta real en
# Direccion/ComiteTutorial (ver _reemplazar_puntos). "otro" es el
# comportamiento original, texto libre. No hay histórico real todavía
# para minar tipos recurrentes (0 puntos capturados en la BD al momento
# de este cambio) — se siembra con los dos flujos que ya existían en el
# expediente del alumno; se puede ampliar más adelante (ver plan de
# plantillas subibles desde la app, pendiente de alcance).
TIPOS_PUNTO_INFO = {
    "direccion": {
        "etiqueta": "Asignación de Director/Codirector de tesis",
        "descripcion": "Crea o cambia el Director o Codirector de tesis de un alumno. Deja listo el oficio de asignación para generar.",
    },
    "comite_tutorial": {
        "etiqueta": "Asignación/cambio de Comité Tutorial",
        "descripcion": "Asigna los profesores tutores de un alumno para el ciclo. Deja listos los oficios (al alumno y a cada tutor) para generar.",
    },
    "otro": {
        "etiqueta": "Otro (texto libre)",
        "descripcion": "Cualquier otro acuerdo que no encaje en los tipos anteriores — tú escribes el título y el resolutivo.",
    },
}

TIPOS_PUNTO = {clave: info["etiqueta"] for clave, info in TIPOS_PUNTO_INFO.items()}


class NumeroDuplicadoError(Exception):
    pass


def _o_none(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    return valor or None


def _parsear_fecha(valor):
    valor = _o_none(valor)
    if not valor:
        return None
    return datetime.strptime(valor, "%Y-%m-%d").date()


def _nombre_tratado(persona) -> str:
    return tratamiento_con_nombre(persona, formatear_nombre(persona.nombre))


def _reemplazar_puntos(session: Session, acta: Acta, puntos: list[dict], usuario: str) -> list[str]:
    """Reconstruye `acta.puntos` a partir de lo que mandó el formulario.
    Para los tipos estructurados, dispara el alta real vía
    `direccion_service.asignar_direccion` / `comite_service.asignar_comite_tutorial`
    (mismo mecanismo que ya usaba el expediente del alumno, ahora movido
    aquí) y compone título/resolutivo automáticamente reutilizando las
    mismas funciones de tratamiento/género que usan los oficios
    (app.documents.generador), para no duplicar esa lógica.

    Si un punto en la MISMA posición ya tenía el mismo tipo y los mismos
    datos estructurados que antes de editar, se reutiliza el registro ya
    creado en vez de disparar una asignación nueva (evita cerrar/reabrir
    un período por el simple hecho de reguardar el acta sin cambios)."""
    avisos: list[str] = []
    existentes = list(acta.puntos)
    nuevos: list[PuntoActa] = []

    for i, dato in enumerate(puntos):
        tipo = dato["tipo"]
        anterior = existentes[i] if i < len(existentes) else None

        if tipo == "direccion":
            reutilizable = (
                anterior is not None
                and anterior.tipo == "direccion"
                and anterior.alumno_id == dato["alumno_id"]
                and anterior.profesor_id == dato["profesor_id"]
                and anterior.rol == dato["rol"]
                and anterior.direccion_id is not None
            )
            if reutilizable:
                direccion = session.get(Direccion, anterior.direccion_id)
            else:
                direccion, aviso = asignar_direccion(
                    session,
                    alumno_id=dato["alumno_id"],
                    profesor_id=dato["profesor_id"],
                    rol=dato["rol"],
                    acta_id=acta.id,
                    usuario=usuario,
                )
                if aviso:
                    avisos.append(aviso)

            rol_texto_largo, rol_corto, _ = _campos_rol(direccion)
            titulo = f"Asignación de {rol_texto_largo} de tesis a {formatear_nombre(direccion.alumno.nombre)}"
            resolutivo = (
                f"Se aprueba la designación de {_nombre_tratado(direccion.profesor)} "
                f"como {rol_corto} del trabajo de tesis de {formatear_nombre(direccion.alumno.nombre)}."
            )
            nuevos.append(
                PuntoActa(
                    orden=i + 1,
                    tipo="direccion",
                    titulo=titulo,
                    resolutivo=resolutivo,
                    alumno_id=dato["alumno_id"],
                    profesor_id=dato["profesor_id"],
                    rol=dato["rol"],
                    direccion_id=direccion.id,
                )
            )

        elif tipo == "comite_tutorial":
            miembro_ids_ordenados = sorted(dato["miembro_ids"])
            reutilizable = (
                anterior is not None
                and anterior.tipo == "comite_tutorial"
                and anterior.alumno_id == dato["alumno_id"]
                and anterior.ciclo == dato.get("ciclo")
                and sorted(m.profesor_id for m in anterior.miembros) == miembro_ids_ordenados
                and anterior.comite_tutorial_id is not None
            )
            if reutilizable:
                comite = session.get(ComiteTutorial, anterior.comite_tutorial_id)
            else:
                comite = asignar_comite_tutorial(
                    session,
                    alumno_id=dato["alumno_id"],
                    profesor_ids=dato["miembro_ids"],
                    ciclo=dato.get("ciclo"),
                    acta_id=acta.id,
                    usuario=usuario,
                )

            nombres = ", ".join(_nombre_tratado(m.profesor) for m in comite.miembros)
            titulo = f"Asignación de Comité Tutorial a {formatear_nombre(comite.alumno.nombre)}"
            resolutivo = f"Se aprueba el Comité Tutorial de {formatear_nombre(comite.alumno.nombre)}, integrado por: {nombres}."
            punto = PuntoActa(
                orden=i + 1,
                tipo="comite_tutorial",
                titulo=titulo,
                resolutivo=resolutivo,
                alumno_id=dato["alumno_id"],
                ciclo=dato.get("ciclo"),
                comite_tutorial_id=comite.id,
            )
            punto.miembros = [PuntoActaMiembro(profesor_id=pid) for pid in dato["miembro_ids"]]
            nuevos.append(punto)

        elif tipo == "personalizado":
            titulo = _o_none(dato.get("titulo"))
            if not (dato.get("tipo_documento_id") and titulo):
                continue
            punto = PuntoActa(
                orden=i + 1,
                tipo="personalizado",
                titulo=titulo,
                resolutivo=_o_none(dato.get("resolutivo")),
                alumno_id=dato.get("alumno_id"),
                profesor_id=dato.get("profesor_id"),
                tipo_documento_id=dato["tipo_documento_id"],
                datos_json=json.dumps(dato.get("campos_libres") or {}, ensure_ascii=False),
            )
            if dato.get("miembro_ids"):
                punto.miembros = [PuntoActaMiembro(profesor_id=pid) for pid in dato["miembro_ids"]]
            nuevos.append(punto)

        else:
            titulo = _o_none(dato.get("titulo"))
            if not titulo:
                continue
            nuevos.append(
                PuntoActa(orden=i + 1, tipo="otro", titulo=titulo, resolutivo=_o_none(dato.get("resolutivo")))
            )

    acta.puntos = nuevos
    return avisos


def crear_acta(session: Session, *, usuario: str = "usuario", puntos: list[dict], **campos) -> tuple[Acta, list[str]]:
    numero = (campos.get("numero") or "").strip()
    if not numero:
        raise ValueError("El número de acta es obligatorio")

    fecha = _parsear_fecha(campos.get("fecha"))
    anio = fecha.year if fecha else datetime.now().year

    acta = Acta(
        numero=numero,
        fecha=fecha,
        anio=anio,
        resumen=_o_none(campos.get("resumen")),
        hora_inicio=_o_none(campos.get("hora_inicio")),
        hora_fin=_o_none(campos.get("hora_fin")),
        lugar=_o_none(campos.get("lugar")) or "Puerto Vallarta, Jalisco",
        sede=_o_none(campos.get("sede")),
        asistentes=_o_none(campos.get("asistentes")),
    )
    session.add(acta)
    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    avisos = _reemplazar_puntos(session, acta, puntos, usuario)
    session.flush()

    registrar(session, usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="crear", valor_nuevo=numero)
    return acta, avisos


def actualizar_acta(
    session: Session, acta: Acta, *, usuario: str = "usuario", puntos: list[dict], **campos
) -> tuple[Acta, list[str]]:
    numero = (campos.get("numero") or "").strip()
    if not numero:
        raise ValueError("El número de acta es obligatorio")

    fecha = _parsear_fecha(campos.get("fecha"))
    acta.numero = numero
    acta.fecha = fecha
    acta.anio = fecha.year if fecha else acta.anio
    acta.resumen = _o_none(campos.get("resumen"))
    acta.hora_inicio = _o_none(campos.get("hora_inicio"))
    acta.hora_fin = _o_none(campos.get("hora_fin"))
    acta.lugar = _o_none(campos.get("lugar")) or "Puerto Vallarta, Jalisco"
    acta.sede = _o_none(campos.get("sede"))
    acta.asistentes = _o_none(campos.get("asistentes"))

    try:
        session.flush()
    except IntegrityError as exc:
        session.rollback()
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    avisos = _reemplazar_puntos(session, acta, puntos, usuario)
    session.flush()

    registrar(
        session, usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="modificar", valor_nuevo="datos actualizados"
    )
    return acta, avisos
