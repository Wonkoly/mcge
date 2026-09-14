"""Catálogo fijo de variables que el coordinador puede insertar al
redactar el cuerpo de un tipo de documento personalizado (taller de
plantillas en Documentos). Cualquier otra variable que aparezca en el
cuerpo (ej. destinatario_nombre — un oficio puede ir dirigido fuera de la
maestría, no siempre hay un alumno/profesor de por medio) se detecta sola
por texto (ver app/services/tipo_documento_service.py) y se pide como
campo libre al generar el documento real — no hace falta declararla aquí.
"""

VARIABLES_ALUMNO = {
    "alumno_nombre": "Nombre del alumno",
    "alumno_codigo": "Código de alumno",
    "alumno_tesis_titulo": "Título de la tesis",
    "alumno_ciclo_ingreso": "Ciclo de ingreso",
}

VARIABLES_PROFESOR = {
    "profesor_nombre": "Nombre del profesor (con tratamiento, ej. \"la Dra. X\")",
}

VARIABLES_GENERALES = {
    "numero_documento": "Folio del documento",
    "fecha_larga": "Fecha completa en texto",
    "coordinador_nombre": "Nombre de quien firma como Coordinador(a)",
    "lema_ciclo": "Lema institucional del ciclo (opcional)",
}

TODAS_LAS_VARIABLES = {**VARIABLES_ALUMNO, **VARIABLES_PROFESOR, **VARIABLES_GENERALES}
