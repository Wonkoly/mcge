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
    aprueba...'.

    Desde Módulo 5 (Actas como fuente de cambios), un punto puede ser de
    un `tipo` estructurado (`direccion`, `comite_tutorial`) en vez de solo
    texto libre (`otro`, el comportamiento original): al guardar el Acta,
    un punto estructurado dispara el alta/cambio real en
    Direccion/ComiteTutorial (ver app/services/acta_service.py) — el
    coordinador ya no edita esas dos secciones desde el expediente del
    alumno, solo desde aquí. `direccion_id`/`comite_tutorial_id` guardan
    el registro que ya se creó, para no duplicar al reeditar el acta y
    para poder generar el oficio directamente desde el detalle del Acta.
    No modela tablas dinámicas de puntos "otro" dentro del documento del
    acta — eso se sigue escribiendo como texto libre en `resolutivo`."""

    __tablename__ = "punto_acta"

    id: Mapped[int] = mapped_column(primary_key=True)
    acta_id: Mapped[int] = mapped_column(ForeignKey("acta.id"))
    orden: Mapped[int] = mapped_column(Integer)
    tipo: Mapped[str] = mapped_column(String(30), default="otro")  # "direccion" | "comite_tutorial" | "otro"
    titulo: Mapped[str] = mapped_column(String(300))  # texto que va en el "ORDEN DEL DIA"
    resolutivo: Mapped[Optional[str]] = mapped_column(String(2000))  # texto que va en "RESOLUTIVOS"

    # Campos estructurados — solo aplican según `tipo`, ver docstring.
    alumno_id: Mapped[Optional[int]] = mapped_column(ForeignKey("alumno.id"))
    profesor_id: Mapped[Optional[int]] = mapped_column(ForeignKey("profesor.id"))  # tipo == "direccion"
    rol: Mapped[Optional[str]] = mapped_column(String(12))  # "Director" | "Codirector", tipo == "direccion"
    ciclo: Mapped[Optional[str]] = mapped_column(String(10))  # tipo == "comite_tutorial"

    # Registro real ya creado por este punto (se llena al guardar).
    direccion_id: Mapped[Optional[int]] = mapped_column(ForeignKey("direccion.id"))
    comite_tutorial_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comite_tutorial.id"))

    # tipo == "personalizado" (taller de plantillas): qué tipo de documento
    # es, y los valores de las variables que no vienen de Alumno/Profesor
    # (ej. destinatario_nombre/cargo) como JSON — alumno_id/profesor_id de
    # arriba se reutilizan tal cual si el cuerpo del documento los usa.
    tipo_documento_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tipo_documento_personalizado.id"))
    datos_json: Mapped[Optional[str]] = mapped_column(String(4000))

    acta: Mapped["Acta"] = relationship(back_populates="puntos")
    alumno = relationship("Alumno")
    profesor = relationship("Profesor")
    tipo_documento = relationship("TipoDocumentoPersonalizado")
    miembros: Mapped[list["PuntoActaMiembro"]] = relationship(cascade="all, delete-orphan")


class PuntoActaMiembro(Base):
    """Un profesor propuesto como miembro del comité tutorial dentro de un
    punto `tipo == "comite_tutorial"` — mismo patrón que `ComiteMiembro`,
    pero a nivel de punto de acta (todavía no es el `ComiteTutorial` real,
    eso se crea al guardar el acta)."""

    __tablename__ = "punto_acta_miembro"

    id: Mapped[int] = mapped_column(primary_key=True)
    punto_id: Mapped[int] = mapped_column(ForeignKey("punto_acta.id"))
    profesor_id: Mapped[int] = mapped_column(ForeignKey("profesor.id"))

    profesor = relationship("Profesor")
