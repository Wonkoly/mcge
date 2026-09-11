"""Datos semilla que NO vienen del Excel: catálogo de Status (inferido de
las tablas dinámicas del Excel, ver MaestriaGeofisica - Excel Alumnos en el
vault), catálogo LIES y núcleo académico oficial (25 personas, extraídos de
cuc.udg.mx el 2026-09-10/11, ver MaestriaGeofisica - Núcleo Académico y
LIES)."""

from sqlalchemy.orm import Session

from app.models import Lies, Profesor, StatusAlumno

STATUS_SEED = [
    # codigo, nombre, categoria, confirmado
    ("AC", "Activo", "activo", True),
    ("PT", "Proceso de Titulación", "proceso_titulacion", True),
    ("GD", "Graduado", "graduado", True),
    ("TT", "Titulado", "titulado", True),
    ("BV", "Baja Voluntaria", "baja", True),
    ("DE", "Baja (Deserción)", "baja", True),
    ("IN", "Inactivo", "inactivo", False),
    ("BA", "Baja (tipo sin confirmar)", "baja", False),
    ("B8", "Sin identificar", "desconocido", False),
    ("RD", "Sin identificar (probable baja)", "desconocido", False),
]

# Variantes del Excel confirmadas manualmente (alta similitud + perfil
# coherente) como la MISMA persona que alguien del núcleo académico oficial.
# Solo entran aquí las que se revisaron con confianza alta — el resto de
# "POSIBLES DUPLICADO" que reporta el importador se deja para revisión
# humana en vez de fusionarse a ciegas (dos personas reales pueden
# parecerse, ej. "Juan Manuel Espinosa Cardeña" vs "Juan Manuel Espíndola
# Castro" comparten nombre de pila pero son apellidos distintos).
ALIAS_CONOCIDOS = {
    "Adán Gómez Hernámdez": "Adán Gómez Hernández",  # typo de imprenta (m/n)
    "Luisa Hernández Aguilar": "María Luisa Hernández Aguilar",  # falta el primer nombre
    "Claudia Beatriz Mercedes Quinteros Cartaya": "Claudia Beatriz M. Quinteros Cartaya",
    "Claudia Mercedes Quinteros Cartaya": "Claudia Beatriz M. Quinteros Cartaya",
}

LIES_SEED = [
    "Paisaje Geográfico y Riesgo",
    "Ciencias de la Tierra",
]

