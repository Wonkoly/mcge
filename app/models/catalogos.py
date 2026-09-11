from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class StatusAlumno(Base):
    """Catálogo de códigos de status de alumno, tomados de la hoja `Estatus`
    del Excel. `confirmado=False` marca códigos cuyo significado exacto
    (B8, RD) sigue pendiente de confirmar con el usuario — ver
    MaestriaGeofisica - Excel Alumnos (Mapeo de Hojas) en el vault."""

    __tablename__ = "status_alumno"

    codigo: Mapped[str] = mapped_column(String(4), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60))
    categoria: Mapped[str] = mapped_column(String(20))  # activo|baja|proceso_titulacion|graduado|titulado|inactivo
    confirmado: Mapped[bool] = mapped_column(default=True)


class Lies(Base):
    """Líneas de Investigación e Incidencia Social — catálogo oficial de 2
    valores (cuc.udg.mx), compartido por Alumno y Profesor."""

    __tablename__ = "lies"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
