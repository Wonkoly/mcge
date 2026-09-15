from django.apps import AppConfig
from django.db.backends.signals import connection_created


def _configurar_conexion(sender, connection, **kwargs):
    if connection.vendor != "sqlite":
        return
    cursor = connection.cursor()
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


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"

    def ready(self):
        connection_created.connect(_configurar_conexion)
