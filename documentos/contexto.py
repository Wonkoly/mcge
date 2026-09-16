"""Catálogo de variables del taller de plantillas — puerto y ampliación de
app/documents/variables_disponibles.py. Además de Alumno/Profesor/Acta/
Generales (lo único que existía), agrega Dirección/Comité Tutorial/Lector/
Sinodal (kind-napping-grove.md, "Rediseño del Módulo 4"): cada `contexto_*`
de abajo es la MISMA función que arma el grupo de variables tanto para el
ejemplo del buscador (`ejemplos_variables`) como para la generación real de
un punto "personalizado" de Acta (`documentos.generador.
generar_documento_personalizado`, Fase 3.2) — un solo catálogo, no dos
desincronizados como en Flask.

Cualquier otra variable que aparezca en el cuerpo y no esté en
TODAS_LAS_VARIABLES (ej. destinatario_nombre) se detecta sola por texto
(ver variables_libres) y se pide como campo libre al generar el documento
real — no hace falta declararla aquí."""

import re

from documentos import texto

VARIABLES_ALUMNO = {
    "alumno_nombre": "Nombre completo",
    "alumno_codigo": "Código de alumno",
    "alumno_ciclo_ingreso": "Ciclo de ingreso",
    "alumno_tesis_titulo": "Título de la tesis",
    "alumno_dictamen": "Dictamen (MIGE/MIGF)",
    "alumno_correo_institucional": "Correo institucional",
    "alumno_correo_personal": "Correo personal",
    "alumno_telefono": "Teléfono",
    "alumno_creditos_acumulados": "Créditos acumulados",
    "alumno_creditos_faltantes": "Créditos faltantes",
    "alumno_promedio": "Promedio",
    "alumno_cvu": "CVU (CONACYT/CONAHCYT)",
    "alumno_lies": "Línea de Investigación (LIES)",
    "alumno_maximo_ciclo": "Máximo ciclo permitido",
}

VARIABLES_PROFESOR = {
    "profesor_nombre": 'Nombre (con tratamiento, ej. "la Dra. X")',
    "profesor_nombre_simple": "Nombre sin tratamiento",
    "profesor_correo": "Correo",
    "profesor_telefono": "Teléfono",
    "profesor_cvu": "CVU (CONACYT/CONAHCYT)",
    "profesor_linea_investigacion": "Línea de investigación",
    "profesor_lies": "Línea de Investigación (LIES)",
    "profesor_sni": "Nivel SNI",
    "profesor_centro_universitario": "Centro universitario",
}

VARIABLES_ACTA = {
    "acta_numero": "Número de acta",
    "acta_fecha": "Fecha del acta",
    "acta_lugar": "Lugar de la sesión",
    "acta_sede": "Sede (edificio/sala)",
    "acta_hora_inicio": "Hora de inicio",
    "acta_hora_fin": "Hora de cierre",
    "acta_asistentes": "Asistentes (texto libre)",
}

VARIABLES_DIRECCION = {
    "director_nombre": "Nombre del Director (con tratamiento)",
    "codirector_nombre": "Nombre del Codirector, si tiene (con tratamiento)",
    "tiene_codirector": '"Sí" / "No"',
    "rol_texto": "Rol de este punto: Director/Directora o Codirector/Codirectora",
    "articulo_del_rol": '"del" / "de la", concuerda con el género del rol',
    "fecha_asignacion_direccion": "Fecha de asignación (texto largo)",
}

VARIABLES_COMITE = {
    "comite_ciclo": "Ciclo del comité tutorial",
    "comite_fecha_inicio": "Fecha de inicio del comité (texto largo)",
}

VARIABLES_LECTOR = {
    "lector_1_nombre": "Nombre del 1er lector",
    "lector_1_fecha": "Fecha de asignación del 1er lector",
    "lector_2_nombre": "Nombre del 2do lector",
    "lector_2_fecha": "Fecha de asignación del 2do lector",
    "lector_3_nombre": "Nombre del 3er lector",
    "lector_3_fecha": "Fecha de asignación del 3er lector",
}

VARIABLES_SINODAL = {
    "sinodal_presidente_nombre": "Nombre del Presidente del jurado",
    "sinodal_secretario_nombre": "Nombre del Secretario del jurado",
    "sinodal_vocal_nombre": "Nombre del Vocal del jurado",
    "examen_fecha": "Fecha del examen",
    "examen_hora": "Hora del examen",
    "examen_lugar": "Lugar del examen",
}

VARIABLES_GENERALES = {
    "numero_documento": "Folio del documento",
    "fecha_larga": "Fecha completa en texto (del día que se genera)",
    "coordinador_nombre": "Nombre de quien firma como Coordinador(a)",
    "lema_ciclo": "Lema institucional del ciclo (opcional)",
}

