import secrets

from flask import Flask

from app.services.configuracion_service import obtener as obtener_config
from app.utils.rutas import directorio_recursos
from app.web.db import cerrar_sesion, get_session

TEMPLATES_DIR = directorio_recursos() / "app" / "web" / "templates"
STATIC_DIR = directorio_recursos() / "app" / "web" / "static"


def create_app() -> Flask:
    app = Flask(__name__, template_folder=str(TEMPLATES_DIR), static_folder=str(STATIC_DIR))
    app.secret_key = secrets.token_hex(16)  # solo para flash messages, no hay login todavía

    from app.web.routes import actas, alumnos, aspirantes, configuracion, dashboard, documentos, profesores

    app.register_blueprint(dashboard.bp)
    app.register_blueprint(alumnos.bp)
    app.register_blueprint(aspirantes.bp)
    app.register_blueprint(profesores.bp)
    app.register_blueprint(actas.bp)
    app.register_blueprint(documentos.bp)
    app.register_blueprint(configuracion.bp)

    @app.context_processor
    def inyectar_configuracion_global():
        # Disponible en TODAS las plantillas como `coordinador_default`, sin
        # tener que pasarlo desde cada ruta — un solo lugar (Settings) en
        # vez de repetirlo/repartirlo por el código.
        return {"coordinador_default": obtener_config(get_session(), "coordinador_nombre")}

    app.teardown_appcontext(cerrar_sesion)

    return app
