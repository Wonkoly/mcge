"""Convierte plantillas .docx REALES (machotes ya en blanco hechos por el
coordinador, o documentos reales ya emitidos usados como base) en
plantillas docxtpl — editando el archivo real in situ (copia) para
conservar el formato exacto, no reconstruyendo desde cero.

Fuentes usadas (todas confirmadas en Docs/ el 2026-09-12):
- Docs/Oficios/Plantillas/Comite Tutorial/*.docx (machotes ya en blanco)
- Docs/Constancias/2024/Plantilla - *.docx (machotes ya en blanco)
- Docs/Constancias/2025/000 Machote Constancias.docx (machote de evaluador de aspirantes)
- Docs/Oficios/2024/Formato 2024.docx (invitación a jurado, caso real generalizado)
- Docs/Oficios/2022/Oficio 2022- 006... Asentamiendo creditos...docx (caso real generalizado)

Correr con: python scripts/construir_plantillas_lote2.py
"""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import docx

from _edicion_docx import quitar_numeracion, reemplazar_en_parrafo

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS = BASE_DIR / "Docs"
OUT = BASE_DIR / "app" / "documents" / "templates_docx"
OUT.mkdir(parents=True, exist_ok=True)


def _parrafos_con_texto(doc):
    return [p for p in doc.paragraphs if p.text.strip()]


def _reemplazar_cierre_estandar(doc, incluir_ccp=True):
    """Las líneas de cierre (lema del ciclo, fecha, coordinador) se
    repiten en todos los oficios/constancias reales pero con texto
    DISTINTO según la época (lema institucional cambia cada año/ciclo, y
    el coordinador de 2022 no es el mismo que el de 2024) — por eso esto
    ubica las líneas por POSICIÓN relativa a anclas fijas ("PIENSA Y
    TRABAJA", "Puerto Vallarta", "Coordinador... Maestría") en vez de
    buscar un texto exacto que solo sirve para un año."""
    import re

    parrafos = [p for p in doc.paragraphs if p.text.strip()]

    for i, p in enumerate(parrafos):
        texto = p.text
        # Lema del ciclo: el párrafo justo después de "PIENSA Y TRABAJA"
        # entre comillas — cualquiera que sea su texto (varía cada año).
        if "PIENSA Y TRABAJA" in texto and i + 1 < len(parrafos):
            siguiente = parrafos[i + 1]
            t = siguiente.text.strip()
            if t.startswith(('"', "“")) and (t.endswith('"') or t.endswith("”")):
                reemplazar_en_parrafo(siguiente, t, "{% if lema_ciclo %}“{{ lema_ciclo }}”{% endif %}")
            elif i + 2 < len(parrafos):
                # el lema a veces sigue en un segundo renglón (línea partida)
                otro = parrafos[i + 2]
                if otro.text.strip().endswith(('"', "”")) and "Puerto Vallarta" not in otro.text:
                    reemplazar_en_parrafo(siguiente, t, "{% if lema_ciclo %}“{{ lema_ciclo }}”{% endif %}")
                    reemplazar_en_parrafo(otro, otro.text.strip(), "")

        if "Puerto Vallarta, Jal" in texto:
            m = re.search(r"(\d{1,2} de \w+ de \d{4})", texto)
            if m:
                reemplazar_en_parrafo(p, m.group(1), "{{ fecha_larga }}")
            elif re.search(r"\d{1,2} de mes de 202X", texto):
                reemplazar_en_parrafo(p, "00 de mes de 202X", "{{ fecha_larga }}")

        # El nombre del coordinador vigente en ese momento va SIEMPRE en
        # el párrafo justo antes de la línea de título "Coordinador... de
        # la Maestría" DEL CIERRE/FIRMA — no basta con que la frase
        # aparezca en cualquier parte del párrafo: "El que subscribe, X,
        # Coordinador de la Maestría..." también la contiene pero es la
        # introducción de la constancia, no la firma. Por eso se exige que
        # la línea EMPIECE con "Coordinador" (la firma es solo el título,
        # nada más, en su propio párrafo corto).
        if re.match(r"^Coordinador\w*\s+de\s+la\s+Maestr", texto.strip(), re.IGNORECASE) and i > 0:
            anterior = parrafos[i - 1]
            if anterior.text.strip() and "{{" not in anterior.text:
                reemplazar_en_parrafo(anterior, anterior.text.strip(), "{{ coordinador_nombre }}")
            # El título de este renglón viene fijo en género del
            # coordinador que firmaba CUANDO se emitió el documento
            # original ("Coordinador" o "Coordinadora") — no del que firme
            # ahora. Se normaliza a "Coordinador(a)" para que sirva sin
            # importar quién sea el coordinador vigente.
            for variante in ("Coordinador de la Maestría", "Coordinadora de la Maestría"):
                reemplazar_en_parrafo(p, variante, "Coordinador(a) de la Maestría")


