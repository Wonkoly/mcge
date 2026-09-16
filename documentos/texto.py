"""Ayudantes de gramática española para los documentos generados — puerto
1:1 de app/documents/generador.py (helpers de texto, sin las funciones
generar_* que dependen de folio_service/modelos)."""

from datetime import date

from profesores.models import PREFIJO_POR_TRATAMIENTO

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]

NUMEROS_TEXTO = [
    "", "uno", "dos", "tres", "cuatro", "cinco", "seis", "siete", "ocho",
    "nueve", "diez", "once", "doce", "trece", "catorce", "quince",
    "dieciséis", "diecisiete", "dieciocho", "diecinueve", "veinte",
]

_MINUSCULAS = {"de", "del", "la", "las", "los", "y"}


def fecha_larga(d: date | None = None) -> str:
    d = d or date.today()
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


def fecha_corta_sin_anio(d: date | None = None) -> str:
    """Para frases como "mediante el Acta X con fecha del {...} del presente
    año" — mismo formato que fecha_larga() pero sin repetir el año."""
    d = d or date.today()
    return f"{d.day} de {MESES[d.month - 1]}"


def numero_a_texto(n: int) -> str:
    if 0 < n < len(NUMEROS_TEXTO):
        return NUMEROS_TEXTO[n]
    return str(n)


def formatear_nombre(nombre: str) -> str:
    """Los nombres de alumno vienen en MAYÚSCULAS del Excel — se ve mal en
    un documento formal. Convierte a Capitalizado manteniendo minúsculas en
    partículas comunes ("de", "del", "la"...)."""
    if not nombre:
        return nombre
    palabras = nombre.strip().split()
    resultado = [
        p.lower() if p.lower() in _MINUSCULAS and i > 0 else p.capitalize()
        for i, p in enumerate(palabras)
    ]
    return " ".join(resultado)


def es_femenino_texto(grado: str | None) -> bool:
    return bool(grado) and ("doctora" in grado.lower() or "maestra" in grado.lower())


def es_femenino(profesor) -> bool:
    if profesor.tratamiento:
        return profesor.tratamiento in ("Doctora", "Maestra")
    return es_femenino_texto(profesor.grado)


def campos_rol(direccion) -> tuple[str, str, str]:
    """(rol_texto_largo, rol_texto_corto, articulo_del_rol) a partir de un
    Direccion — ej. ('Director', 'director', 'del') o
    ('Codirectora', 'codirectora', 'de la'). Fuente única, reutilizada por
    actas.acta_service (composición de título/resolutivo) y
    documentos.generador (oficio/constancia de dirección)."""
    femenino = es_femenino(direccion.profesor)
    articulo = "de la" if femenino else "del"
    if direccion.rol == "Director":
        return ("Directora" if femenino else "Director"), ("directora" if femenino else "director"), articulo
    return ("Codirectora" if femenino else "Codirector"), ("codirectora" if femenino else "codirector"), articulo


def tratamiento_con_nombre(profesor, nombre: str) -> str:
    """'el Dr. Fulano' / 'la Dra. Fulana' / solo 'Fulano' si no se conoce el
    tratamiento. Usa el campo `tratamiento` (catálogo cerrado) si existe; si
    no, cae en la heurística vieja sobre el texto libre de `grado`."""
    if profesor.tratamiento:
        prefijo = PREFIJO_POR_TRATAMIENTO.get(profesor.tratamiento, "")
        articulo = "la" if es_femenino(profesor) else "el"
        return f"{articulo} {prefijo} {nombre}" if prefijo else nombre

    grado = profesor.grado
    femenino = es_femenino_texto(grado)
    if grado and "doctor" in grado.lower():
        return f"{'la Dra.' if femenino else 'el Dr.'} {nombre}"
    if grado and ("maestro" in grado.lower() or "maestra" in grado.lower() or "m.c" in grado.lower() or "m. en c" in grado.lower()):
        return f"{'la Mtra.' if femenino else 'el Mtro.'} {nombre}"
    return nombre


def a_contraido(nombre_con_tratamiento: str) -> str:
    """"A el Dr. X" no es español correcto — es "Al Dr. X"."""
    if nombre_con_tratamiento.startswith("el "):
        return "Al " + nombre_con_tratamiento[3:]
    return f"A {nombre_con_tratamiento}"


def nombre_con_tratamiento(profesor) -> str:
    return tratamiento_con_nombre(profesor, formatear_nombre(profesor.nombre))


def acta_referencia(acta) -> str:
    if not acta:
        return ""
    if acta.fecha:
        return f"Acta {acta.numero} con fecha del {fecha_larga(acta.fecha)}"
    return f"Acta {acta.numero}"
