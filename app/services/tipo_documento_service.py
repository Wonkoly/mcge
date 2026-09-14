import re
from io import BytesIO

from docx import Document
from docx.shared import Pt
from sqlalchemy.orm import Session

from app.documents.variables_disponibles import TODAS_LAS_VARIABLES, VARIABLES_ALUMNO, VARIABLES_PROFESOR
from app.models import Acta, Alumno, PlantillaBase, Profesor, TipoDocumentoPersonalizado
from app.utils.rutas import directorio_plantillas_personalizadas

CATEGORIAS_VALIDAS = ("oficio", "constancia")
FUENTE_DOCUMENTOS = "Arial"

CUERPO_INICIAL = {
    "oficio": (
        "{{ numero_documento }}\n"
        "\n"
        "{{ destinatario_nombre }}\n"
        "{{ destinatario_cargo }}\n"
        "P R E S E N T E\n"
        "\n"
        "\n"
        "\n"
        "Atentamente\n"
        "\n"
        "{{ coordinador_nombre }}\n"
        "Puerto Vallarta, Jalisco, a {{ fecha_larga }}"
    ),
    "constancia": (
        "{{ numero_documento }}\n"
        "\n"
        "A QUIEN CORRESPONDA\n"
        "\n"
        "\n"
        "\n"
        "Atentamente\n"
        "\n"
        "{{ coordinador_nombre }}\n"
        "Puerto Vallarta, Jalisco, a {{ fecha_larga }}"
    ),
}

_PATRON_VARIABLE = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class ClaveDuplicadaError(Exception):
    pass


class MoldeFaltanteError(Exception):
    pass


def _slug(etiqueta: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "_", etiqueta.strip().lower()).strip("_") or "tipo"
    return base


def crear_tipo(session: Session, *, etiqueta: str, categoria: str, descripcion: str = "") -> TipoDocumentoPersonalizado:
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ValueError("La etiqueta es obligatoria")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria!r}")

    clave = _slug(etiqueta)
    if session.query(TipoDocumentoPersonalizado).filter_by(clave=clave).first():
        sufijo = 2
        while session.query(TipoDocumentoPersonalizado).filter_by(clave=f"{clave}_{sufijo}").first():
            sufijo += 1
        clave = f"{clave}_{sufijo}"

    tipo = TipoDocumentoPersonalizado(
        clave=clave,
        etiqueta=etiqueta,
        descripcion=(descripcion or "").strip() or None,
        categoria=categoria,
        cuerpo_texto=CUERPO_INICIAL[categoria],
        estado="borrador",
    )
    session.add(tipo)
    session.flush()
    return tipo


def actualizar_cuerpo(session: Session, tipo: TipoDocumentoPersonalizado, cuerpo_texto: str) -> None:
    tipo.cuerpo_texto = cuerpo_texto


def actualizar_metadatos(tipo: TipoDocumentoPersonalizado, *, etiqueta: str, descripcion: str = "") -> None:
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ValueError("La etiqueta es obligatoria")
    tipo.etiqueta = etiqueta
    tipo.descripcion = (descripcion or "").strip() or None


def eliminar_tipo(session: Session, tipo: TipoDocumentoPersonalizado) -> None:
    """Para "rehacer" uno mal armado desde cero — si ya estaba confirmado y
    en uso en algún punto de Acta, esos puntos quedan con `tipo_documento`
    nulo (el documento ya generado no se pierde, pero ya no se podrá
    regenerar desde ahí sin recrear el tipo)."""
    if tipo.plantilla_archivo:
        ruta = directorio_plantillas_personalizadas() / tipo.plantilla_archivo
        ruta.unlink(missing_ok=True)
    session.delete(tipo)


def ejemplos_variables(session: Session) -> dict[str, str]:
    """Un valor de ejemplo real (no inventado) por variable, para que el
    buscador del taller muestre cómo se ve cada dato antes de insertarlo.
    Toma el primer alumno/profesor/acta que haya en la base — si todavía
    no hay datos, la variable simplemente no aparece con ejemplo."""
    ejemplos: dict[str, str] = {}

    alumno = session.query(Alumno).order_by(Alumno.id).first()
    if alumno:
        ejemplos.update(
            {
                "alumno_nombre": alumno.nombre,
                "alumno_codigo": alumno.codigo,
                "alumno_ciclo_ingreso": alumno.ciclo_ingreso or "",
                "alumno_tesis_titulo": alumno.tesis_titulo or "",
                "alumno_dictamen": alumno.dictamen or "",
                "alumno_correo_institucional": alumno.correo_institucional or "",
                "alumno_correo_personal": alumno.correo_personal or "",
                "alumno_telefono": alumno.telefono or "",
                "alumno_creditos_acumulados": str(alumno.creditos_acumulados or ""),
                "alumno_creditos_faltantes": str(alumno.creditos_faltantes or ""),
                "alumno_promedio": str(alumno.promedio or ""),
                "alumno_cvu": alumno.cvu or "",
                "alumno_lies": alumno.lies.nombre if alumno.lies else "",
                "alumno_maximo_ciclo": alumno.maximo_ciclo or "",
            }
        )

    profesor = session.query(Profesor).filter(Profesor.tratamiento.isnot(None)).order_by(Profesor.id).first()
    if profesor:
        from app.documents.generador import _nombre_con_tratamiento, formatear_nombre

        ejemplos.update(
            {
                "profesor_nombre": _nombre_con_tratamiento(profesor),
                "profesor_nombre_simple": formatear_nombre(profesor.nombre),
                "profesor_correo": profesor.correo or "",
                "profesor_telefono": profesor.telefono or "",
                "profesor_cvu": profesor.cvu or "",
                "profesor_linea_investigacion": profesor.linea_investigacion or "",
                "profesor_lies": profesor.lies.nombre if profesor.lies else "",
                "profesor_sni": profesor.sni or "",
                "profesor_centro_universitario": profesor.centro_universitario or "",
            }
        )

    acta = session.query(Acta).order_by(Acta.id.desc()).first()
    if acta:
        ejemplos.update(
            {
                "acta_numero": acta.numero,
                "acta_fecha": str(acta.fecha or ""),
                "acta_lugar": acta.lugar or "",
                "acta_sede": acta.sede or "",
                "acta_hora_inicio": acta.hora_inicio or "",
                "acta_hora_fin": acta.hora_fin or "",
                "acta_asistentes": acta.asistentes or "",
            }
        )

    ejemplos.update(
        {
            "numero_documento": "CUCPV/MCG/001/2026",
            "fecha_larga": "14 de septiembre de 2026",
            "coordinador_nombre": "Dr. Héctor Javier Rendón Contreras",
            "lema_ciclo": "",
        }
    )
    return ejemplos


