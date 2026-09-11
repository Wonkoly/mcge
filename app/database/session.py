from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "data" / "maestria.db"

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)


@event.listens_for(engine, "connect")
def _configurar_conexion(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # Con dos PCs escribiendo casi al mismo tiempo, sin esto un segundo
    # escritor recibe "database is locked" de inmediato en vez de esperar
    # su turno — con esto espera hasta 5s antes de fallar.
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, future=True)


def init_db() -> None:
    from app.models import Base

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