# (nombre, sni, dedicacion, grado, linea_investigacion)
NUCLEO_ACADEMICO_SEED = [
    ("Araceli Zamora Camacho", "I", "Tiempo completo", "Doctora en Ciencias (Sismología y Vulcanología), UNAM", "Sismología, riesgos naturales, vulcanología"),
    ("Gonzalo Alejandro Ramírez Gaytán", "II", "Tiempo completo", "Doctor en Ciencias, UNAM", "Sismología, suelo-estructura, geotecnia"),
    ("Fátima Maciel Carrillo González", "I", "Tiempo completo", "Doctora en Ingeniería y Tecnología, UDG", "Variabilidad climática, oceanografía costera"),
    ("Christian Rene Escudero Ayala", "I", "Tiempo completo", "Doctor en Ciencias de la Tierra, UTEP", "Sismología, física de la Tierra, riesgos sísmicos"),
    ("María Carolina Rodríguez Uribe", "I", "Tiempo completo", "Doctora en Biosistemática y Manejo de Recursos Naturales", "Geotermia, sistemas hidrotermales"),
    ("Mario Alberto Fuentes Arreazola", "I", "Tiempo completo", "Doctor en Ciencias de la Tierra, CICESE", "Métodos electromagnéticos, geofísica aplicada"),
    ("Lorena Anaya Ortega", "C", "Tiempo completo", "Doctorado en Ciudad, Territorio y Sustentabilidad", "Espacio urbano, sustentabilidad, planeación"),
    ("Héctor Javier Rendón Contreras", "I", "Tiempo completo", "Doctor en Ciencias para el Desarrollo Sustentable, UDG", "Hidrogeofísica, gestión del agua subterránea"),
    ("Erika Sandoval Hernández", "No", "Tiempo completo", "Doctora en Matemática Física, UDG", "Dinámica de fluidos geofísicos, oceanografía"),
    ("Juan Ignacio Pinzón López", "C", "Tiempo completo", "Doctor en Geofísica, U. de Lisboa", "Sismología ambiental, tectónica"),
    ("Quiriat Jearim Gutiérrez Peña", "C", "Tiempo completo", "Doctor en Ciencias de la Tierra, CICESE", "Sismología regional, geofísica ambiental"),
    ("Juan Manuel Espíndola Castro", "E", "Tiempo parcial externo", "Doctor en Filosofía", "Sismología, vulcanología, gravimetría"),
    ("Olga Sarichikhina", "I", "Tiempo parcial externa", "Doctora en Filosofía, CICESE", "Monitoreo de desplazamientos terrestres, InSAR"),
    ("Bartolo Cruz Romero", "I", "Tiempo parcial interno", "Doctor en Biosistemática, Ecología y Manejo de Recursos Naturales", "Desarrollo sustentable, hidrología, SIG"),
    ("Claudia Beatriz M. Quinteros Cartaya", "I", "Tiempo parcial externa", "Doctora en Sismología, CICESE", "Análisis de grandes sismos, peligros sísmicos"),
    ("Julio César Morales Hernández", "I", "Tiempo parcial interno", None, "Fenómenos hidrometeorológicos extremos, gestión del agua"),
    ("Elizabeth Trejo Gómez", None, "Tiempo parcial interna", "Doctora en Sismología, CICESE", "Sismología, peligros sísmicos"),
    ("María Luisa Hernández Aguilar", "I", "Tiempo parcial externa", "Doctora en Geografía", "Riesgos de desastres, vulnerabilidad territorial"),
    ("Gabriela Colorado Ruíz", "C", "Tiempo parcial externa", None, "Ciencias atmosféricas, cambio climático"),
    ("Karen Leticia Flores Navarro", None, "Tiempo parcial externa", "Licenciada en Ciencias con especialidad", "Peligros naturales, gestión del riesgo"),
    ("Adán Gómez Hernández", None, "Tiempo parcial interno", "Maestro en Ciencias en Geofísica, Ingeniero Civil", "Geofísica, riesgos naturales"),
    ("Horacio Ramírez Rodríguez", None, "Tiempo parcial interno", "Doctorante en Ciencias para el Desarrollo Sustentable", "Gestión del agua, turismo en contextos costeros"),
    ("Hafid Salgado Martínez", None, "Tiempo parcial interno", "Doctorante en Geografía y Ordenamiento Territorial", "Métodos geofísicos, comportamiento geotectónico"),
    ("Carlos Suárez Plascencia", None, "Tiempo parcial interno", "Maestría en Ciencias, CICESE", "Riesgos naturales, ordenamiento territorial"),
    ("Luz María Zúñiga Medina", None, "Tiempo parcial interna", "Doctora en Ciencias Estadísticas", "Matemáticas aplicadas, estadística, educación matemática"),
]


def seed_status(session: Session) -> None:
    for codigo, nombre, categoria, confirmado in STATUS_SEED:
        if session.get(StatusAlumno, codigo) is None:
            session.add(StatusAlumno(codigo=codigo, nombre=nombre, categoria=categoria, confirmado=confirmado))


def seed_lies(session: Session) -> dict[str, Lies]:
    result = {}
    for nombre in LIES_SEED:
        obj = session.query(Lies).filter_by(nombre=nombre).one_or_none()
        if obj is None:
            obj = Lies(nombre=nombre)
            session.add(obj)
            session.flush()
        result[nombre] = obj
    return result


def seed_nucleo_academico(session: Session) -> None:
    for nombre, sni, dedicacion, grado, linea in NUCLEO_ACADEMICO_SEED:
        existente = session.query(Profesor).filter_by(nombre=nombre).one_or_none()
        if existente is None:
            session.add(
                Profesor(
                    nombre=nombre,
                    grado=grado,
                    sni=sni,
                    dedicacion=dedicacion,
                    linea_investigacion=linea,
                    nucleo_academico=True,
                )
            )
        else:
            existente.nucleo_academico = True
            existente.sni = sni
            existente.dedicacion = dedicacion
            existente.grado = existente.grado or grado
            existente.linea_investigacion = linea
