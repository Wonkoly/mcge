from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Acta(Base, TimestampMixin):
    """Acta de Junta Académica — fuente de verdad de casi todo lo demás
    (aceptación de aspirante, comité tutorial, dirección/codirección,
    lectores, sinodales). Ver MaestriaGeofisica - Actas, Oficios y
    Constancias (Procesos) en el vault. Los campos hora/lugar/sede/
    asistentes existen para poder generar el documento del acta con el
    mismo texto introductorio que usan las actas reales."""

    __tablename__ = "acta"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(30), unique=True)  # ej. "MCG/14/2022"
    fecha: Mapped[Optional[date]] = mapped_column(Date)
    anio: Mapped[int] = mapped_column()
    resumen: Mapped[Optional[str]] = mapped_column(String(500))

    hora_inicio: Mapped[Optional[str]] = mapped_column(String(10))
    hora_fin: Mapped[Optional[str]] = mapped_column(String(10))
    lugar: Mapped[Optional[str]] = mapped_column(String(150), default="Puerto Vallarta, Jalisco")
    sede: Mapped[Optional[str]] = mapped_column(String(250))  # ej. "la biblioteca del edificio Centro Estudios de la Tierra"
    asistentes: Mapped[Optional[str]] = mapped_column(String(1000))

    puntos: Mapped[list["PuntoActa"]] = relationship(
        back_populates="acta", cascade="all, delete-orphan", order_by="PuntoActa.orden"
    )


class PuntoActa(Base):
    """Un punto del orden del día de un Acta, con su resolutivo. Ver
    ejemplo real: 'Como punto número cuatro del orden del día... se
    aprueba...'. No modela tablas dinámicas dentro del punto (ej. la lista
    de comités tutoriales asignados) — eso se escribe como texto libre en
    `resolutivo` por ahora."""

    __tablename__ = "punto_acta"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(ForeignKey("acta.id"))
    orden: Mapped[int] = mapped_column(Integer)
    titulo: Mapped[str] = mapped_column(String(300))  # texto que va en el "ORDEN DEL DIA"
    resolutivo: Mapped[Optional[str]] = mapped_column(String(2000))  # texto que va en "RESOLUTIVOS"

    acta: Mapped["Acta"] = relationship(back_populates="puntos")
