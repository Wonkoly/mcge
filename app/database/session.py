from app.utils.rutas import directorio_datos
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

BASE_DIR = directorio_datos()
DB_PATH = BASE_DIR / "data" / "maestria.db"

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)


@event.listens_for(engine, "connect")
def _configurar_conexion(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    # WAL: lectores no bloquean al escritor y viceversa — importante con dos
    # PCs usando la app a la vez. synchronous=NORMAL es seguro en modo WAL
    # (solo se pierde durabilidad ante un corte de luz en el mismo instante
    # del commit, no ante un crash del proceso).
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
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
