from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.catalogos import Lies

TRATAMIENTOS = ["Doctor", "Doctora", "Maestro", "Maestra"]

PREFIJO_POR_TRATAMIENTO = {
    "Doctor": "Dr.",
    "Doctora": "Dra.",
    "Maestro": "Mtro.",
    "Maestra": "Mtra.",
}


class Profesor(Base, TimestampMixin):
    __tablename__ = "profesor"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150), unique=True)
    tratamiento: Mapped[Optional[str]] = mapped_column(String(10))  # catálogo cerrado: TRATAMIENTOS — para el prefijo en documentos
    grado: Mapped[Optional[str]] = mapped_column(String(150))  # disciplina/grado en texto libre, informativo — NO entra a los documentos
    centro_universitario: Mapped[Optional[str]] = mapped_column(String(150), default="Centro Universitario de la Costa")
    cvu: Mapped[Optional[str]] = mapped_column(String(20))
    correo: Mapped[Optional[str]] = mapped_column(String(150))
    telefono: Mapped[Optional[str]] = mapped_column(String(30))
    nucleo_academico: Mapped[bool] = mapped_column(default=False)
    sni: Mapped[Optional[str]] = mapped_column(String(10))
    dedicacion: Mapped[Optional[str]] = mapped_column(String(60))
    linea_investigacion: Mapped[Optional[str]] = mapped_column(String(200))
    lies_id: Mapped[Optional[int]] = mapped_column(ForeignKey("lies.id"))
    activo: Mapped[bool] = mapped_column(default=True)
    observaciones: Mapped[Optional[str]] = mapped_column(String(500))

    lies: Mapped[Optional["Lies"]] = relationship()

    @property
    def prefijo(self) -> str:
        return PREFIJO_POR_TRATAMIENTO.get(self.tratamiento or "", "")


class ProfesorAlias(Base):
    """Variantes de nombre encontradas en el Excel/actas para un mismo
    profesor (typos, acentos, prefijos Dr./Dra./Mtro.) — permite reconciliar
    texto libre histórico sin perder la referencia a qué persona real es."""

    __tablename__ = "profesor_alias"

    id: Mapped[int] = mapped_column(primary_key=True)
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))
    alias: Mapped[str] = mapped_column(String(150))

    profesor: Mapped["Profesor"] = relationship()