GRUPOS_VARIABLES = {
    "Alumno": VARIABLES_ALUMNO,
    "Profesor": VARIABLES_PROFESOR,
    "Acta": VARIABLES_ACTA,
    "Dirección": VARIABLES_DIRECCION,
    "Comité Tutorial": VARIABLES_COMITE,
    "Lector": VARIABLES_LECTOR,
    "Sinodal": VARIABLES_SINODAL,
    "General": VARIABLES_GENERALES,
}

TODAS_LAS_VARIABLES = {clave: etiqueta for grupo in GRUPOS_VARIABLES.values() for clave, etiqueta in grupo.items()}

# Variables de lista (bucle Jinja, ej. {% for p in profesores_lista %}) — no
# son {{ variable }} planas, se insertan con su propio botón y no aparecen
# en el catálogo buscable ni en TODAS_LAS_VARIABLES.
LISTAS_DISPONIBLES = {
    "profesores_lista": "Lista de profesores marcados a mano en el punto",
    "comite_miembros": "Miembros del comité tutorial de la fuente",
    "sinodales_lista": "Sinodales asignados al alumno de la fuente",
}

_PATRON_VARIABLE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


def variables_libres(cuerpo_texto: str) -> list[str]:
    """Variables que aparecen en el cuerpo pero no son del catálogo fijo —
    ej. destinatario_nombre. Se piden como campo de texto libre al generar
    un documento real."""
    encontradas = dict.fromkeys(_PATRON_VARIABLE.findall(cuerpo_texto or ""))  # preserva orden, sin duplicados
    return [v for v in encontradas if v not in TODAS_LAS_VARIABLES]


def variables_usadas(cuerpo_texto: str) -> set[str]:
    return set(_PATRON_VARIABLE.findall(cuerpo_texto or ""))


# --------------------------------------------------------- Context builders
# Cada función arma el grupo de variables a partir del registro real
# correspondiente. Se reutilizan tal cual desde ejemplos_variables() (abajo)
# y desde documentos.generador.generar_documento_personalizado (Fase 3.2).


def contexto_alumno(alumno) -> dict:
    return {
        "alumno_nombre": texto.formatear_nombre(alumno.nombre),
        "alumno_codigo": alumno.codigo,
        "alumno_ciclo_ingreso": alumno.ciclo_ingreso or "",
        "alumno_tesis_titulo": alumno.tesis_titulo or "",
        "alumno_dictamen": alumno.dictamen or "",
        "alumno_correo_institucional": alumno.correo_institucional or "",
        "alumno_correo_personal": alumno.correo_personal or "",
        "alumno_telefono": alumno.telefono or "",
        "alumno_creditos_acumulados": alumno.creditos_acumulados if alumno.creditos_acumulados is not None else "",
        "alumno_creditos_faltantes": alumno.creditos_faltantes if alumno.creditos_faltantes is not None else "",
        "alumno_promedio": alumno.promedio if alumno.promedio is not None else "",
        "alumno_cvu": alumno.cvu or "",
        "alumno_lies": alumno.lies.nombre if alumno.lies else "",
        "alumno_maximo_ciclo": alumno.maximo_ciclo or "",
    }


def contexto_profesor(profesor) -> dict:
    return {
        "profesor_nombre": texto.nombre_con_tratamiento(profesor),
        "profesor_nombre_simple": texto.formatear_nombre(profesor.nombre),
        "profesor_correo": profesor.correo or "",
        "profesor_telefono": profesor.telefono or "",
        "profesor_cvu": profesor.cvu or "",
        "profesor_linea_investigacion": profesor.linea_investigacion or "",
        "profesor_lies": profesor.lies.nombre if profesor.lies else "",
        "profesor_sni": profesor.sni or "",
        "profesor_centro_universitario": profesor.centro_universitario or "",
    }


def contexto_acta(acta) -> dict:
    return {
        "acta_numero": acta.numero,
        "acta_fecha": texto.fecha_larga(acta.fecha) if acta.fecha else "",
        "acta_lugar": acta.lugar or "",
        "acta_sede": acta.sede or "",
        "acta_hora_inicio": acta.hora_inicio or "",
        "acta_hora_fin": acta.hora_fin or "",
        "acta_asistentes": acta.asistentes or "",
    }


def _rol_texto_y_articulo(direccion) -> tuple[str, str]:
    femenino = texto.es_femenino(direccion.profesor)
    if direccion.rol == "Director":
        return ("Directora" if femenino else "Director"), ("de la" if femenino else "del")
    return ("Codirectora" if femenino else "Codirector"), ("de la" if femenino else "del")


