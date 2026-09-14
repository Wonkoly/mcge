"""Genera dos documentos de referencia para que el coordinador pueda ajustar
a mano (en Word) el acomodo de imágenes de las plantillas reales, sin que
eso rompa las etiquetas que usa la app para rellenar datos:

    Docs/Templates/GUIA_para_editar_plantillas.docx
    Docs/Templates/EJEMPLO_estructura_correcta.docx

Se corre a mano cuando cambien las variables de app/documents/generador.py
(para mantener la guía actualizada) — no se ejecuta como parte de la app:

    python scripts/generar_guia_plantillas.py

Contexto del problema real (encontrado inspeccionando los .docx reales):
en `acta.docx`, `oficio_comite_tutorial_alumno.docx`,
`oficio_comite_tutorial_docente.docx` y `constancia_evaluador_aspirantes.docx`
el número de folio ({{ numero }} / {{ oficio_numero }} / {{ constancia_numero }})
quedó escrito DENTRO del header de Word, pegado al mismo bloque de texto
del membrete institucional — junto a las imágenes del logo. Cuando docxtpl
sustituye ese texto, el layout de las imágenes ancladas a ese párrafo se
puede mover. La solución no es de código: es mover esa etiqueta al CUERPO
del documento, exactamente como ya está bien hecho en `oficio_asignacion.docx`
(primer párrafo del cuerpo). Este script documenta esa regla y once más.
"""

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "Docs" / "Templates"

# Plantillas donde el folio quedó atrapado en el header, junto al membrete —
# hay que sacarlo de ahí y ponerlo en el cuerpo (ver EJEMPLO_estructura_correcta.docx).
PLANTILLAS_CON_FOLIO_EN_HEADER = {
    "acta.docx": "Acta {{ numero }}",
    "oficio_comite_tutorial_alumno.docx": "{{ oficio_numero }}",
    "oficio_comite_tutorial_docente.docx": "{{ oficio_numero }}",
    "constancia_evaluador_aspirantes.docx": "Constancia: {{ constancia_numero }}",
}

