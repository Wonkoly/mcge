from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.database.session import SessionLocal
from app.models import Alumno
from app.repositories.alumno_repository import buscar_alumnos
from app.repositories.comite_repository import comite_vigente, historial_comites
from app.repositories.direccion_repository import direcciones_vigentes, historial_direcciones
from app.repositories.profesor_repository import listar_profesores
from app.services.comite_service import asignar_comite_tutorial
from app.services.direccion_service import asignar_direccion
from app.ui.dialogs import ComiteDialog, DireccionDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Maestría en Ciencias en Geofísica — Gestión Académica")
        self.resize(1200, 750)

        self.session = SessionLocal()
        self.alumno_actual: Alumno | None = None

        self._construir_ui()
        self._cargar_alumnos()

    # ---------- construcción de UI ----------

    def _construir_ui(self):
        splitter = QSplitter(Qt.Horizontal)

        # Panel izquierdo: buscador + tabla
        panel_izq = QWidget()
        layout_izq = QVBoxLayout(panel_izq)
        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar por nombre o código...")
        self.campo_busqueda.textChanged.connect(self._cargar_alumnos)
        layout_izq.addWidget(self.campo_busqueda)

        self.tabla_alumnos = QTableWidget(0, 3)
        self.tabla_alumnos.setHorizontalHeaderLabels(["Código", "Nombre", "Status"])
        self.tabla_alumnos.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabla_alumnos.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tabla_alumnos.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabla_alumnos.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabla_alumnos.itemSelectionChanged.connect(self._al_seleccionar_alumno)
        layout_izq.addWidget(self.tabla_alumnos)

        self.etiqueta_conteo = QLabel("")
        layout_izq.addWidget(self.etiqueta_conteo)

        splitter.addWidget(panel_izq)

        # Panel derecho: expediente por pestañas
        self.tabs = QTabWidget()
        self.tab_datos = self._crear_tab_datos()
        self.tab_comite = self._crear_tab_comite()
        self.tab_direccion = self._crear_tab_direccion()
        self.tabs.addTab(self.tab_datos, "Datos generales")
        self.tabs.addTab(self.tab_comite, "Comité Tutorial")
        self.tabs.addTab(self.tab_direccion, "Dirección / Codirección")
        splitter.addWidget(self.tabs)

        splitter.setSizes([450, 750])
        self.setCentralWidget(splitter)

    def _crear_tab_datos(self) -> QWidget:
        widget = QWidget()
        form = QFormLayout(widget)
        self.lbl_nombre = QLabel("—")
        self.lbl_codigo = QLabel("—")
        self.lbl_ciclo = QLabel("—")
        self.lbl_status = QLabel("—")
        self.lbl_creditos = QLabel("—")
        self.lbl_promedio = QLabel("—")
        self.lbl_lies = QLabel("—")
        self.lbl_correo = QLabel("—")
        self.lbl_telefono = QLabel("—")
        self.txt_tesis = QTextEdit()
        self.txt_tesis.setReadOnly(True)
        self.txt_tesis.setMaximumHeight(80)
        for etiqueta, campo in [
            ("Nombre:", self.lbl_nombre),
            ("Código:", self.lbl_codigo),
            ("Ciclo de ingreso:", self.lbl_ciclo),
            ("Status:", self.lbl_status),
            ("Créditos (acum. / faltan):", self.lbl_creditos),
            ("Promedio:", self.lbl_promedio),
            ("LIES:", self.lbl_lies),
            ("Correo:", self.lbl_correo),
            ("Teléfono:", self.lbl_telefono),
        ]:
            form.addRow(etiqueta, campo)
        form.addRow("Título de tesis:", self.txt_tesis)
        return widget

    def _crear_tab_comite(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>Comité Tutorial vigente</b>"))
        self.lbl_comite_ciclo = QLabel("—")
        layout.addWidget(self.lbl_comite_ciclo)
        self.lista_comite_miembros = QTextEdit()
        self.lista_comite_miembros.setReadOnly(True)
        self.lista_comite_miembros.setMaximumHeight(100)
        layout.addWidget(self.lista_comite_miembros)

        btn_asignar = QPushButton("Asignar / cambiar comité tutorial...")
        btn_asignar.clicked.connect(self._abrir_dialogo_comite)
        layout.addWidget(btn_asignar)

        layout.addWidget(QLabel("<b>Historial</b>"))
        self.txt_comite_historial = QTextEdit()
        self.txt_comite_historial.setReadOnly(True)
        layout.addWidget(self.txt_comite_historial)

        return widget

    def _crear_tab_direccion(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("<b>Vigente</b>"))
        self.lbl_director = QLabel("Director: —")
        self.lbl_codirector = QLabel("Codirector: —")
        layout.addWidget(self.lbl_director)
        layout.addWidget(self.lbl_codirector)

        fila_botones = QHBoxLayout()
        btn_director = QPushButton("Asignar / cambiar Director...")
        btn_director.clicked.connect(lambda: self._abrir_dialogo_direccion("Director"))
        btn_codirector = QPushButton("Asignar / cambiar Codirector...")
        btn_codirector.clicked.connect(lambda: self._abrir_dialogo_direccion("Codirector"))
        fila_botones.addWidget(btn_director)
        fila_botones.addWidget(btn_codirector)
        layout.addLayout(fila_botones)

        layout.addWidget(QLabel("<b>Historial</b>"))
        self.txt_direccion_historial = QTextEdit()
        self.txt_direccion_historial.setReadOnly(True)
        layout.addWidget(self.txt_direccion_historial)

        return widget

    # ---------- carga de datos ----------

    def _cargar_alumnos(self):
        texto = self.campo_busqueda.text().strip()
        alumnos = buscar_alumnos(self.session, texto)
        self.tabla_alumnos.setRowCount(0)
        for alumno in alumnos:
            fila = self.tabla_alumnos.rowCount()
            self.tabla_alumnos.insertRow(fila)
            item_codigo = QTableWidgetItem(alumno.codigo)
            item_codigo.setData(Qt.UserRole, alumno.id)
            self.tabla_alumnos.setItem(fila, 0, item_codigo)
            self.tabla_alumnos.setItem(fila, 1, QTableWidgetItem(alumno.nombre))
            status = alumno.status.nombre if alumno.status else (alumno.status_codigo or "—")
            self.tabla_alumnos.setItem(fila, 2, QTableWidgetItem(status))
        self.etiqueta_conteo.setText(f"{len(alumnos)} alumno(s)")

    def _al_seleccionar_alumno(self):
        filas = self.tabla_alumnos.selectedItems()
        if not filas:
            self.alumno_actual = None
            return
        alumno_id = self.tabla_alumnos.item(self.tabla_alumnos.currentRow(), 0).data(Qt.UserRole)
        self.alumno_actual = self.session.get(Alumno, alumno_id)
        self._refrescar_expediente()

    def _refrescar_expediente(self):
        a = self.alumno_actual
        if a is None:
            return

        self.lbl_nombre.setText(a.nombre)
        self.lbl_codigo.setText(a.codigo)
        self.lbl_ciclo.setText(a.ciclo_ingreso or "—")
        self.lbl_status.setText(a.status.nombre if a.status else (a.status_codigo or "—"))
        acum = a.creditos_acumulados if a.creditos_acumulados is not None else "—"
        falt = a.creditos_faltantes if a.creditos_faltantes is not None else "—"
        self.lbl_creditos.setText(f"{acum} / {falt}")
        self.lbl_promedio.setText(str(a.promedio) if a.promedio is not None else "—")
        self.lbl_lies.setText(a.lies.nombre if a.lies else "—")
        self.lbl_correo.setText(a.correo_institucional or a.correo_personal or "—")
        self.lbl_telefono.setText(a.telefono or "—")
        self.txt_tesis.setPlainText(a.tesis_titulo or "—")

        # Comité tutorial
        comite = comite_vigente(self.session, a.id)
        if comite:
            self.lbl_comite_ciclo.setText(f"Ciclo: {comite.ciclo or '—'} (desde {comite.fecha_inicio})")
            nombres = "\n".join(f"- {m.profesor.nombre}" for m in comite.miembros)
            self.lista_comite_miembros.setPlainText(nombres or "(sin miembros)")
        else:
            self.lbl_comite_ciclo.setText("Sin comité tutorial asignado")
            self.lista_comite_miembros.setPlainText("")

        historial_c = historial_comites(self.session, a.id)
        lineas = []
        for c in historial_c:
            estado = "VIGENTE" if c.vigente else f"cerrado {c.fecha_fin}"
            miembros = ", ".join(m.profesor.nombre for m in c.miembros)
            fecha = c.fecha_inicio or "fecha desconocida"
            lineas.append(f"[{fecha} - {estado}] ciclo {c.ciclo or '?'}: {miembros}")
        self.txt_comite_historial.setPlainText("\n".join(lineas) or "(sin historial)")

        # Dirección / codirección
        vigentes = direcciones_vigentes(self.session, a.id)
        director = next((d for d in vigentes if d.rol == "Director"), None)
        codirector = next((d for d in vigentes if d.rol == "Codirector"), None)
        self.lbl_director.setText(f"Director: {director.profesor.nombre if director else '—'}")
        self.lbl_codirector.setText(f"Codirector: {codirector.profesor.nombre if codirector else '—'}")

        historial_d = historial_direcciones(self.session, a.id)
        lineas = []
        for d in historial_d:
            estado = "VIGENTE" if d.vigente else f"cerrado {d.fecha_fin}"
            fecha = d.fecha_inicio or "fecha desconocida"
            lineas.append(f"[{fecha} - {estado}] {d.rol}: {d.profesor.nombre}")
        self.txt_direccion_historial.setPlainText("\n".join(lineas) or "(sin historial)")

    # ---------- acciones ----------

    def _abrir_dialogo_direccion(self, rol: str):
        if self.alumno_actual is None:
            QMessageBox.information(self, "Dirección", "Selecciona un alumno primero.")
            return
        profesores = listar_profesores(self.session)
        dialogo = DireccionDialog(profesores, rol_inicial=rol, parent=self)
        if dialogo.exec():
            resultado = dialogo.resultado()
            if resultado is None:
                return
            rol_elegido, profesor_id = resultado
            _, aviso = asignar_direccion(
                self.session, alumno_id=self.alumno_actual.id, profesor_id=profesor_id, rol=rol_elegido
            )
            self.session.commit()
            self._refrescar_expediente()
            if aviso:
                QMessageBox.warning(self, "Aviso", aviso)

    def _abrir_dialogo_comite(self):
        if self.alumno_actual is None:
            QMessageBox.information(self, "Comité Tutorial", "Selecciona un alumno primero.")
            return
        profesores = listar_profesores(self.session)
        actual = comite_vigente(self.session, self.alumno_actual.id)
        miembros_actuales = [m.profesor_id for m in actual.miembros] if actual else []
        dialogo = ComiteDialog(profesores, miembros_actuales=miembros_actuales, parent=self)
        if dialogo.exec():
            asignar_comite_tutorial(
                self.session,
                alumno_id=self.alumno_actual.id,
                profesor_ids=dialogo.miembros_seleccionados(),
                ciclo=dialogo.ciclo(),
            )
            self.session.commit()
            self._refrescar_expediente()

    def closeEvent(self, event):
        self.session.close()
        super().closeEvent(event)
