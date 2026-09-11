from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.alumno import Alumno
from app.models.profesor import Profesor
from app.models.acta import Acta


class Direccion(Base, TimestampMixin):
    """Relación alumno<->profesor como Director o Codirector de tesis.
    Con historial real: al cambiar de director, la fila anterior se cierra
    con `fecha_fin` (no se borra) y se crea una nueva — confirmado en actas
    reales (ej. caso Harlen Irene Cruz López, Acta 04/2022)."""

    __tablename__ = "direccion"

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumno.id"))
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))
    rol: Mapped[str] = mapped_column(String(12))  # "Director" | "Codirector"
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date)  # NULL = vigente
    acta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("acta.id"))

    alumno: Mapped["Alumno"] = relationship()
    profesor: Mapped["Profesor"] = relationship()
    acta: Mapped[Optional["Acta"]] = relationship()

    @property
    def vigente(self) -> bool:
        return self.fecha_fin is None
