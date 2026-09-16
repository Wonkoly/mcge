"""Taller de plantillas — puerto de app/services/tipo_documento_service.py.
Compone cada tipo de documento personalizado sobre el molde en blanco
(PlantillaBase) de su categoría: el cuerpo redactado en el editor se agrega
como párrafos de texto plano, el header/footer del molde (membrete) nunca
se toca."""

import re
from datetime import date
from io import BytesIO

from django.conf import settings
from docx import Document
from docx.shared import Pt
from docxtpl import DocxTemplate

from core.auditoria import registrar
from documentos.contexto import ejemplos_variables
from documentos.models import PlantillaBase, TipoDocumentoPersonalizado

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


class MoldeFaltanteError(Exception):
    pass


def _slug(etiqueta: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", etiqueta.strip().lower()).strip("_") or "tipo"


def _ruta_plantillas():
    ruta = settings.PLANTILLAS_DIR
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def crear_tipo(*, etiqueta: str, categoria: str, descripcion: str = "", usuario: str = "usuario") -> TipoDocumentoPersonalizado:
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ValueError("La etiqueta es obligatoria")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria!r}")

    clave = _slug(etiqueta)
    if TipoDocumentoPersonalizado.objects.filter(clave=clave).exists():
        sufijo = 2
        while TipoDocumentoPersonalizado.objects.filter(clave=f"{clave}_{sufijo}").exists():
            sufijo += 1
        clave = f"{clave}_{sufijo}"

    tipo = TipoDocumentoPersonalizado.objects.create(
        clave=clave,
        etiqueta=etiqueta,
        descripcion=(descripcion or "").strip() or None,
        categoria=categoria,
        cuerpo_texto=CUERPO_INICIAL[categoria],
        estado="borrador",
    )
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="crear", valor_nuevo=etiqueta)
    return tipo


def actualizar_cuerpo(tipo: TipoDocumentoPersonalizado, cuerpo_texto: str, *, usuario: str = "usuario") -> None:
    tipo.cuerpo_texto = cuerpo_texto
    tipo.save(update_fields=["cuerpo_texto", "actualizado_en"])
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="modificar", campo="cuerpo_texto")


def actualizar_metadatos(tipo: TipoDocumentoPersonalizado, *, etiqueta: str, descripcion: str = "", usuario: str = "usuario") -> None:
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ValueError("La etiqueta es obligatoria")
    tipo.etiqueta = etiqueta
    tipo.descripcion = (descripcion or "").strip() or None
    tipo.save(update_fields=["etiqueta", "descripcion", "actualizado_en"])
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="modificar", campo="etiqueta/descripcion")


def eliminar_tipo(tipo: TipoDocumentoPersonalizado, *, usuario: str = "usuario") -> None:
    """Para "rehacer" uno mal armado desde cero — si ya estaba confirmado y
    en uso en algún punto de Acta, esos puntos quedan con `tipo_documento`
    nulo (el documento ya generado no se pierde, pero ya no se podrá
    regenerar desde ahí sin recrear el tipo)."""
    if tipo.plantilla_archivo:
        (_ruta_plantillas() / tipo.plantilla_archivo).unlink(missing_ok=True)
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="eliminar", valor_anterior=tipo.etiqueta)
    tipo.delete()


def compilar_plantilla(tipo: TipoDocumentoPersonalizado) -> BytesIO:
    """Junta el molde base de la categoría (header/footer, imágenes
    intactas) con el cuerpo redactado (texto plano, un renglón = un
    párrafo) — nunca toca el header/footer. El resultado sigue siendo una
    plantilla docxtpl (las {{ variables }} quedan literales): esto es lo
    que se guarda al confirmar, y también la base sobre la que
    generar_vista_previa() renderiza datos de ejemplo."""
    try:
        molde = PlantillaBase.objects.get(pk=tipo.categoria)
    except PlantillaBase.DoesNotExist:
        molde = None
    if molde is None or not molde.archivo:
        raise MoldeFaltanteError(
            f'No hay un molde base subido todavía para la categoría "{tipo.categoria}" — '
            "súbelo primero en Documentos."
        )

    ruta_molde = _ruta_plantillas() / molde.archivo
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


def generar_vista_previa(tipo: TipoDocumentoPersonalizado) -> BytesIO:
    """A diferencia del taller original (que dejaba las {{ }} literales),
    esto SÍ sustituye los datos — usa ejemplos_variables() para que la
    vista previa muestre cómo se vería el documento real, no solo el
    acomodo del membrete."""
    plantilla = compilar_plantilla(tipo)
    tpl = DocxTemplate(plantilla)
    tpl.render(ejemplos_variables())
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer


def confirmar_tipo(tipo: TipoDocumentoPersonalizado, *, usuario: str = "usuario") -> None:
    buffer = compilar_plantilla(tipo)
    nombre_archivo = f"{tipo.clave}.docx"
    (_ruta_plantillas() / nombre_archivo).write_bytes(buffer.getvalue())
    tipo.plantilla_archivo = nombre_archivo
    tipo.estado = "confirmado"
    tipo.save(update_fields=["plantilla_archivo", "estado", "actualizado_en"])
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="modificar", campo="estado", valor_nuevo="confirmado")


def guardar_molde_base(categoria: str, archivo, *, usuario: str = "usuario") -> None:
    # Sin auditoría aquí: HistorialCambio.entidad_id es entero y PlantillaBase
    # usa la categoría (texto) como llave — no encaja en ese esquema, y es
    # una acción de bajo riesgo y fácilmente reversible (se puede resubir).
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria!r}")
    if not archivo or not archivo.name.lower().endswith(".docx"):
        raise ValueError("El archivo debe ser un .docx")

    nombre_archivo = f"base_{categoria}.docx"
    ruta = _ruta_plantillas() / nombre_archivo
    with open(ruta, "wb") as destino:
        for chunk in archivo.chunks():
            destino.write(chunk)
    try:
        Document(str(ruta))  # valida que sea un .docx real y abrible
    except Exception as exc:
        ruta.unlink(missing_ok=True)
        raise ValueError("El archivo no se pudo abrir como .docx — ¿está corrupto?") from exc

    PlantillaBase.objects.update_or_create(categoria=categoria, defaults={"archivo": nombre_archivo})
