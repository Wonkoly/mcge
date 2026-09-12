from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.alumno import Alumno
from app.models.profesor import Profesor
from app.models.acta import Acta


class Sinodal(Base, TimestampMixin):
    """Jurado de examen de grado: Presidente/Secretario/Vocal — sí tiene
    cargo diferenciado (a diferencia del comité tutorial). Se asigna en
    Acta al aprobar fecha/hora de examen."""

    __tablename__ = "sinodal"

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumno.id"))
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))
    cargo: Mapped[Optional[str]] = mapped_column(String(15))  # Presidente | Secretario | Vocal
    fecha_examen: Mapped[Optional[date]] = mapped_column(Date)
    hora_examen: Mapped[Optional[str]] = mapped_column(String(10))
    lugar_examen: Mapped[Optional[str]] = mapped_column(String(200))
    acta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("acta.id"))

    alumno: Mapped["Alumno"] = relationship()
    profesor: Mapped["Profesor"] = relationship()
    acta: Mapped[Optional["Acta"]] = relationship()
