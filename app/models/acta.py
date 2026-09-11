from datetime import date
from typing import Optional

from sqlalchemy import Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class Acta(Base, TimestampMixin):
    """Acta de Junta Académica — fuente de verdad de casi todo lo demás
    (aceptación de aspirante, comité tutorial, dirección/codirección,
    lectores, sinodales). Ver MaestriaGeofisica - Actas, Oficios y
    Constancias (Procesos) en el vault."""

    __tablename__ = "acta"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True)  # ej. "MCG/14/2022"
    fecha: Mapped[Optional[date]] = mapped_column(Date)
    anio: Mapped[int] = mapped_column()
    resumen: Mapped[Optional[str]] = mapped_column(String(500))
