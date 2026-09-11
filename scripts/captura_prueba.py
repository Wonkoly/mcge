"""Prueba visual headless: levanta la ventana principal, selecciona el
primer alumno de la lista y guarda una captura PNG para revisar que la UI
carga datos reales correctamente."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow

app = QApplication(sys.argv)
ventana = MainWindow()
ventana.resize(1200, 750)
ventana.show()

if ventana.tabla_alumnos.rowCount() > 0:
    ventana.tabla_alumnos.selectRow(0)

app.processEvents()

salida = Path(__file__).resolve().parent.parent / "scratch_captura.png"
ventana.grab().save(str(salida))
print("Guardado:", salida)
print("Alumnos en tabla:", ventana.tabla_alumnos.rowCount())
print("Alumno seleccionado:", ventana.alumno_actual.nombre if ventana.alumno_actual else None)
