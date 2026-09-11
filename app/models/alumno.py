from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.catalogos import Lies, StatusAlumno


class Alumno(Base, TimestampMixin):
    __tablename__ = "alumno"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True)
    nombre: Mapped[str] = mapped_column(String(150))
    ciclo_ingreso: Mapped[Optional[str]] = mapped_column(String(10))
    status_codigo: Mapped[Optional[str]] = mapped_column(ForeignKey("status_alumno.codigo"))
    creditos_acumulados: Mapped[Optional[int]] = mapped_column()
    creditos_faltantes: Mapped[Optional[int]] = mapped_column()
    promedio: Mapped[Optional[float]] = mapped_column()
    ciclos_cursados: Mapped[Optional[int]] = mapped_column()
    maximo_ciclo: Mapped[Optional[str]] = mapped_column(String(10))
    dictamen: Mapped[Optional[str]] = mapped_column(String(10))  # MIGE / MIGF — significado exacto sin confirmar
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    correo_personal: Mapped[Optional[str]] = mapped_column(String(150))
    correo_institucional: Mapped[Optional[str]] = mapped_column(String(150))
    fecha_nacimiento: Mapped[Optional[date]] = mapped_column(Date)
    retribucion_social: Mapped[Optional[str]] = mapped_column(String(150))
    cvu: Mapped[Optional[str]] = mapped_column(String(20))
    fecha_grado: Mapped[Optional[date]] = mapped_column(Date)
    lies_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lies.id"))

    tesis_titulo: Mapped[Optional[str]] = mapped_column(String(400))
    protocolo: Mapped[Optional[str]] = mapped_column(String(1000))
    impacto_cientifico: Mapped[Optional[str]] = mapped_column(String(1000))
    impacto_social: Mapped[Optional[str]] = mapped_column(String(1000))
    solucion_problemas: Mapped[Optional[str]] = mapped_column(String(1000))
    estrategias_acceso: Mapped[Optional[str]] = mapped_column(String(1000))

    observaciones: Mapped[Optional[str]] = mapped_column(String(1000))

    status: Mapped[Optional["StatusAlumno"]] = relationship()
    lies: Mapped[Optional["Lies"]] = relationship()
