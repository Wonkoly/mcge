import sys
import threading
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database.session import DB_PATH, init_db
from app.utils.backup import respaldar_si_hace_falta
from app.web import create_app

HOST = "127.0.0.1"
PORT = 8420


def main():
    if not DB_PATH.exists():
        init_db()
    else:
        respaldar_si_hace_falta()

    app = create_app()

    url = f"http://{HOST}:{PORT}/"
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    print(f"Maestría en Ciencias en Geofísica — corriendo en {url}")
    print("Cierra esta ventana (o Ctrl+C) para apagar la app.")
    app.run(host=HOST, port=PORT, debug=False)


if __name__ == "__main__":
    main()