# Variables disponibles por plantilla — sacadas directamente de los
# contextos que arma app/documents/generador.py. Si agregas o renombras un
# campo ahí, actualiza esta tabla y vuelve a correr el script.
DOCUMENTOS = [
    (
        "oficio_asignacion.docx",
        "Oficio de asignación de Director/Codirector de tesis (al alumno)",
        [
            ("oficio_numero", "Folio del oficio, ej. \"123/2026\". Ya viene en el CUERPO — este archivo es el ejemplo a seguir."),
            ("fecha_larga", "Fecha completa en texto: \"13 de septiembre de 2026\"."),
            ("alumno_nombre", "Nombre del alumno, ya capitalizado."),
            ("rol_texto", "\"Director\", \"Directora\", \"Codirector\" o \"Codirectora\"."),
            ("rol_texto_corto", "Lo mismo en minúsculas: \"director\", \"directora\", etc."),
            ("articulo_del_rol", "\"del\" o \"de la\" (para \"las funciones ___ Director\")."),
            ("profesor_nombre", "Nombre del profesor con tratamiento: \"la Dra. Araceli Zamora Camacho\"."),
            ("tesis_titulo", "Título de la tesis (puede venir vacío)."),
            ("acta_numero", "Número de acta relacionada (puede venir vacío)."),
            ("acta_fecha", "Fecha del acta relacionada (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("coordinador_nombre", "Nombre de quien firma como Coordinador(a)."),
        ],
    ),
    (
        "constancia_director_individual.docx",
        "Constancia individual de Director/Codirector de tesis",
        [
            ("constancia_numero", "Folio de la constancia."),
            ("coordinador_nombre", "Nombre de quien firma."),
            ("profesor_nombre", "Nombre del profesor con tratamiento."),
            ("rol_texto", "\"Director\", \"Directora\", \"Codirector\" o \"Codirectora\"."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("tesis_titulo", "Título de la tesis (puede venir vacío)."),
            ("fecha_grado", "Fecha de grado, si ya existe (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
        ],
    ),
    (
        "oficio_comite_tutorial_alumno.docx",
        "Oficio de comité tutorial dirigido al alumno",
        [
            ("oficio_numero", "Folio del oficio. ⚠️ Hoy está metido en el HEADER — sácalo de ahí (ver abajo)."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("acta_referencia", "Texto ya armado tipo \"el Acta 04/2022 con fecha del ...\" (puede venir vacío)."),
            ("comite_miembros", "LISTA de nombres ya tratados (\"el Dr. ...\"). Usa el patrón de lista — ver EJEMPLO."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
    (
        "oficio_comite_tutorial_docente.docx",
        "Oficio de comité tutorial dirigido a cada profesor tutor (una carta por profesor)",
        [
            ("oficio_numero", "Folio del oficio. ⚠️ Hoy está metido en el HEADER — sácalo de ahí (ver abajo)."),
            ("profesor_tratamiento_nombre", "Nombre del profesor destinatario de ESTA carta, con tratamiento."),
            ("acta_referencia", "Texto ya armado tipo \"el Acta 04/2022 con fecha del ...\" (puede venir vacío)."),
            ("otros_miembros", "LISTA de los OTROS tutores (sin el destinatario). Patrón de lista — ver EJEMPLO."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
    (
        "constancia_lector.docx",
        "Constancia de Lector de tesis",
        [
            ("constancia_numero", "Folio de la constancia."),
            ("coordinador_nombre", "Nombre de quien firma."),
            ("profesor_nombre", "Nombre del profesor lector, con tratamiento."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("tesis_titulo", "Título de la tesis (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
        ],
    ),
    (
        "constancia_jurado.docx",
        "Constancia de Sinodal / Jurado de examen",
        [
            ("constancia_numero", "Folio de la constancia."),
            ("coordinador_nombre", "Nombre de quien firma."),
            ("profesor_nombre", "Nombre del sinodal, con tratamiento."),
            ("a_profesor", "\"Al Dr. X\" / \"A la Dra. X\" — ya armado, para el saludo inicial."),
            ("cargo_texto", "\"Presidente\", \"Secretario\" o \"Vocal\"."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("fecha_examen", "Fecha del examen (puede venir vacío)."),
            ("tesis_titulo", "Título de la tesis (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
        ],
    ),
    (
        "oficio_invitacion_jurado.docx",
        "Oficio de invitación a Sinodal / Jurado de examen",
        [
            ("oficio_numero", "Folio del oficio."),
            ("profesor_tratamiento_nombre", "Nombre del sinodal invitado, con tratamiento."),
            ("acta_referencia", "Texto ya armado tipo \"el Acta 04/2022 con fecha del ...\" (puede venir vacío)."),
            ("cargo_texto", "\"Presidente\", \"Secretario\" o \"Vocal\"."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("tesis_titulo", "Título de la tesis (puede venir vacío)."),
            ("fecha_examen", "Fecha del examen (puede venir vacío)."),
            ("hora_examen", "Hora del examen (puede venir vacío)."),
            ("lugar_examen", "Lugar del examen (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
    (
        "constancia_evaluador_aspirantes.docx",
        "Constancia de evaluador de aspirantes",
        [
            ("constancia_numero", "Folio de la constancia. ⚠️ Hoy está metido en el HEADER — sácalo de ahí (ver abajo)."),
            ("coordinador_nombre", "Nombre de quien firma."),
            ("profesor_nombre", "Nombre del profesor evaluador, con tratamiento."),
            ("a_profesor", "\"Al Dr. X\" / \"A la Dra. X\" — ya armado, para el saludo inicial."),
            ("ciclo", "Ciclo escolar, ej. \"2026 B\"."),
            ("fecha_entrevista", "Fecha de la entrevista (puede venir vacío)."),
            ("lugar", "Lugar de la entrevista (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
        ],
    ),
    (
        "oficio_asentamiento_creditos.docx",
        "Oficio de asentamiento de créditos de trabajo de campo",
        [
            ("oficio_numero", "Folio del oficio."),
            ("destinatario_nombre", "A quién va dirigido (por defecto \"Coordinadora de Control Escolar\")."),
            ("creditos", "Número de créditos a asentar."),
            ("materia_nombre", "Nombre de la materia."),
            ("materia_clave", "Clave de la materia."),
            ("ciclo", "Ciclo escolar, ej. \"2026 B\"."),
            ("alumno_nombre", "Nombre del alumno."),
            ("alumno_codigo", "Código de alumno."),
            ("acta_referencia", "Texto ya armado tipo \"el Acta 04/2022 con fecha del ...\" (puede venir vacío)."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
    (
        "oficio_permiso_municipio.docx",
        "Oficio de solicitud de permiso/registro de exploración a un municipio",
        [
            ("oficio_numero", "Folio del oficio."),
            ("destinatario_nombre", "Nombre de la autoridad municipal destinataria."),
            ("destinatario_cargo", "Cargo de esa autoridad."),
            ("municipio", "Nombre del municipio."),
            ("cuerpo_solicitud", "Texto LIBRE del primer párrafo de la solicitud (cada caso describe un proyecto distinto)."),
            ("cuerpo_parrafo2", "Texto LIBRE de un segundo párrafo, opcional."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("fecha_larga", "Fecha completa en texto."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
    (
        "acta.docx",
        "Acta de Junta Académica",
        [
            ("numero", "Número de acta, ej. \"07/2026\". ⚠️ Hoy está metido en el HEADER — sácalo de ahí (ver abajo)."),
            ("lugar", "Lugar de la reunión."),
            ("hora_inicio", "Hora de inicio."),
            ("hora_fin", "Hora de fin."),
            ("sede", "Sede de la reunión."),
            ("asistentes", "Texto libre con la lista de asistentes."),
            ("fecha_larga", "Fecha completa en texto."),
            ("puntos", "LISTA de puntos del orden del día. Cada punto trae: numero_texto (\"uno\", \"dos\"...), titulo, resolutivo. Patrón de lista — ver EJEMPLO."),
            ("lema_ciclo", "Lema institucional del ciclo, opcional."),
            ("coordinador_nombre", "Nombre de quien firma."),
        ],
    ),
]


def _titulo(doc, texto):
    p = doc.add_heading(texto, level=1)
    return p


def _subtitulo(doc, texto):
    doc.add_heading(texto, level=2)


def _parrafo(doc, texto, *, negritas=False, cursivas=False, color=None, tamano=None):
    p = doc.add_paragraph()
    run = p.add_run(texto)
    run.bold = negritas
    run.italic = cursivas
    if color:
        run.font.color.rgb = RGBColor(*color)
    if tamano:
        run.font.size = Pt(tamano)
    return p


def generar_guia():
    doc = Document()
    doc.add_heading("Guía para editar las plantillas de documentos (MCG)", level=0)

    _parrafo(
        doc,
        "El programa nunca inventa el formato de un oficio o constancia: abre el archivo .docx "
        "que le indiques, busca las etiquetas con doble llave (como {{ nombre }}) y las cambia "
        "por el dato real. Todo lo demás del documento — texto fijo, tipografía, membrete, "
        "imágenes, firma — se queda exactamente como lo dejaste en Word.",
    )
    _parrafo(
        doc,
        "Por eso el acomodo de las imágenes del membrete y del pie de página es trabajo tuyo en "
        "Word, no del programa: ahí sí tienes las herramientas correctas (ajustar texto, alinear, "
        "traer al frente/atrás) para dejarlas exactas. La única condición es que el ENCABEZADO y "
        "el PIE DE PÁGINA de Word queden sin ninguna etiqueta {{ }} adentro — ver la regla 1.",
    )

    _subtitulo(doc, "Cómo funciona esta carpeta")
    _parrafo(
        doc,
        "En esta misma carpeta (Docs/Templates/) tienes una copia de cada plantilla que usa hoy "
        "el programa. Ábrelas en Word, ajusta las imágenes a tu gusto, y cuando termines dime "
        "cuáles ya quedaron listas — las reemplazo en app/documents/templates_docx/ con el mismo "
        "nombre de archivo. No hace falta reiniciar el programa para que tome un .docx nuevo, "
        "solo el archivo tiene que quedar con el mismo nombre.",
    )

    _subtitulo(doc, "Regla 1 — Nada de {{ }} dentro del header ni del footer de Word")
    _parrafo(
        doc,
        "Revisé los .docx reales y encontré el problema exacto: en estos 4 archivos, el número de "
        "folio quedó escrito DENTRO del encabezado de Word, pegado al mismo bloque de texto del "
        "membrete — justo al lado de las imágenes del logo:",
    )
    for nombre, fragmento in PLANTILLAS_CON_FOLIO_EN_HEADER.items():
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(nombre + " ").bold = True
        p.add_run(f'→ dentro del header dice: "{fragmento}"')
    _parrafo(
        doc,
        "Cuando el programa rellena ese texto, el ancla de las imágenes de ese mismo párrafo se "
        "puede recorrer — de ahí que el membrete se vea descuadrado. La solución: CORTA esa "
        "etiqueta del header y PÉGALA como el primer renglón del CUERPO del documento (fuera del "
        "header, ya en el área de texto normal), alineada donde tú quieras que se vea el folio. "
        "Así ya no comparte párrafo con ninguna imagen y puedes mover los logos del header "
        "libremente sin que nada se desacomode.",
    )
    _parrafo(
        doc,
        "\"oficio_asignacion.docx\" (en esta misma carpeta) ya tiene el folio bien puesto en el "
        "cuerpo, como primer renglón del documento — ábrelo para ver exactamente cómo debe quedar. "
        "También revisa EJEMPLO_estructura_correcta.docx, en esta misma carpeta, con un mockup "
        "simple de las 3 zonas (encabezado / cuerpo / pie de página) y comentarios de Word "
        "explicando cada etiqueta.",
    )

    _subtitulo(doc, "Regla 2 — Una lista (comité, puntos de acta) va en 3 renglones separados")
    _parrafo(
        doc,
        "Cuando un dato es una LISTA (por ejemplo, los profesores de un comité tutorial), no se "
        "escribe una sola etiqueta — se arma con 3 renglones, cada uno como un párrafo propio, "
        "sin nada más de texto compartiendo ese renglón:",
    )
    for texto in ["{%for m in comite_miembros %}", "{{ m }}", "{%endfor %}"]:
        p = doc.add_paragraph(texto, style="List Bullet")
        p.runs[0].font.name = "Consolas"
    _parrafo(
        doc,
        "\"oficio_comite_tutorial_alumno.docx\" (en esta misma carpeta) ya trae este patrón "
        "correctamente armado — puedes copiarlo tal cual a otra plantilla que necesite una lista.",
    )

    _subtitulo(doc, "Regla 3 — Cuidado con el autocorrector al escribir una etiqueta")
    _parrafo(
        doc,
        "Escribe la etiqueta completa de un jalón ({{ nombre_variable }}) ANTES de aplicarle "
        "negritas, cursivas o cambiarle la fuente. Si formateas solo una parte de la etiqueta a "
        "medio escribir, Word puede partirla en pedazos por dentro y el programa ya no la "
        "reconoce. Si algo no se rellena al generar el documento, ese es el motivo más común — "
        "bórrala y vuelve a escribirla completa.",
    )

    _subtitulo(doc, "Variables disponibles por documento")
    _parrafo(
        doc,
        "Escribe el nombre exactamente como aparece aquí, entre doble llave: {{ así }}. Mayúsculas "
        "y guiones bajos importan.",
    )
    for nombre_archivo, descripcion, variables in DOCUMENTOS:
        doc.add_heading(f"{nombre_archivo} — {descripcion}", level=3)
        tabla = doc.add_table(rows=1, cols=2)
        tabla.style = "Light Grid Accent 1"
        tabla.rows[0].cells[0].text = "Variable"
        tabla.rows[0].cells[1].text = "Qué es"
        for variable, explicacion in variables:
            fila = tabla.add_row()
            fila.cells[0].text = "{{ " + variable + " }}"
            fila.cells[1].text = explicacion
        doc.add_paragraph()

    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / "GUIA_para_editar_plantillas.docx"
    doc.save(ruta)
    print(f"Escrito: {ruta}")


def generar_ejemplo():
    doc = Document()

    encabezado = doc.sections[0].header
    encabezado.is_linked_to_previous = False
    p = encabezado.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        "[ ZONA LIBRE PARA IMÁGENES DEL MEMBRETE — logos, sellos, etc. "
        "Acomódalos aquí con las herramientas de Word. El programa NUNCA lee "
        "ni modifica esta zona — NO escribas ninguna etiqueta {{ }} aquí adentro. ]"
    )
    run.italic = True
    run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    pie = doc.sections[0].footer
    pie.is_linked_to_previous = False
    p = pie.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(
        "[ ZONA LIBRE PARA PIE DE PÁGINA — dirección, teléfono, sello, número "
        "de página, etc. Tampoco lleva ninguna etiqueta {{ }}. ]"
    )
    run.italic = True
    run.font.color.rgb = RGBColor(0x80, 0x80, 0x80)

    doc.add_heading("Ejemplo de estructura correcta", level=1)
    _parrafo(
        doc,
        "Este archivo es solo un mockup de referencia — no está ligado a ningún oficio real. "
        "Muestra dónde va cada cosa. El cuerpo de aquí para abajo SÍ lo lee el programa.",
        cursivas=True,
        color=(0x80, 0x80, 0x80),
    )
    doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run_folio = p.add_run("{{ oficio_numero }}")
    c1 = doc.add_comment(
        runs=run_folio,
        text=(
            'El folio va aquí, en el CUERPO (primer renglón), NO en el header — así ya no '
            'comparte párrafo con ninguna imagen del membrete. Este es exactamente el lugar '
            'donde ya lo tiene bien puesto "oficio_asignacion.docx".'
        ),
        author="Guía de plantillas",
        initials="GP",
    )

    p = doc.add_paragraph()
    run_fecha = p.add_run("Puerto Vallarta, Jalisco, a {{ fecha_larga }}")
    doc.add_comment(
        runs=run_fecha,
        text='Fecha ya armada en texto largo, ej. "13 de septiembre de 2026".',
        author="Guía de plantillas",
        initials="GP",
    )
    doc.add_paragraph()

    p = doc.add_paragraph()
    run_nombre = p.add_run("C. {{ alumno_nombre }}")
    doc.add_comment(
        runs=run_nombre,
        text="Nombre del destinatario — ya viene capitalizado, sin necesidad de arreglarlo.",
        author="Guía de plantillas",
        initials="GP",
    )
    doc.add_paragraph("P R E S E N T E")
    doc.add_paragraph()

    p = doc.add_paragraph()
    run_cuerpo = p.add_run(
        "Por este medio informo que se aprueba la designación de {{ profesor_nombre }} "
        "para la dirección del trabajo de investigación titulado “{{ tesis_titulo }}”."
    )
    doc.add_comment(
        runs=run_cuerpo,
        text=(
            "Puedes mezclar texto fijo con varias etiquetas en el mismo párrafo sin problema — "
            "la regla de \"un renglón, una etiqueta\" solo aplica a las LISTAS (ver más abajo)."
        ),
        author="Guía de plantillas",
        initials="GP",
    )
    doc.add_paragraph()

    doc.add_paragraph("Comité tutorial asignado:")
    p1 = doc.add_paragraph("{%for m in comite_miembros %}", style="List Bullet")
    p2 = doc.add_paragraph("{{ m }}", style="List Bullet")
    p3 = doc.add_paragraph("{%endfor %}", style="List Bullet")
    for p in (p1, p2, p3):
        for r in p.runs:
            r.font.name = "Consolas"
    doc.add_comment(
        runs=[p1.runs[0], p3.runs[0]],
        text=(
            "EJEMPLO DE LISTA: estos 3 renglones deben ser CADA UNO el contenido completo de su "
            "propio párrafo (no los juntes en una sola línea ni les agregues más texto). Así se "
            "repite un renglón por cada profesor del comité. Bórralos si tu documento no necesita "
            "una lista. \"oficio_comite_tutorial_alumno.docx\" ya trae este mismo patrón."
        ),
        author="Guía de plantillas",
        initials="GP",
    )
    doc.add_paragraph()

    doc.add_paragraph("Atentamente")
    p = doc.add_paragraph()
    run_coord = p.add_run("{{ coordinador_nombre }}")
    doc.add_comment(
        runs=run_coord,
        text="Nombre de quien firma — sale de Configuración, no hay que capturarlo cada vez.",
        author="Guía de plantillas",
        initials="GP",
    )
    doc.add_paragraph("Coordinador(a) de la Maestría en Geofísica")

    DESTINO.mkdir(parents=True, exist_ok=True)
    ruta = DESTINO / "EJEMPLO_estructura_correcta.docx"
    doc.save(ruta)
    print(f"Escrito: {ruta}")


if __name__ == "__main__":
    generar_guia()
    generar_ejemplo()
