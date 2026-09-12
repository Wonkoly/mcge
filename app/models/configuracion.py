from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Configuracion(Base):
    """Ajustes de la app en un solo lugar (no repartidos en el código):
    ruta de respaldos, ciclo escolar actual, coordinador por defecto, etc.
    Clave/valor simple — ver app/services/configuracion_service.py para las
    claves conocidas y sus valores por defecto."""

    __tablename__ = "configuracion"

    clave: Mapped[str] = mapped_column(String(60), primary_key=True)
    valor: Mapped[Optional[str]] = mapped_column(String(500))
