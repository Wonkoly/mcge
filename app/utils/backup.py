import shutil
from datetime import date
from pathlib import Path

from app.database.session import DB_PATH

BASE_DIR = Path(__file__).resolve().parent.parent.parent
BACKUPS_DIR = BASE_DIR / "backups"


def respaldar_si_hace_falta() -> Path | None:
    """Copia data/maestria.db a backups/maestria_AAAA-MM-DD.db si hoy
    todavía no existe un respaldo. Se llama al arrancar la app, no requiere
    tarea programada aparte."""
    if not DB_PATH.exists():
        return None

    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    destino = BACKUPS_DIR / f"maestria_{date.today().isoformat()}.db"
    if destino.exists():
        return None

    shutil.copy2(DB_PATH, destino)
    return destino
