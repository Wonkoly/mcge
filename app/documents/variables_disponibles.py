"""Catálogo de variables que el coordinador puede insertar al redactar el
cuerpo de un tipo de documento personalizado (taller de plantillas en
Documentos) — ahora con el set completo de campos razonables de
Alumno/Profesor/Acta, no solo los básicos. Cualquier otra variable que
aparezca en el cuerpo y no esté aquí (ej. destinatario_nombre — un oficio
puede ir dirigido fuera de la maestría) se detecta sola por texto (ver
app/services/tipo_documento_service.py) y se pide como campo libre al
generar el documento real — no hace falta declararla aquí.
"""

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
    "profesor_nombre": "Nombre (con tratamiento, ej. \"la Dra. X\")",
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
    "General": VARIABLES_GENERALES,
}

TODAS_LAS_VARIABLES = {**VARIABLES_ALUMNO, **VARIABLES_PROFESOR, **VARIABLES_ACTA, **VARIABLES_GENERALES}
