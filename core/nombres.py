"""Normalización de nombres de profesor en texto libre (Excel, actas):
prefijos Dr./Dra./Mtro., typos de acentos, saltos de línea."""

import re
import unicodedata
from difflib import SequenceMatcher

_PREFIJOS = re.compile(
    r"^(dr\.?a?\.?\s+|dra\.?\s+|mtro\.?\s+|mtra\.?\s+|m\.?\s*en\s*c\.?\s+|"
    r"m\.?c\.?\s+|mc\.?\s+|lic\.?\s+|c\.\s+)",
    re.IGNORECASE,
)


def limpiar_nombre(crudo: str) -> str:
    """Quita prefijos de grado y normaliza espacios/saltos de línea. NO
    quita acentos — el nombre limpio se sigue mostrando con acentos, la
    comparación sin acentos es solo para encontrar duplicados."""
    if not crudo:
        return ""
    texto = crudo.replace("\n", " ").replace("\r", " ")
    texto = re.sub(r"\s+", " ", texto).strip()
    # puede tener el prefijo repetido o en medio ("Dr. Dra. X"), aplicar 2 veces
    texto = _PREFIJOS.sub("", texto)
    texto = _PREFIJOS.sub("", texto)
    return texto.strip(" .")


def clave_comparacion(nombre: str) -> str:
    """Clave insensible a acentos/mayúsculas para detectar que dos strings
    de texto libre son la misma persona."""
    sin_acentos = unicodedata.normalize("NFKD", nombre)
    sin_acentos = "".join(c for c in sin_acentos if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_acentos).strip().upper()


def separar_director_codirector(campo: str) -> tuple[str | None, str | None]:
    """'Director(es)' del Excel viene a veces como 'Nombre1 / Nombre2'
    (director / codirector) y a veces como un solo nombre."""
    if not campo:
        return None, None
    partes = [p.strip() for p in campo.split("/") if p.strip()]
    director = limpiar_nombre(partes[0]) if len(partes) >= 1 else None
    codirector = limpiar_nombre(partes[1]) if len(partes) >= 2 else None
    return director or None, codirector or None


def similitud(nombre_a: str, nombre_b: str) -> float:
    """0.0-1.0. Heurística barata para sugerir posibles duplicados de
    profesor SIN fusionarlos automáticamente (dos personas reales pueden
    tener nombres parecidos) — solo para que un humano revise."""
    return SequenceMatcher(None, clave_comparacion(nombre_a), clave_comparacion(nombre_b)).ratio()
