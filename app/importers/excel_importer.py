"""Importador del Excel actual de la maestría (hoja `Estatus`, fuente
primaria de alumnos) hacia el modelo normalizado. El Excel es fuente de
migración, no la base de datos oficial una vez importado — ver
'MaestriaGeofisica - Excel Alumnos (Mapeo de Hojas)' en el vault para el
mapeo completo de columnas y las decisiones de diseño detrás de este código.

Este importador solo carga el estado VIGENTE (snapshot del Excel), no
reconstruye historial — el historial real de comités/direcciones se captura
en Fase B a partir de las actas."""

from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from app.importers.seed_data import ALIAS_CONOCIDOS
from app.models import Alumno, Direccion, Lies, Profesor
from app.utils.nombres import clave_comparacion, limpiar_nombre, separar_director_codirector, similitud

_ALIAS_POR_CLAVE = {clave_comparacion(k): v for k, v in ALIAS_CONOCIDOS.items()}

UMBRAL_POSIBLE_DUPLICADO = 0.82

COL = {
    "nombre": 0,
    "codigo": 1,
    "ciclo_ingreso": 2,
    "status": 3,
    "creditos_acumulados": 4,
    "promedio": 5,
    "ciclos": 6,
    "creditos_faltantes": 7,
    "maximo_ciclo": 8,
    "dictamen": 9,
    "telefono": 10,
    "correo_personal": 11,
    "correo_institucional": 12,
    "fecha_nacimiento": 13,
    "retribucion_social": 14,
    "cvu": 15,
    "fecha_grado": 16,
    "director": 17,
    "tesis": 18,
    "lies": 19,
    "protocolo": 20,
    "impacto_cientifico": 21,
    "impacto_social": 22,
    "solucion_problemas": 23,
    "estrategias_acceso": 24,
}


@dataclass
class ResultadoImportacion:
    alumnos_creados: int = 0
    alumnos_actualizados: int = 0
    profesores_creados: int = 0
    direcciones_creadas: int = 0
    advertencias: list[str] = field(default_factory=list)


def _valor(row, clave):
    idx = COL[clave]
    return row[idx] if idx < len(row) else None


def _a_fecha(valor) -> date | None:
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    return None


def _a_texto(valor) -> str | None:
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


