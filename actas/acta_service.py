"""Puerto de app/services/acta_service.py — con una corrección deliberada
respecto al original (ver _reemplazar_puntos)."""

import json
from datetime import date, datetime

from django.db import transaction
from django.db.utils import IntegrityError

from actas.comite_service import asignar_comite_tutorial
from actas.models import Acta, ComiteTutorial, Direccion, PuntoActa, PuntoActaMiembro
from actas.direccion_service import asignar_direccion
from core.auditoria import registrar
from documentos import texto

# "direccion" y "comite_tutorial" son estructurados: al guardar el acta
# disparan el alta real en Direccion/ComiteTutorial (ver
# _reemplazar_puntos). "otro" es texto libre. "personalizado" no aparece
# aquí — cada tipo de documento CONFIRMADO del taller es su propia opción
# en el selector (ver documentos.tipos.listar_confirmados en la vista).
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
    return texto.tratamiento_con_nombre(persona, texto.formatear_nombre(persona.nombre))


def _campos_rol(direccion) -> tuple[str, str]:
    femenino = texto.es_femenino(direccion.profesor)
    if direccion.rol == "Director":
        return ("Directora" if femenino else "Director"), ("directora" if femenino else "director")
    return ("Codirectora" if femenino else "Codirector"), ("codirectora" if femenino else "codirector")


def _reemplazar_puntos(acta: Acta, puntos: list[dict], usuario: str) -> list[str]:
    """Reconstruye los puntos de `acta` a partir de lo que mandó el
    formulario. Para los tipos estructurados, dispara el alta real vía
    direccion_service.asignar_direccion / comite_service.asignar_comite_tutorial
    y compone título/resolutivo automáticamente reutilizando las mismas
    funciones de tratamiento/género que usan los oficios (documentos.texto).

    Corrección deliberada respecto al original (Flask): ahí, un punto se
    consideraba "el mismo de antes" (y por tanto reutilizaba el
    Direccion/ComiteTutorial ya creado, sin cerrar/reabrir el historial)
    si coincidía en la MISMA POSICIÓN de la lista — reordenar o insertar un
    punto antes rompía esa comparación y disparaba un cierre/reapertura
    espurio. Aquí se compara por el `punto_id` real (la PK del PuntoActa
    que el formulario manda como campo oculto, vacío si es nuevo) — mismo
    comportamiento en el caso normal, corrige el caso de reordenar. Esto
    es código nuevo, no un port línea por línea, así que no hace falta
    preservar el defecto."""
    avisos: list[str] = []
    existentes_por_id = {p.id: p for p in acta.puntos.prefetch_related("miembros").all()}
    nuevos: list[dict] = []  # cada uno: kwargs de PuntoActa + "miembro_ids" opcional

    for i, dato in enumerate(puntos):
        tipo = dato["tipo"]
        anterior = existentes_por_id.get(dato.get("punto_id"))

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
                direccion = Direccion.objects.select_related("alumno", "profesor").get(pk=anterior.direccion_id)
            else:
                direccion, aviso = asignar_direccion(
                    alumno_id=dato["alumno_id"], profesor_id=dato["profesor_id"], rol=dato["rol"],
                    acta_id=acta.id, usuario=usuario,
                )
                direccion = Direccion.objects.select_related("alumno", "profesor").get(pk=direccion.pk)
                if aviso:
                    avisos.append(aviso)

            rol_texto_largo, rol_corto = _campos_rol(direccion)
            titulo = f"Asignación de {rol_texto_largo} de tesis a {texto.formatear_nombre(direccion.alumno.nombre)}"
            resolutivo = (
                f"Se aprueba la designación de {_nombre_tratado(direccion.profesor)} "
                f"como {rol_corto} del trabajo de tesis de {texto.formatear_nombre(direccion.alumno.nombre)}."
            )
            nuevos.append({
                "orden": i + 1, "tipo": "direccion", "titulo": titulo, "resolutivo": resolutivo,
                "alumno_id": dato["alumno_id"], "profesor_id": dato["profesor_id"], "rol": dato["rol"],
                "direccion_id": direccion.id,
            })

        elif tipo == "comite_tutorial":
            miembro_ids_ordenados = sorted(dato["miembro_ids"])
            reutilizable = (
                anterior is not None
                and anterior.tipo == "comite_tutorial"
                and anterior.alumno_id == dato["alumno_id"]
                and anterior.ciclo == dato.get("ciclo")
                and sorted(m.profesor_id for m in anterior.miembros.all()) == miembro_ids_ordenados
                and anterior.comite_tutorial_id is not None
            )
            if reutilizable:
                comite = ComiteTutorial.objects.prefetch_related("miembros__profesor").get(pk=anterior.comite_tutorial_id)
            else:
                comite = asignar_comite_tutorial(
                    alumno_id=dato["alumno_id"], profesor_ids=dato["miembro_ids"],
                    ciclo=dato.get("ciclo"), acta_id=acta.id, usuario=usuario,
                )
                comite = ComiteTutorial.objects.prefetch_related("miembros__profesor").get(pk=comite.pk)

            nombres = ", ".join(_nombre_tratado(m.profesor) for m in comite.miembros.all())
            alumno_nombre = texto.formatear_nombre(comite.alumno.nombre)
            titulo = f"Asignación de Comité Tutorial a {alumno_nombre}"
            resolutivo = f"Se aprueba el Comité Tutorial de {alumno_nombre}, integrado por: {nombres}."
            nuevos.append({
                "orden": i + 1, "tipo": "comite_tutorial", "titulo": titulo, "resolutivo": resolutivo,
                "alumno_id": dato["alumno_id"], "ciclo": dato.get("ciclo"), "comite_tutorial_id": comite.id,
                "miembro_ids": dato["miembro_ids"],
            })

        elif tipo == "personalizado":
            titulo = _o_none(dato.get("titulo"))
            if not (dato.get("tipo_documento_id") and titulo):
                continue
            nuevos.append({
                "orden": i + 1, "tipo": "personalizado", "titulo": titulo, "resolutivo": _o_none(dato.get("resolutivo")),
                "alumno_id": dato.get("alumno_id"), "profesor_id": dato.get("profesor_id"),
                "tipo_documento_id": dato["tipo_documento_id"],
                "datos_json": json.dumps(dato.get("campos_libres") or {}, ensure_ascii=False),
                "miembro_ids": dato.get("miembro_ids") or [],
            })

        else:
            titulo = _o_none(dato.get("titulo"))
            if not titulo:
                continue
            nuevos.append({"orden": i + 1, "tipo": "otro", "titulo": titulo, "resolutivo": _o_none(dato.get("resolutivo"))})

    acta.puntos.all().delete()
    for datos_punto in nuevos:
        miembro_ids = datos_punto.pop("miembro_ids", None)
        punto = PuntoActa.objects.create(acta=acta, **datos_punto)
        if miembro_ids:
            PuntoActaMiembro.objects.bulk_create([PuntoActaMiembro(punto=punto, profesor_id=pid) for pid in miembro_ids])

    return avisos


