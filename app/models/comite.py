from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.alumno import Alumno
from app.models.acta import Acta
from app.models.profesor import Profesor


class ComiteTutorial(Base, TimestampMixin):
    """Comité tutorial de un alumno para un ciclo. Confirmado en actas
    reales: 2-3 profesores por alumno, sin cargo diferenciado (lista plana
    de miembros vía ComiteMiembro), reasignable por ciclo — por eso lleva
    fecha_inicio/fecha_fin igual que Dirección, no es un valor único fijo."""

    __tablename__ = "comite_tutorial"

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumno.id"))
    ciclo: Mapped[Optional[str]] = mapped_column(String(10))
    fecha_inicio: Mapped[Optional[date]] = mapped_column(Date)
    fecha_fin: Mapped[Optional[date]] = mapped_column(Date)  # NULL = vigente
    acta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("acta.id"))

    alumno: Mapped["Alumno"] = relationship()
    acta: Mapped[Optional["Acta"]] = relationship()
    miembros: Mapped[list["ComiteMiembro"]] = relationship(
        back_populates="comite", cascade="all, delete-orphan"
    )

    @property
    def vigente(self) -> bool:
        return self.fecha_fin is None


class ComiteMiembro(Base):
    """Un profesor dentro de un ComiteTutorial. Sin columna `cargo`: los
    datos reales de las actas no distinguen roles dentro del comité
    tutorial (a diferencia de Sinodal, que sí tiene Presidente/Secretario/
    Vocal)."""

    __tablename__ = "comite_miembro"

    id: Mapped[int] = mapped_column(primary_key=True)
    comite_id: Mapped[int] = mapped_column(ForeignKey("comite_tutorial.id"))
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))

    comite: Mapped["ComiteTutorial"] = relationship(back_populates="miembros")
    profesor: Mapped["Profesor"] = relationship()
