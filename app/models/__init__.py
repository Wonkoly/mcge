from app.models.base import Base
from app.models.catalogos import StatusAlumno, Lies
from app.models.configuracion import Configuracion
from app.models.folio import FolioSecuencia
from app.models.profesor import Profesor, ProfesorAlias
from app.models.alumno import Alumno
from app.models.acta import Acta, PuntoActa, PuntoActaMiembro
from app.models.direccion import Direccion
from app.models.comite import ComiteTutorial, ComiteMiembro
from app.models.lector import Lector
from app.models.sinodal import Sinodal
from app.models.aspirante import Aspirante
from app.models.auditoria import HistorialCambio

__all__ = [
    "Base",
    "StatusAlumno",
    "Lies",
    "Configuracion",
    "FolioSecuencia",
    "Profesor",
    "ProfesorAlias",
    "Alumno",
    "Acta",
    "PuntoActa",
    "PuntoActaMiembro",
    "Direccion",
    "ComiteTutorial",
    "ComiteMiembro",
    "Lector",
    "Sinodal",
    "Aspirante",
    "HistorialCambio",
]
