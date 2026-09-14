import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path

from app.database.session import DB_PATH
from app.utils.rutas import directorio_datos, directorio_plantillas_personalizadas

BACKUPS_DIR_LOCAL = directorio_datos() / "backups"

PREFIJO = "maestria_"


def carpeta_respaldos() -> Path:
    """Carpeta compartida configurada en Settings, o `backups/` local si no
    se ha configurado ninguna. Los respaldos SÍ pueden vivir en red (son
    copias de solo lectura) — la base de datos viva, no."""
    from app.database.session import SessionLocal
    from app.services.configuracion_service import obtener

    session = SessionLocal()
    try:
        ruta_configurada = obtener(session, "backup_carpeta_compartida")
    finally:
        session.close()

    carpeta = Path(ruta_configurada) if ruta_configurada else BACKUPS_DIR_LOCAL
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def crear_respaldo() -> Path | None:
    """VACUUM INTO en vez de copiar el archivo a mano — una copia hecha con
    shutil.copy mientras alguien escribe puede quedar corrupta; VACUUM INTO
    siempre produce un archivo consistente aunque haya actividad."""
    if not DB_PATH.exists():
        return None

    sello = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino = carpeta_respaldos() / f"{PREFIJO}{sello}.db"
    con = sqlite3.connect(str(DB_PATH))
    try:
        con.execute("VACUUM INTO ?", [str(destino)])
    finally:
        con.close()

    _respaldar_plantillas(sello)
    return destino


def _respaldar_plantillas(sello: str) -> None:
    """Copia los moldes/plantillas subidos desde el taller (Documentos) —
    no viven en la base de datos, así que VACUUM INTO no los cubre. Se
    salta si todavía no se ha subido nada (nada que respaldar)."""
    origen = directorio_plantillas_personalizadas()
    archivos = list(origen.glob("*.docx"))
    if not archivos:
        return

    destino = carpeta_respaldos() / f"{PREFIJO}{sello}_plantillas"
    destino.mkdir(exist_ok=True)
    for archivo in archivos:
        shutil.copy2(archivo, destino / archivo.name)


def listar_respaldos() -> list[Path]:
    carpeta = carpeta_respaldos()
    return sorted(carpeta.glob(f"{PREFIJO}*.db"), reverse=True)


def limpiar_respaldos_viejos(dias_retencion: int = 30) -> int:
    limite = datetime.now() - timedelta(days=dias_retencion)
    eliminados = 0
    for archivo in listar_respaldos():
        if datetime.fromtimestamp(archivo.stat().st_mtime) < limite:
            archivo.unlink()
            eliminados += 1
            carpeta_plantillas = archivo.parent / f"{archivo.stem}_plantillas"
            if carpeta_plantillas.is_dir():
                shutil.rmtree(carpeta_plantillas)
    return eliminados


def restaurar_respaldo(nombre_archivo: str) -> None:
    """Sobrescribe data/maestria.db con un respaldo. Se hace un respaldo de
    seguridad del estado actual antes de tocar nada (por si el respaldo
    elegido resulta ser el equivocado). Requiere reiniciar la app después
    (se cierran las conexiones activas, pero el proceso debe volver a
    arrancar para que todo quede limpio)."""
    origen = carpeta_respaldos() / nombre_archivo
    if not origen.exists() or origen.parent != carpeta_respaldos():
        raise FileNotFoundError(f"Respaldo no encontrado: {nombre_archivo!r}")

    from app.database.session import engine

    engine.dispose()  # cierra conexiones abiertas del pool antes de tocar el archivo

    crear_respaldo()  # respaldo de seguridad del estado justo antes de restaurar

    for sufijo in ("", "-wal", "-shm"):
        candidato = Path(str(DB_PATH) + sufijo)
        if candidato.exists():
            candidato.unlink()

    shutil.copy2(origen, DB_PATH)

    carpeta_plantillas_respaldo = origen.parent / f"{origen.stem}_plantillas"
    if carpeta_plantillas_respaldo.is_dir():
        destino_plantillas = directorio_plantillas_personalizadas()
        for archivo in destino_plantillas.glob("*.docx"):
            archivo.unlink()
        for archivo in carpeta_plantillas_respaldo.glob("*.docx"):
            shutil.copy2(archivo, destino_plantillas / archivo.name)


def iniciar_respaldos_periodicos(intervalo_horas: float = 4) -> None:
    """Corre en un hilo de fondo mientras la app está viva — respaldo cada
    N horas, más limpieza de los que ya pasaron su retención. No bloquea el
    arranque de la app."""

    def _ciclo():
        while True:
            time.sleep(intervalo_horas * 3600)
            try:
                crear_respaldo()
                limpiar_respaldos_viejos()
            except OSError:
                pass  # ej. carpeta compartida desconectada momentáneamente

    hilo = threading.Thread(target=_ciclo, daemon=True)
    hilo.start()


def respaldar_si_hace_falta() -> Path | None:
    """Al arrancar la app: un respaldo si hoy todavía no hay ninguno."""
    hoy = datetime.now().strftime("%Y-%m-%d")
    if any(hoy in p.name for p in listar_respaldos()):
        return None
    return crear_respaldo()
