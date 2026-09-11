from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class HistorialCambio(Base):
    __tablename__ = "historial_cambio"

    id: Mapped[int] = mapped_column(primary_key=True)
    usuario: Mapped[Optional[str]] = mapped_column(String(80))
    fecha: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    entidad: Mapped[str] = mapped_column(String(50))
    entidad_id: Mapped[int] = mapped_column()
    accion: Mapped[str] = mapped_column(String(20))  # crear | modificar | eliminar
    campo: Mapped[Optional[str]] = mapped_column(String(50))
    valor_anterior: Mapped[Optional[str]] = mapped_column(String(500))
    valor_nuevo: Mapped[Optional[str]] = mapped_column(String(500))
