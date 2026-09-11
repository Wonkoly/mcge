import secrets
from pathlib import Path

from flask import Flask

from app.web.db import cerrar_sesion

TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
    app.secret_key = secrets.token_hex(16)  # solo para flash messages, no hay login todavía

    from app.web.routes import actas, alumnos, aspirantes, dashboard, documentos, profesores

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(alumnos.bp)
    app.register_blueprint(aspirantes.bp)
    app.register_blueprint(profesores.bp)
    app.register_blueprint(actas.bp)
    app.register_blueprint(documentos.bp)

    app.teardown_appcontext(cerrar_sesion)

    return app
