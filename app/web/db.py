from flask import g

from app.database.session import SessionLocal


def get_session():
    if "db_session" not in g:
        g.db_session = SessionLocal()
    return g.db_session


def cerrar_sesion(exception=None):
    session = g.pop("db_session", None)
    if session is not None:
        session.close()
