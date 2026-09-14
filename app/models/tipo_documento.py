from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class TipoDocumentoPersonalizado(Base, TimestampMixin):
    """Un tipo de oficio/constancia definido por el coordinador desde el
    taller de plantillas (Documentos), sin tocar código. `cuerpo_texto` es
    lo que se redactó en el editor (texto plano, un renglón = un párrafo,
    con {{ variables }} literales insertadas desde el panel de datos
    disponibles). `plantilla_archivo` es el .docx ya compilado (molde de
    PlantillaBase + cuerpo_texto), listo para docxtpl. Solo los
    "confirmado" aparecen como opción al agregar un punto de Acta."""

    __tablename__ = "tipo_documento_personalizado"

    id: Mapped[int] = mapped_column(primary_key=True)
    clave: Mapped[str] = mapped_column(String(60), unique=True)
    etiqueta: Mapped[str] = mapped_column(String(150))
    descripcion: Mapped[Optional[str]] = mapped_column(String(500))
    categoria: Mapped[str] = mapped_column(String(20))  # "oficio" | "constancia"
    cuerpo_texto: Mapped[Optional[str]] = mapped_column(Text)
    plantilla_archivo: Mapped[Optional[str]] = mapped_column(String(255))
    estado: Mapped[str] = mapped_column(String(20), default="borrador")  # "borrador" | "confirmado"
