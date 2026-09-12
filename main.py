import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.session import DB_PATH, SessionLocal, init_db
from app.utils.backup import iniciar_respaldos_periodicos, limpiar_respaldos_viejos, respaldar_si_hace_falta
from app.web import create_app

PORT = 8420

# Por defecto solo esta PC puede usar la app (más seguro). Para que otra PC
# en la misma red (ej. la del coordinador) se pueda conectar, arrancar con
# la variable de entorno MCG_LAN=1 — ver
# 'MaestriaGeofisica - Red Local (Dos Equipos)' en el vault de Obsidian
# para la guía completa de prueba en Windows.
MODO_LAN = os.environ.get("MCG_LAN") == "1"
HOST = "0.0.0.0" if MODO_LAN else "127.0.0.1"


def _ip_local() -> str | None:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except OSError:
        return None


def main():
    if not DB_PATH.exists():
        init_db()
    else:
        respaldar_si_hace_falta()
        limpiar_respaldos_viejos()

    from app.services.configuracion_service import obtener as obtener_config

    session = SessionLocal()
    try:
        intervalo = float(obtener_config(session, "backup_intervalo_horas"))
    finally:
        session.close()
    iniciar_respaldos_periodicos(intervalo)

    app = create_app()

    url_local = f"http://127.0.0.1:{PORT}/"
    threading.Timer(1.0, lambda: webbrowser.open(url_local)).start()

    print(f"Maestría en Ciencias en Geofísica — corriendo en {url_local}")
    if MODO_LAN:
        ip = _ip_local()
        if ip:
            print(f"Modo red local activo — desde OTRA PC en la misma red, entrar a: http://{ip}:{PORT}/")
        else:
            print("Modo red local activo, pero no se pudo detectar la IP de esta PC (revisa 'ipconfig').")
    print("Cierra esta ventana (o Ctrl+C) para apagar la app.")
    app.run(host=HOST, port=PORT, debug=False, threaded=True)


if __name__ == "__main__":
    main()