class ImportadorExcel:
    def __init__(self, session: Session):
        self.session = session
        self.resultado = ResultadoImportacion()
        self._indice_profesores: dict[str, Profesor] = {}
        self._indice_lies: dict[str, Lies] = {}

    def _cargar_indices(self):
        for p in self.session.query(Profesor).all():
            self._indice_profesores[clave_comparacion(p.nombre)] = p
        for l in self.session.query(Lies).all():
            self._indice_lies[clave_comparacion(l.nombre)] = l

    def _obtener_o_crear_profesor(self, nombre_crudo: str) -> Profesor | None:
        nombre = limpiar_nombre(nombre_crudo)
        if not nombre:
            return None
        nombre = _ALIAS_POR_CLAVE.get(clave_comparacion(nombre), nombre)
        clave = clave_comparacion(nombre)
        profesor = self._indice_profesores.get(clave)
        if profesor is None:
            profesor = Profesor(nombre=nombre, nucleo_academico=False)
            self.session.add(profesor)
            self.session.flush()
            self._indice_profesores[clave] = profesor
            self.resultado.profesores_creados += 1
            self.resultado.advertencias.append(
                f"Profesor creado fuera del núcleo académico (revisar si es duplicado): {nombre!r}"
            )
        return profesor

    def _resolver_lies(self, nombre_crudo) -> Lies | None:
        # El Excel trae el párrafo descriptivo completo de la LIES, no el
        # nombre corto del catálogo oficial (2 valores). Cada línea/párrafo
        # empieza con su propia etiqueta ("Paisajes geográficos y riesgos:"
        # / "Ciencias de la tierra:") — OJO: el texto de "Paisaje" menciona
        # de pasada la frase "Ciencias de la Tierra" dentro de su propia
        # descripción, así que hay que mirar el INICIO de cada línea, no
        # buscar la palabra en cualquier parte del texto (eso daba falsos
        # positivos de "ambigüedad").
        texto = _a_texto(nombre_crudo)
        if not texto:
            return None
        encontradas: list[str] = []
        for segmento in texto.split("\n"):
            clave_seg = clave_comparacion(segmento)
            if clave_seg.startswith("PAISAJE"):
                encontradas.append("Paisaje Geográfico y Riesgo")
            elif clave_seg.startswith("CIENCIAS DE LA TIERRA"):
                encontradas.append("Ciencias de la Tierra")
        if not encontradas:
            self.resultado.advertencias.append(
                f"Valor de LIES no reconocido (se ignora): {texto[:80]!r}..."
            )
            return None
        if len(set(encontradas)) > 1:
            self.resultado.advertencias.append(
                f"LIES ambigua (el campo menciona las 2 líneas), se tomó la primera: {texto[:80]!r}..."
            )
        return self._indice_lies.get(clave_comparacion(encontradas[0]))

    def importar(self, ruta_excel: Path, hoja: str = "Estatus") -> ResultadoImportacion:
        self._cargar_indices()
        wb = openpyxl.load_workbook(ruta_excel, data_only=True)
        ws = wb[hoja]

        filas = list(ws.iter_rows(min_row=2, values_only=True))
        for row in filas:
            codigo = _a_texto(_valor(row, "codigo"))
            nombre = _a_texto(_valor(row, "nombre"))
            if not codigo or not nombre:
                continue

            alumno = self.session.query(Alumno).filter_by(codigo=codigo).one_or_none()
            es_nuevo = alumno is None
            if alumno is None:
                alumno = Alumno(codigo=codigo)
                self.session.add(alumno)

            alumno.nombre = nombre
            alumno.ciclo_ingreso = _a_texto(_valor(row, "ciclo_ingreso"))
            status_codigo = _a_texto(_valor(row, "status"))
            alumno.status_codigo = status_codigo
            alumno.creditos_acumulados = _valor(row, "creditos_acumulados")
            alumno.promedio = _valor(row, "promedio")
            alumno.ciclos_cursados = _valor(row, "ciclos")
            alumno.creditos_faltantes = _valor(row, "creditos_faltantes")
            alumno.maximo_ciclo = _a_texto(_valor(row, "maximo_ciclo"))
            alumno.dictamen = _a_texto(_valor(row, "dictamen"))
            alumno.telefono = _a_texto(_valor(row, "telefono"))
            alumno.correo_personal = _a_texto(_valor(row, "correo_personal"))
            alumno.correo_institucional = _a_texto(_valor(row, "correo_institucional"))
            alumno.fecha_nacimiento = _a_fecha(_valor(row, "fecha_nacimiento"))
            alumno.retribucion_social = _a_texto(_valor(row, "retribucion_social"))
            alumno.cvu = _a_texto(_valor(row, "cvu"))
            alumno.fecha_grado = _a_fecha(_valor(row, "fecha_grado"))
            lies = self._resolver_lies(_valor(row, "lies"))
            alumno.lies_id = lies.id if lies else None
            alumno.tesis_titulo = _a_texto(_valor(row, "tesis"))
            alumno.protocolo = _a_texto(_valor(row, "protocolo"))
            alumno.impacto_cientifico = _a_texto(_valor(row, "impacto_cientifico"))
            alumno.impacto_social = _a_texto(_valor(row, "impacto_social"))
            alumno.solucion_problemas = _a_texto(_valor(row, "solucion_problemas"))
            alumno.estrategias_acceso = _a_texto(_valor(row, "estrategias_acceso"))

            self.session.flush()  # asegura alumno.id

            if es_nuevo:
                self.resultado.alumnos_creados += 1
            else:
                self.resultado.alumnos_actualizados += 1

            self._importar_direccion(alumno, _a_texto(_valor(row, "director")))

        self._revisar_posibles_duplicados()
        return self.resultado

    def _revisar_posibles_duplicados(self):
        """No fusiona nada automáticamente (dos personas reales pueden
        parecerse) — solo deja una lista para revisión humana. Ver
        pendiente 'Reconciliar los 53 nombres...' en el vault."""
        nucleo = [p for p in self._indice_profesores.values() if p.nucleo_academico]
        externos = [p for p in self._indice_profesores.values() if not p.nucleo_academico]
        for externo in externos:
            for candidato in nucleo:
                score = similitud(externo.nombre, candidato.nombre)
                if score >= UMBRAL_POSIBLE_DUPLICADO:
                    self.resultado.advertencias.append(
                        f"POSIBLE DUPLICADO ({score:.0%} similar): "
                        f"{externo.nombre!r} (fuera de núcleo) <-> {candidato.nombre!r} (núcleo académico)"
                    )

    def _importar_direccion(self, alumno: Alumno, campo_director: str | None):
        if not campo_director:
            return
        director_nombre, codirector_nombre = separar_director_codirector(campo_director)

        # Snapshot del Excel = solo el estado vigente. Si ya existe una
        # dirección vigente con el mismo profesor+rol no se duplica.
        vigentes = {
            (d.rol, clave_comparacion(d.profesor.nombre))
            for d in self.session.query(Direccion).filter_by(alumno_id=alumno.id, fecha_fin=None).all()
        }

        if director_nombre:
            profesor = self._obtener_o_crear_profesor(director_nombre)
            if profesor and ("Director", clave_comparacion(profesor.nombre)) not in vigentes:
                self.session.add(Direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Director"))
                self.resultado.direcciones_creadas += 1

        if codirector_nombre:
            profesor = self._obtener_o_crear_profesor(codirector_nombre)
            if profesor and ("Codirector", clave_comparacion(profesor.nombre)) not in vigentes:
                self.session.add(Direccion(alumno_id=alumno.id, profesor_id=profesor.id, rol="Codirector"))
                self.resultado.direcciones_creadas += 1
