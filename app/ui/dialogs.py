from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QVBoxLayout,
)

from app.models import Profesor


class DireccionDialog(QDialog):
    """Asignar/cambiar Director o Codirector de tesis."""

    def __init__(self, profesores: list[Profesor], rol_inicial: str = "Director", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Asignar {rol_inicial}")
        self.profesores = profesores

        layout = QFormLayout(self)

        self.combo_rol = QComboBox()
        self.combo_rol.addItems(["Director", "Codirector"])
        self.combo_rol.setCurrentText(rol_inicial)
        layout.addRow("Rol:", self.combo_rol)

        self.combo_profesor = QComboBox()
        self.combo_profesor.setEditable(True)
        self.combo_profesor.setInsertPolicy(QComboBox.NoInsert)
        for p in profesores:
            etiqueta = p.nombre + ("" if p.nucleo_academico else "  (externo)")
            self.combo_profesor.addItem(etiqueta, userData=p.id)
        layout.addRow("Profesor:", self.combo_profesor)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addRow(botones)

    def resultado(self) -> tuple[str, int] | None:
        idx = self.combo_profesor.currentIndex()
        if idx < 0:
            return None
        profesor_id = self.combo_profesor.itemData(idx)
        if profesor_id is None:
            return None
        return self.combo_rol.currentText(), profesor_id


class ComiteDialog(QDialog):
    """Asignar/cambiar el Comité Tutorial del alumno (2-3 profesores, lista
    plana sin cargo diferenciado — ver notas del proyecto)."""

    def __init__(self, profesores: list[Profesor], miembros_actuales: list[int] | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Asignar Comité Tutorial")
        miembros_actuales = miembros_actuales or []

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Ciclo (ej. 2026 B):"))
        self.campo_ciclo = QLineEdit()
        layout.addWidget(self.campo_ciclo)

        layout.addWidget(QLabel("Miembros del comité (marca 2 o 3):"))
        self.lista = QListWidget()
        for p in profesores:
            etiqueta = p.nombre + ("" if p.nucleo_academico else "  (externo)")
            item = QListWidgetItem(etiqueta)
            item.setData(Qt.UserRole, p.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked if p.id in miembros_actuales else Qt.Unchecked)
            self.lista.addItem(item)
        layout.addWidget(self.lista)

        botones = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        botones.accepted.connect(self._validar_y_aceptar)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    def _validar_y_aceptar(self):
        if len(self.miembros_seleccionados()) < 1:
            QMessageBox.warning(self, "Comité Tutorial", "Selecciona al menos un profesor.")
            return
        self.accept()

    def miembros_seleccionados(self) -> list[int]:
        seleccionados = []
        for i in range(self.lista.count()):
            item = self.lista.item(i)
            if item.checkState() == Qt.Checked:
                seleccionados.append(item.data(Qt.UserRole))
        return seleccionados

    def ciclo(self) -> str | None:
        return self.campo_ciclo.text().strip() or None
