from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.alumno import Alumno


class Aspirante(Base, TimestampMixin):
    """Proceso real confirmado en actas: Evaluación Curricular 35% +
    Entrevista con profesores 30% + EXANI-III/inglés 35%, aprobación por
    Junta Académica ("recomendación de aceptación"). Al aceptarse se
    convierte en Alumno (alumno_id) sin recapturar datos."""

    __tablename__ = "aspirante"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    licenciatura: Mapped[Optional[str]] = mapped_column(String(150))
    universidad: Mapped[Optional[str]] = mapped_column(String(150))
    promedio: Mapped[Optional[float]] = mapped_column()
    correo: Mapped[Optional[str]] = mapped_column(String(150))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    fecha_registro: Mapped[Optional[date]] = mapped_column(Date)
    ciclo: Mapped[Optional[str]] = mapped_column(String(10))
    estado: Mapped[str] = mapped_column(String(30), default="Registrado")
    # Registrado | Documentacion incompleta | En evaluacion | Entrevista | Aceptado | No aceptado | Inscrito

    evaluacion_curricular: Mapped[Optional[float]] = mapped_column()  # 35%
    evaluacion_entrevista: Mapped[Optional[float]] = mapped_column()  # 30%
    evaluacion_conocimientos: Mapped[Optional[float]] = mapped_column()  # 35% (EXANI-III + inglés)

    observaciones: Mapped[Optional[str]] = mapped_column(String(1000))
    alumno_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alumno.id"))

    alumno: Mapped[Optional["Alumno"]] = relationship()
