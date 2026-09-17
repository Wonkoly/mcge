"""Plantillas personalizadas — se preparan enteras en Word (membrete +
cuerpo + {{ variables }}) y se suben ya terminadas; la app no las compone.
Puerto simplificado de app/services/tipo_documento_service.py: se quitó el
editor de cuerpo en el navegador (ver kind-napping-grove.md original) a
pedido del coordinador — "poco útil y funcional" en la práctica, porque
edita más rápido y con más control en Word directamente."""

import re

from django.conf import settings
from docx import Document
from docxtpl import DocxTemplate
from io import BytesIO

from core.auditoria import registrar
from documentos.contexto import ejemplos_variables
from documentos.models import PlantillaBase, TipoDocumentoPersonalizado

CATEGORIAS_VALIDAS = ("oficio", "constancia")


class PlantillaFaltanteError(Exception):
    pass


def _slug(etiqueta: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", etiqueta.strip().lower()).strip("_") or "tipo"


def ruta_plantillas():
    ruta = settings.PLANTILLAS_DIR
    ruta.mkdir(parents=True, exist_ok=True)
    return ruta


def _guardar_archivo_valido(archivo, ruta) -> None:
    if not archivo or not archivo.name.lower().endswith(".docx"):
        raise ValueError("El archivo debe ser un .docx")
    with open(ruta, "wb") as destino:
        for chunk in archivo.chunks():
            destino.write(chunk)
    try:
        Document(str(ruta))  # valida que sea un .docx real y abrible
    except Exception as exc:
        ruta.unlink(missing_ok=True)
        raise ValueError("El archivo no se pudo abrir como .docx — ¿está corrupto?") from exc


def crear_tipo(*, etiqueta: str, categoria: str, descripcion: str = "", archivo, usuario: str = "usuario") -> TipoDocumentoPersonalizado:
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

    nombre_archivo = f"{clave}.docx"
    _guardar_archivo_valido(archivo, ruta_plantillas() / nombre_archivo)

    tipo = TipoDocumentoPersonalizado.objects.create(
        clave=clave,
        etiqueta=etiqueta,
        descripcion=(descripcion or "").strip() or None,
        categoria=categoria,
        plantilla_archivo=nombre_archivo,
        estado="confirmado",
    )
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="crear", valor_nuevo=etiqueta)
    return tipo


def reemplazar_plantilla(tipo: TipoDocumentoPersonalizado, archivo, *, usuario: str = "usuario") -> None:
    """El coordinador corrigió algo en Word y vuelve a subir el mismo tipo
    — se sobreescribe el .docx, se conserva la clave/etiqueta."""
    nombre_archivo = tipo.plantilla_archivo or f"{tipo.clave}.docx"
    _guardar_archivo_valido(archivo, ruta_plantillas() / nombre_archivo)
    tipo.plantilla_archivo = nombre_archivo
    tipo.estado = "confirmado"
    tipo.save(update_fields=["plantilla_archivo", "estado", "actualizado_en"])
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="modificar", campo="plantilla_archivo")


def actualizar_metadatos(tipo: TipoDocumentoPersonalizado, *, etiqueta: str, descripcion: str = "", usuario: str = "usuario") -> None:
    etiqueta = (etiqueta or "").strip()
    if not etiqueta:
        raise ValueError("La etiqueta es obligatoria")
    tipo.etiqueta = etiqueta
    tipo.descripcion = (descripcion or "").strip() or None
    tipo.save(update_fields=["etiqueta", "descripcion", "actualizado_en"])
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="modificar", campo="etiqueta/descripcion")


def eliminar_tipo(tipo: TipoDocumentoPersonalizado, *, usuario: str = "usuario") -> None:
    """Si ya estaba en uso en algún punto de Acta, esos puntos quedan con
    `tipo_documento` nulo (el documento ya generado no se pierde, pero ya
    no se podrá regenerar desde ahí sin recrear el tipo)."""
    if tipo.plantilla_archivo:
        (ruta_plantillas() / tipo.plantilla_archivo).unlink(missing_ok=True)
    registrar(usuario=usuario, entidad="TipoDocumentoPersonalizado", entidad_id=tipo.id, accion="eliminar", valor_anterior=tipo.etiqueta)
    tipo.delete()


def generar_vista_previa(tipo: TipoDocumentoPersonalizado) -> BytesIO:
    """Render real (no de mentiras) de la plantilla ya subida, con datos
    de ejemplo — para que el coordinador vea si sus {{ variables }}
    escritas a mano en Word coinciden con el catálogo real."""
    if not tipo.plantilla_archivo:
        raise PlantillaFaltanteError("Todavía no se ha subido ninguna plantilla para este tipo.")
    tpl = DocxTemplate(str(ruta_plantillas() / tipo.plantilla_archivo))
    tpl.render(ejemplos_variables())
    buffer = BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer


def guardar_molde_base(categoria: str, archivo, *, usuario: str = "usuario") -> None:
    # Sin auditoría aquí: HistorialCambio.entidad_id es entero y PlantillaBase
    # usa la categoría (texto) como llave — no encaja en ese esquema, y es
    # una acción de bajo riesgo y fácilmente reversible (se puede resubir).
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValueError(f"Categoría inválida: {categoria!r}")
    if not archivo or not archivo.name.lower().endswith(".docx"):
        raise ValueError("El archivo debe ser un .docx")

    nombre_archivo = f"base_{categoria}.docx"
    ruta = ruta_plantillas() / nombre_archivo
    with open(ruta, "wb") as destino:
        for chunk in archivo.chunks():
            destino.write(chunk)
    try:
        Document(str(ruta))  # valida que sea un .docx real y abrible
    except Exception as exc:
        ruta.unlink(missing_ok=True)
        raise ValueError("El archivo no se pudo abrir como .docx — ¿está corrupto?") from exc

    PlantillaBase.objects.update_or_create(categoria=categoria, defaults={"archivo": nombre_archivo})
