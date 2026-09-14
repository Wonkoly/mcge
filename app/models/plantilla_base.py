from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class PlantillaBase(Base):
    """Molde en blanco (solo membrete — header/footer con logos, cuerpo
    vacío) subido una vez por categoría. Sobre este molde se componen los
    tipos de documento personalizados (ver TipoDocumentoPersonalizado) —
    el cuerpo se agrega como texto plano en la app, nunca se toca el
    header/footer, así el acomodo de imágenes nunca se desarma."""

    __tablename__ = "plantilla_base"

    categoria: Mapped[str] = mapped_column(String(20), primary_key=True)  # "oficio" | "constancia"
    archivo: Mapped[Optional[str]] = mapped_column(String(255))  # nombre dentro de directorio_plantillas_personalizadas()
