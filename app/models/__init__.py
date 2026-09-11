from app.models.base import Base
from app.models.catalogos import StatusAlumno, Lies
from app.models.profesor import Profesor, ProfesorAlias
from app.models.alumno import Alumno
from app.models.acta import Acta
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
    "Profesor",
    "ProfesorAlias",
    "Alumno",
    "Acta",
    "Direccion",
    "ComiteTutorial",
    "ComiteMiembro",
    "Lector",
    "Sinodal",
    "Aspirante",
    "HistorialCambio",
]