def variables_libres(cuerpo_texto: str) -> list[str]:
    """Variables que aparecen en el cuerpo pero no son del catálogo fijo
    (alumno/profesor/generales) — ej. destinatario_nombre. Se piden como
    campo de texto libre al generar un documento real."""
    encontradas = dict.fromkeys(_PATRON_VARIABLE.findall(cuerpo_texto or ""))  # preserva orden, sin duplicados
    return [v for v in encontradas if v not in TODAS_LAS_VARIABLES]


def necesita_alumno(cuerpo_texto: str) -> bool:
    return any(v in VARIABLES_ALUMNO for v in _PATRON_VARIABLE.findall(cuerpo_texto or ""))


def necesita_profesor(cuerpo_texto: str) -> bool:
    return any(v in VARIABLES_PROFESOR for v in _PATRON_VARIABLE.findall(cuerpo_texto or ""))


def necesita_profesores_lista(cuerpo_texto: str) -> bool:
    """`profesores_lista` no es un {{ variable }} plano — se usa dentro de
    un bucle ({%for p in profesores_lista%}{{ p.nombre }}{%endfor%}) para
    formatos que enlistan a varios profesores (ej. un oficio dirigido a
    todo un comité). Se detecta por texto simple, no con el regex de
    {{ }} — ver ejemplo ya probado en oficio_comite_tutorial_alumno.docx."""
    return "profesores_lista" in (cuerpo_texto or "")


def compilar_plantilla(session: Session, tipo: TipoDocumentoPersonalizado) -> BytesIO:
    """Junta el molde base de la categoría (header/footer, imágenes
    intactas) con el cuerpo redactado (texto plano, un renglón = un
    párrafo) — nunca toca el header/footer, así nunca hay riesgo de
    desacomodar el membrete."""
    molde = session.get(PlantillaBase, tipo.categoria)
    if molde is None or not molde.archivo:
        raise MoldeFaltanteError(
            f'No hay un molde base subido todavía para la categoría "{tipo.categoria}" — '
            "súbelo primero en Documentos."
        )

    ruta_molde = directorio_plantillas_personalizadas() / molde.archivo
    doc = Document(str(ruta_molde))
    for linea in (tipo.cuerpo_texto or "").split("\n"):
        p = doc.add_paragraph()
        run = p.add_run(linea)
        # Arial fijo en el cuerpo agregado, sin importar qué fuente traiga el
        # molde por defecto — así el texto compuesto en el taller siempre
        # sale con la tipografía institucional pedida.
        run.font.name = FUENTE_DOCUMENTOS
        run.font.size = Pt(11)

    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def confirmar_plantilla(session: Session, tipo: TipoDocumentoPersonalizado) -> None:
    buffer = compilar_plantilla(session, tipo)
    nombre_archivo = f"{tipo.clave}.docx"
    ruta = directorio_plantillas_personalizadas() / nombre_archivo
    ruta.write_bytes(buffer.getvalue())
    tipo.plantilla_archivo = nombre_archivo
    tipo.estado = "confirmado"


def guardar_molde_base(session: Session, categoria: str, file_storage) -> None:
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria!r}")
    if not file_storage or not file_storage.filename.lower().endswith(".docx"):
        raise ValueError("El archivo debe ser un .docx")

    nombre_archivo = f"base_{categoria}.docx"
    ruta = directorio_plantillas_personalizadas() / nombre_archivo
    file_storage.save(str(ruta))
    try:
        Document(str(ruta))  # valida que sea un .docx real y abrible
    except Exception as exc:
        ruta.unlink(missing_ok=True)
        raise ValueError("El archivo no se pudo abrir como .docx — ¿está corrupto?") from exc

    molde = session.get(PlantillaBase, categoria)
    if molde is None:
        molde = PlantillaBase(categoria=categoria)
        session.add(molde)
    molde.archivo = nombre_archivo
