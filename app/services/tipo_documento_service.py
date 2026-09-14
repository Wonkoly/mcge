import re
from io import BytesIO

from docx import Document
from sqlalchemy.orm import Session

from app.documents.variables_disponibles import TODAS_LAS_VARIABLES, VARIABLES_ALUMNO, VARIABLES_PROFESOR
from app.models import PlantillaBase, TipoDocumentoPersonalizado
from app.utils.rutas import directorio_plantillas_personalizadas

CATEGORIAS_VALIDAS = ("oficio", "constancia")

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
        doc.add_paragraph(linea)

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
