import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication

from app.database.session import DB_PATH, init_db
from app.ui.main_window import MainWindow
from app.utils.backup import respaldar_si_hace_falta


def main():
    if not DB_PATH.exists():
        init_db()
    else:
        respaldar_si_hace_falta()

    app = QApplication(sys.argv)
    app.setApplicationName("Maestría en Ciencias en Geofísica")
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