@transaction.atomic
def crear_acta(*, usuario: str = "usuario", puntos: list[dict], **campos) -> tuple[Acta, list[str]]:
    numero = (campos.get("numero") or "").strip()
    if not numero:
        raise ValueError("El número de acta es obligatorio")

    fecha = _parsear_fecha(campos.get("fecha"))
    anio = fecha.year if fecha else date.today().year

    try:
        acta = Acta.objects.create(
            numero=numero, fecha=fecha, anio=anio, resumen=_o_none(campos.get("resumen")),
            hora_inicio=_o_none(campos.get("hora_inicio")), hora_fin=_o_none(campos.get("hora_fin")),
            lugar=_o_none(campos.get("lugar")) or "Puerto Vallarta, Jalisco",
            sede=_o_none(campos.get("sede")), asistentes=_o_none(campos.get("asistentes")),
        )
    except IntegrityError as exc:
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    avisos = _reemplazar_puntos(acta, puntos, usuario)
    registrar(usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="crear", valor_nuevo=numero)
    return acta, avisos


@transaction.atomic
def actualizar_acta(acta: Acta, *, usuario: str = "usuario", puntos: list[dict], **campos) -> tuple[Acta, list[str]]:
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
        acta.save()
    except IntegrityError as exc:
        raise NumeroDuplicadoError(f"Ya existe un acta con número {numero!r}") from exc

    avisos = _reemplazar_puntos(acta, puntos, usuario)
    registrar(usuario=usuario, entidad="Acta", entidad_id=acta.id, accion="modificar", valor_nuevo="datos actualizados")
    return acta, avisos
