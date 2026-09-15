from core.fechas import ciclo_actual
from core.models import Configuracion

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


def obtener(clave: str) -> str:
    fila = Configuracion.objects.filter(pk=clave).first()
    if fila is not None and fila.valor:
        return fila.valor
    return CLAVES_DEFAULT.get(clave, "")


def establecer(clave: str, valor: str) -> None:
    Configuracion.objects.update_or_create(clave=clave, defaults={"valor": valor})


def obtener_todas() -> dict:
    return {clave: obtener(clave) for clave in CLAVES_DEFAULT}


def ciclo_escolar_vigente() -> str:
    """Ciclo a usar en toda la app (comité tutorial, panel, etc.) — si el
    coordinador fijó uno a mano en Settings se respeta, si no se calcula
    solo a partir de la fecha (ver core/fechas.py)."""
    manual = obtener("ciclo_escolar_actual")
    return manual or ciclo_actual()
