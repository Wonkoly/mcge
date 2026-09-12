from sqlalchemy.orm import Session

from app.models import Configuracion
from app.utils.fechas import ciclo_actual

# Claves conocidas y su valor por defecto. Todo lo que antes se pedía en
# cada formulario (coordinador, ciclo) o vivía fijo en el código (ruta de
# respaldos) vive aquí en un solo lugar.
CLAVES_DEFAULT = {
    "coordinador_nombre": "Dr. Héctor Javier Rendón Contreras",
    "ciclo_escolar_actual": "",  # vacío = usar ciclo_actual() calculado por fecha
    "backup_carpeta_compartida": "",  # vacío = usar backups/ local
    "backup_retencion_dias": "30",
    "backup_intervalo_horas": "4",
}


def obtener(session: Session, clave: str) -> str:
    fila = session.get(Configuracion, clave)
    if fila is not None and fila.valor:
        return fila.valor
    return CLAVES_DEFAULT.get(clave, "")


def establecer(session: Session, clave: str, valor: str) -> None:
    fila = session.get(Configuracion, clave)
    if fila is None:
        fila = Configuracion(clave=clave, valor=valor)
        session.add(fila)
    else:
        fila.valor = valor


def obtener_todas(session: Session) -> dict:
    return {clave: obtener(session, clave) for clave in CLAVES_DEFAULT}


def ciclo_escolar_vigente(session: Session) -> str:
    """Ciclo a usar en toda la app (comité tutorial, panel, etc.) — si el
    coordinador fijó uno a mano en Settings se respeta, si no se calcula
    solo a partir de la fecha (ver app/utils/fechas.py)."""
    manual = obtener(session, "ciclo_escolar_actual")
    return manual or ciclo_actual()
