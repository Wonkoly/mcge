from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.alumno import Alumno
from app.models.profesor import Profesor
from app.models.acta import Acta


class Lector(Base, TimestampMixin):
    """3 personas por tesis, propuestas por el director y aprobadas en
    Acta, certifican que el documento de tesis está terminado — requisito
    para cargar los 10 créditos de "Trabajo de Tesis". Distinto de comité
    tutorial y de sinodales."""

    __tablename__ = "lector"

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumno.id"))
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))
    fecha: Mapped[Optional[date]] = mapped_column(Date)
    acta_id: Mapped[Optional[int]] = mapped_column(ForeignKey("acta.id"))

    alumno: Mapped["Alumno"] = relationship()
    profesor: Mapped["Profesor"] = relationship()
    acta: Mapped[Optional["Acta"]] = relationship()
