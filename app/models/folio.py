from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class FolioSecuencia(Base):
    """Contador de folios por tipo de documento y año, con incremento
    atómico (ver app/services/folio_service.py) para que dos PCs pidiendo
    folio casi al mismo tiempo nunca reciban el mismo número. La secuencia
    reinicia sola cada año porque la clave incluye `anio`."""

    __tablename__ = "folio_secuencia"

    tipo_documento: Mapped[str] = mapped_column(String(60), primary_key=True)
    anio: Mapped[int] = mapped_column(Integer, primary_key=True)
    ultimo_folio: Mapped[int] = mapped_column(Integer, default=0)