def construir_comite_tutorial_alumno():
    origen = DOCS / "Oficios/Plantillas/Comite Tutorial/000 Asiganacion de Comite Tutorial - Alumno.docx"
    destino = OUT / "oficio_comite_tutorial_alumno.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    for hp in d.sections[0].header.paragraphs:
        reemplazar_en_parrafo(hp, "CUCPV/MCG/000/202X", "{{ oficio_numero }}")
    reemplazar_en_parrafo(ps[0], "C. ALUMNO", "C. {{ alumno_nombre }}")
    reemplazar_en_parrafo(ps[1], "CODIGO: …", "CODIGO: {{ alumno_codigo }}")
    reemplazar_en_parrafo(
        ps[4],
        "el Acta MCG/0X/202X con fecha del 00 de mes del presente año",
        "{% if acta_referencia %}el {{ acta_referencia }}{% else %}un acuerdo{% endif %}",
    )
    # ps[5], ps[6], ps[7] son las 3 líneas "Dra. …" / "Dr. …" / "Dra. …" —
    # se convierten en el envoltorio de un loop multi-párrafo de docxtpl
    # (abre-cuerpo-cierra), reutilizando exactamente esas 3 líneas.
    reemplazar_en_parrafo(ps[5], "Dra. …", "{%for m in comite_miembros %}")
    quitar_numeracion(ps[5])
    reemplazar_en_parrafo(ps[6], "Dr. …", "{{ m }}")
    reemplazar_en_parrafo(ps[7], "Dra. …", "{%endfor %}")
    quitar_numeracion(ps[7])

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_comite_tutorial_docente():
    origen = DOCS / "Oficios/Plantillas/Comite Tutorial/000 Asiganacion de Comite Tutorial - Docente.docx"
    destino = OUT / "oficio_comite_tutorial_docente.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    for hp in d.sections[0].header.paragraphs:
        reemplazar_en_parrafo(hp, "CUCPV/MCG/000/202X", "{{ oficio_numero }}")
    reemplazar_en_parrafo(ps[0], "DR. …", "{{ profesor_tratamiento_nombre }}")
    reemplazar_en_parrafo(
        ps[3],
        "el Acta MCG/00/202X con fecha del 00 de mes del presente año",
        "{% if acta_referencia %}el {{ acta_referencia }}{% else %}un acuerdo{% endif %}",
    )
    reemplazar_en_parrafo(ps[4], "DRA. …", "{%for m in otros_miembros %}")
    quitar_numeracion(ps[4])
    reemplazar_en_parrafo(ps[5], "MTRO. …", "{{ m }}")
    # El machote solo trae 2 líneas de ejemplo para los demás miembros del
    # comité, pero el ciclo puede cerrar aquí mismo y seguir con la
    # siguiente oración en el mismo párrafo sin problema (probado).
    reemplazar_en_parrafo(
        ps[6],
        "Para el siguiente alumno (a): … con código … .",
        "{%endfor %}Para el siguiente alumno(a): {{ alumno_nombre }}, con código {{ alumno_codigo }}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_constancia_director_individual():
    origen = DOCS / "Constancias/2024/Plantilla - Director de Tesis .docx"
    destino = OUT / "constancia_director_individual.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "MCG/040/2024", "{{ constancia_numero }}")
    reemplazar_en_parrafo(
        ps[3],
        "DR. HÉCTOR JAVIER RENDÓN CONTRERAS",
        "{{ coordinador_nombre }}",
    )
    reemplazar_en_parrafo(
        ps[5],
        "Que al Dr. CHRISTIAN RENÉ ESCUDERO AYALA quien fungió como Director de Tesis del alumna CORDOBA CAMARGO ANA ALEJANDRA, con código 211281982, quien obtuvo el grado de Maestro en Ciencias en Geofísica el 28 de agosto de 2015, con la tesis titulada: “PATRONES SÍSMICOS EN LA ZONA DE CABO CORRIENTES, JALISCO”.",
        "Que {{ profesor_nombre }} fungió como {{ rol_texto }} de Tesis del(la) alumno(a) {{ alumno_nombre }}, con código {{ alumno_codigo }}{% if fecha_grado %}, quien obtuvo el grado el {{ fecha_grado }}{% endif %}{% if tesis_titulo %}, con la tesis titulada: “{{ tesis_titulo }}”{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_constancia_jurado():
    origen = DOCS / "Constancias/2024/Plantilla - Jurado Defensa de Tesis.docx"
    destino = OUT / "constancia_jurado.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "MCG/042/2024", "{{ constancia_numero }}")
    reemplazar_en_parrafo(ps[3], "Dr. HÉCTOR JAVIER RENDÓN CONTRERAS", "{{ coordinador_nombre }}")
    reemplazar_en_parrafo(
        ps[5],
        "Al Dra. FÁTIMA MACIEL CARRILLO GONZÁLEZ quien fungió como Presidenta del Jurado en el examen de grado de del alumno MARTINEZ ALVAREZ JUANA con codigo 216909572 quien sustentó su examen para obtener el grado de maestro; 10/11/2019, con la tesis titulada: “Zonificación de la vulnerabilidad por la actividad del volcán Cerobuco, Nayarit, México”.",
        "{{ a_profesor }} quien fungió como {{ cargo_texto }} del Jurado en el examen de grado del(la) alumno(a) {{ alumno_nombre }} con código {{ alumno_codigo }}{% if fecha_examen %} quien sustentó su examen el {{ fecha_examen }}{% endif %}{% if tesis_titulo %}, con la tesis titulada: “{{ tesis_titulo }}”{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_constancia_lector():
    origen = DOCS / "Constancias/2024/Plantilla - Lector.docx"
    destino = OUT / "constancia_lector.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "MCG/055/2024", "{{ constancia_numero }}")
    reemplazar_en_parrafo(ps[3], "DR. HÉCTOR JAVIER RENDÓN CONTRERAS", "{{ coordinador_nombre }}")
    reemplazar_en_parrafo(
        ps[5],
        "Que al Dr. MARIA CAROLINA RODRIGUEZ URIBE quien fungió como Lector de Tesis del (la) alumno (a) ALVAREZ SALAZAR FRANCISCO JAVIER, con código 221325856, con el tema de tesis titulada: “ANÁLISIS Y DETERMINACIÓN DE TENDENCIAS EN AUMENTO DEL NIVEL DEL MAR EN LAS ZONAS DE RIESGO EN LA ZONA URBANA DE  PUERTO VALLARTA ”.",
        "Que {{ profesor_nombre }} fungió como Lector de Tesis del(la) alumno(a) {{ alumno_nombre }}, con código {{ alumno_codigo }}{% if tesis_titulo %}, con el tema de tesis titulada: “{{ tesis_titulo }}”{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_constancia_evaluador_aspirantes():
    origen = DOCS / "Constancias/2025/000 Machote Constancias.docx"
    destino = OUT / "constancia_evaluador_aspirantes.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    for hp in d.sections[0].header.paragraphs:
        reemplazar_en_parrafo(hp, "Constancia: MCG/000/2025", "Constancia: {{ constancia_numero }}")
    reemplazar_en_parrafo(ps[2], "Dr. HÉCTOR JAVIER RENDÓN CONTRERAS", "{{ coordinador_nombre }}")
    reemplazar_en_parrafo(
        ps[4],
        "Al Mtro. ADÁN GÓMEZ HERNÁNDEZ por haber participado como Profesor Evaluador de los aspirantes a la Maestría en Ciencias de Geofísica para el ciclo escolar 2025 A, colaborando en la entrevista realizada a los aspirantes de acuerdo a la Convocatoria del ciclo mencionado, la cual se llevó a cabo el día 03 de diciembre del presente año, en el aula 001 del edificio de Estudios de Ciencia de la Tierra.",
        "{{ a_profesor }} por haber participado como Profesor(a) Evaluador(a) de los aspirantes a la Maestría en Ciencias en Geofísica para el ciclo escolar {{ ciclo }}, colaborando en la entrevista realizada a los aspirantes de acuerdo a la Convocatoria del ciclo mencionado{% if fecha_entrevista %}, la cual se llevó a cabo el día {{ fecha_entrevista }}{% endif %}{% if lugar %}, en {{ lugar }}{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_oficio_invitacion_jurado():
    origen = DOCS / "Oficios/2024/Formato 2024.docx"
    destino = OUT / "oficio_invitacion_jurado.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "CUCPV/MCG/000/2024", "{{ oficio_numero }}")
    reemplazar_en_parrafo(ps[1], "DR. - DRA", "{{ profesor_tratamiento_nombre }}")
    reemplazar_en_parrafo(
        ps[4],
        "Por este medio envió un cordial saludo y me permito informarle que la Junta Académica de la Maestría en Ciencias en Geofísica en el Acta MCG/12/2023 realizada el día 27 de octubre de 2023, se le invita a formar parte del JURADO en la defensa de tesis del alumno EDGAR ALAN MARTINEZ DIAZ con código 217895435 siendo el tema “PROSPECCIÓN MAGNÉTICA PARA LA EXPLORACIÓN GEOTÉRMICA EN EL ÁREA DEL VOLCÁN CEBORUCO, NAYARIT, MÉXICO”; el día jueves 16 de noviembre de 2023, a las 11:00 horas, en el Edificio de Ciencias de la Tierra, aula A001; en las Instalaciones del Centro Universitario de la Costa.",
        "Por este medio envío un cordial saludo y me permito informarle que la Junta Académica de la Maestría en Ciencias en Geofísica{% if acta_referencia %} en el {{ acta_referencia }}{% endif %}, se le invita a formar parte del JURADO como {{ cargo_texto }} en la defensa de tesis del(la) alumno(a) {{ alumno_nombre }} con código {{ alumno_codigo }}{% if tesis_titulo %} siendo el tema “{{ tesis_titulo }}”{% endif %}{% if fecha_examen %}; el día {{ fecha_examen }}{% endif %}{% if hora_examen %}, a las {{ hora_examen }} horas{% endif %}{% if lugar_examen %}, en {{ lugar_examen }}{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_oficio_asentamiento_creditos():
    origen = DOCS / "Oficios/2022/Oficio 2022- 006 MCG Asentamiendo creditos Trab campo Magdalena Rivas Ruiz.docx"
    destino = OUT / "oficio_asentamiento_creditos.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "Of. CUCPV/MCG/061/2022", "{{ oficio_numero }}")
    reemplazar_en_parrafo(ps[1], "Dra. Claudia Figueroa Ypiña", "{{ destinatario_nombre }}")
    reemplazar_en_parrafo(
        ps[5],
        "Por este medio solicito su apoyo y en atención a su correo, se realiza la corrección del oficio para que le sean asentados en Kardex los 10 diez créditos en la materia de PROYECTO DE INVESTIGACIÓN DEL POSGRADO EN GEOFÍSICA, con clave IF981 en el calendario 2021B a la estudiante María Magdalena Rivas Ruiz con código 214415947, por haber comprobado la realización de las horas correspondientes a trabajo de campo en la participación en proyectos de investigación, de acuerdo al acta MCG / 14 / 2021 de fecha 03 de diciembre del 2021.",
        "Por este medio solicito su apoyo para que le sean asentados en Kardex los {{ creditos }} créditos en la materia de {{ materia_nombre }}, con clave {{ materia_clave }} en el calendario {{ ciclo }} a{% if alumno_es_mujer %} la estudiante{% else %} el/la estudiante{% endif %} {{ alumno_nombre }} con código {{ alumno_codigo }}, por haber comprobado la realización de las horas correspondientes a trabajo de campo en la participación en proyectos de investigación{% if acta_referencia %}, de acuerdo al {{ acta_referencia }}{% endif %}.",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


def construir_oficio_permiso_municipio():
    origen = DOCS / "Oficios/2022/Oficio 2022- 074 MCG Solicitud registro Armeria.docx"
    destino = OUT / "oficio_permiso_municipio.docx"
    shutil.copy(origen, destino)
    d = docx.Document(destino)
    ps = _parrafos_con_texto(d)

    reemplazar_en_parrafo(ps[0], "Of: CUCPV/MCG/074/2022", "{{ oficio_numero }}")
    reemplazar_en_parrafo(ps[1], "Puerto Vallarta Jalisco a 15 de marzo del 2022", "Puerto Vallarta, Jalisco, a {{ fecha_larga }}")
    reemplazar_en_parrafo(ps[2], "Salvador Bueno Arceo", "{{ destinatario_nombre }}")
    reemplazar_en_parrafo(ps[3], "Director de la Unidad Municipal de Protección Civil", "{{ destinatario_cargo }}")
    reemplazar_en_parrafo(ps[4], "de Armería, Colima", "de {{ municipio }}")
    reemplazar_en_parrafo(
        ps[6],
        "Por medio de la presente, la Maestría en Ciencias en Geofísica en el Centro Universitario de la Costa de la Universidad de Guadalajara, con fines académicos, solicita registros históricos de eventos de inestabilidad de laderas (procesos de remoción en masas, deslizamientos de laderas, caídos de roca,  flujo de detritos) georreferenciados en formato digital (.shp, .kml o .dwg) y documentos descriptivos de los eventos y acervos fotográficos (en caso de existir) ocurridos en el municipio de Armería, con la finalidad de generar un inventario histórico de eventos de inestabilidad ocurridos en las cuencas costeras del sur de Nayarit, Jalisco y el norte de Colima, que sirva como insumo principal para la generación de modelo probabilístico de inestabilidad de laderas.",
        "{{ cuerpo_solicitud }}",
    )
    reemplazar_en_parrafo(
        ps[7],
        "Modelo que se realizara durante el periodo de 2021B-2023A en el trabajo de tesis titulado, “Cambios de uso de suelos promotores de inestabilidad de laderas en las cuencas que integran la costa de Jalisco y la Bahía de Banderas” a cargo del estudiante de la maestría en Geofísica, Jonatan Ernesto Rivera García, cuyos resultados serán entregados a las autoridades encargadas de gestionar el riesgo y el territorio en cada municipio, a fin de aportar al ordenamiento territorial y la gestión del riesgo, a través de la generación de planes y programas que ayuden a mitigar los efectos adversos de los procesos de inestabilidad y generar estrategias para evitar su ocurrencia, que siente las bases para la gestión de un sistema de alerta temprana en materia de deslizamientos de laderas.",
        "{% if cuerpo_parrafo2 %}{{ cuerpo_parrafo2 }}{% endif %}",
    )

    _reemplazar_cierre_estandar(d)
    d.save(destino)
    print("Generado:", destino)


if __name__ == "__main__":
    construir_comite_tutorial_alumno()
    construir_comite_tutorial_docente()
    construir_constancia_director_individual()
    construir_constancia_jurado()
    construir_constancia_lector()
    construir_constancia_evaluador_aspirantes()
    construir_oficio_invitacion_jurado()
    construir_oficio_asentamiento_creditos()
    construir_oficio_permiso_municipio()