def contexto_direccion(direccion) -> dict:
    """`direccion` es el registro puntual sobre el que trata el punto (un
    Director *o* un Codirector) — se busca también al "hermano" vigente del
    mismo alumno para poder mencionar a ambos en el mismo documento."""
    from actas.models import Direccion

    hermano = (
        Direccion.objects.filter(alumno_id=direccion.alumno_id, fecha_fin__isnull=True)
        .exclude(rol=direccion.rol)
        .select_related("profesor")
        .first()
    )
    director = direccion if direccion.rol == "Director" else hermano
    codirector = direccion if direccion.rol == "Codirector" else hermano
    rol_texto, articulo = _rol_texto_y_articulo(direccion)
    return {
        "director_nombre": texto.nombre_con_tratamiento(director.profesor) if director else "",
        "codirector_nombre": texto.nombre_con_tratamiento(codirector.profesor) if codirector else "",
        "tiene_codirector": "Sí" if codirector else "No",
        "rol_texto": rol_texto,
        "articulo_del_rol": articulo,
        "fecha_asignacion_direccion": texto.fecha_larga(direccion.fecha_inicio) if direccion.fecha_inicio else "",
    }


def contexto_comite(comite) -> dict:
    return {
        "comite_ciclo": comite.ciclo or "",
        "comite_fecha_inicio": texto.fecha_larga(comite.fecha_inicio) if comite.fecha_inicio else "",
    }


def lista_comite_miembros(comite) -> list[dict]:
    return [{"nombre": texto.nombre_con_tratamiento(m.profesor)} for m in comite.miembros.select_related("profesor").all()]


def contexto_lectores(alumno) -> dict:
    from actas.models import Lector

    lectores = list(Lector.objects.filter(alumno_id=alumno.id).select_related("profesor").order_by("fecha")[:3])
    ctx = {}
    for i in range(3):
        n = i + 1
        lector = lectores[i] if i < len(lectores) else None
        ctx[f"lector_{n}_nombre"] = texto.nombre_con_tratamiento(lector.profesor) if lector else ""
        ctx[f"lector_{n}_fecha"] = (texto.fecha_larga(lector.fecha) if lector and lector.fecha else "")
    return ctx


def contexto_sinodales(alumno) -> dict:
    from actas.models import Sinodal

    sinodales = list(Sinodal.objects.filter(alumno_id=alumno.id).select_related("profesor"))
    por_cargo = {s.cargo: s for s in sinodales}
    primero = sinodales[0] if sinodales else None
    return {
        "sinodal_presidente_nombre": texto.nombre_con_tratamiento(por_cargo["Presidente"].profesor) if "Presidente" in por_cargo else "",
        "sinodal_secretario_nombre": texto.nombre_con_tratamiento(por_cargo["Secretario"].profesor) if "Secretario" in por_cargo else "",
        "sinodal_vocal_nombre": texto.nombre_con_tratamiento(por_cargo["Vocal"].profesor) if "Vocal" in por_cargo else "",
        "examen_fecha": texto.fecha_larga(primero.fecha_examen) if primero and primero.fecha_examen else "",
        "examen_hora": primero.hora_examen if primero else "",
        "examen_lugar": primero.lugar_examen if primero else "",
    }


def lista_sinodales(alumno) -> list[dict]:
    from actas.models import Sinodal

    return [
        {"nombre": texto.nombre_con_tratamiento(s.profesor)}
        for s in Sinodal.objects.filter(alumno_id=alumno.id).select_related("profesor")
    ]


def ejemplos_variables() -> dict[str, str]:
    """Un valor de ejemplo real (no inventado) por variable, para que el
    buscador del taller muestre cómo se ve cada dato antes de insertarlo.
    Toma el primer registro que haya de cada tipo — si todavía no hay
    datos para un grupo, sus variables simplemente no aparecen con
    ejemplo."""
    from actas.models import Acta, ComiteTutorial, Direccion
    from alumnos.models import Alumno
    from profesores.models import Profesor

    ejemplos: dict[str, str] = {}

    alumno = Alumno.objects.order_by("id").first()
    if alumno:
        ejemplos.update(contexto_alumno(alumno))
        ejemplos.update(contexto_lectores(alumno))
        ejemplos.update(contexto_sinodales(alumno))

    profesor = Profesor.objects.filter(tratamiento__isnull=False).order_by("id").first()
    if profesor:
        ejemplos.update(contexto_profesor(profesor))

    acta = Acta.objects.order_by("-id").first()
    if acta:
        ejemplos.update(contexto_acta(acta))

    direccion = (
        Direccion.objects.filter(fecha_fin__isnull=True).select_related("profesor", "alumno").order_by("-id").first()
    )
    if direccion:
        ejemplos.update(contexto_direccion(direccion))

    comite = (
        ComiteTutorial.objects.filter(fecha_fin__isnull=True).prefetch_related("miembros__profesor").order_by("-id").first()
    )
    if comite:
        ejemplos.update(contexto_comite(comite))

    ejemplos.update(
        {
            "numero_documento": "CUCPV/MCG/001/2026",
            "fecha_larga": texto.fecha_larga(),
            "coordinador_nombre": "Dr. Héctor Javier Rendón Contreras",
            "lema_ciclo": "",
        }
    )
    return ejemplos
